import customtkinter as ctk
import json
import os
import datetime


# ══════════════════════════════════════════════════════════════════════════════
# Funções auxiliares para manipulação de atributos (edição na ficha)
# ══════════════════════════════════════════════════════════════════════════════

LIMITE_NORMAL = 13
LIMITE_ABSOLUTO = 14

def calcular_pontos_disponiveis_ficha(ficha: dict) -> int:
    # Total de pontos que o personagem tem direito
    totais = ficha.get("totais_nex", {})
    total_disponivel = 4 + totais.get("pontos_atributo", 0) + ficha.get("pontos_extras_temp", 0)

    # Calcula quantos pontos já foram efetivamente gastos (baseado nos valores atuais)
    atributos = ficha.get("atributos", {})
    soma_atributos = sum(atributos.values())
    gastos_reais = max(0, soma_atributos - 5)   # cada atributo começa com 1

    pontos_restantes = total_disponivel - gastos_reais
    return max(0, pontos_restantes)

# ══════════════════════════════════════════════════════════════════════════════
# Normalização — garante retrocompatibilidade com fichas antigas
# ══════════════════════════════════════════════════════════════════════════════

def normalizar_ficha(ficha: dict) -> dict:
    """
    Preenche campos ausentes com defaults seguros.
    Fichas criadas antes da v2 continuam funcionando normalmente.
    """
    lp = ficha.get("lp", 0) or 0

    ficha.setdefault("atualizado_em", ficha.get("criado_em", ""))
    ficha.setdefault("pontos_atributo_gastos", 0)
    ficha.setdefault("pontos_atributo_gastos", 0)
    ficha.setdefault("pontos_extras_temp", 0)

    # Garante que 'atributos' exista com os valores base
    if "atributos" not in ficha:
        ficha["atributos"] = {
            "AGI": 1, "FOR": 1, "INT": 1, "VIG": 1, "PRE": 1
        }

    # Estado de sessão (PV, Sanidade, PE)
    if "estado" not in ficha:
        ficha["estado"] = {
            "pv_atual":   lp,
            "pv_maximo":  lp,
            "san_atual":  lp,
            "san_maximo": lp,
            "pe_atual":   ficha.get("totais_nex", {}).get("feiticos", 0),
            "pe_maximo":  ficha.get("totais_nex", {}).get("feiticos", 0),
        }
    else:
        ficha["estado"].setdefault("pv_atual",   lp)
        ficha["estado"].setdefault("pv_maximo",  lp)
        ficha["estado"].setdefault("san_atual",  lp)
        ficha["estado"].setdefault("san_maximo", lp)
        ficha["estado"].setdefault("pe_atual",   0)
        ficha["estado"].setdefault("pe_maximo",  0)

    # Combate
    ficha.setdefault("estilo_luta", {
        "id": None, "nome": None, "descricao": None,
        "origem": "padrao", "efeito": None,
    })
    ficha.setdefault("tecnica", {
        "id": None, "nome": None, "descricao": None,
        "origem": "padrao", "efeito": None,
    })
    ficha.setdefault("feiticos_custom", [])

    # Inventário
    ficha.setdefault("inventario", {"dinheiro": 0, "itens": []})

    # Anotações
    ficha.setdefault("anotacoes", "")
    ficha.setdefault("historico_sessoes", [])

    return ficha


def salvar_ficha(ficha: dict):
    """Sobrescreve o .json da ficha no disco e atualiza atualizado_em."""
    caminho = ficha.get("_arquivo")
    if not caminho:
        return
    ficha["atualizado_em"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    dados = {k: v for k, v in ficha.items() if k != "_arquivo"}
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


# ══════════════════════════════════════════════════════════════════════════════
# Widget: BarraRecurso (PV / Sanidade / PE)
# ══════════════════════════════════════════════════════════════════════════════

class BarraRecurso(ctk.CTkFrame):
    """
    Barra de recurso reutilizável.
    Layout: label + fração  |  barra de progresso  |  [−] [entrada] [+]  [máx]
    on_change(novo_atual) é chamado após cada alteração.
    """

    def __init__(self, parent, label: str, atual: int, maximo: int,
                 cor_barra: str, on_change=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self._atual     = atual
        self._maximo    = maximo
        self._on_change = on_change

        # Linha superior: nome + fracção
        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.pack(fill="x")

        ctk.CTkLabel(topo, text=label,
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#cccccc").pack(side="left")

        self._lbl_fracao = ctk.CTkLabel(topo, text=self._texto_fracao(),
                                        font=ctk.CTkFont(size=12),
                                        text_color="#888888")
        self._lbl_fracao.pack(side="right")

        # Barra visual
        self._barra = ctk.CTkProgressBar(self, height=8, corner_radius=4,
                                         progress_color=cor_barra,
                                         fg_color="#2a2a2a")
        self._barra.pack(fill="x", pady=(4, 6))
        self._atualizar_barra()

        # Controles: − | entrada | + | máx
        controles = ctk.CTkFrame(self, fg_color="transparent")
        controles.pack(fill="x")

        ctk.CTkButton(controles, text="−", width=36, height=30,
                      font=ctk.CTkFont(size=18),
                      fg_color="#2a2a2a", hover_color="#3a3a3a",
                      command=self._decrementar).pack(side="left")

        self._entrada = ctk.CTkEntry(controles, width=70, height=30,
                                     justify="center",
                                     font=ctk.CTkFont(size=14, weight="bold"))
        self._entrada.insert(0, str(self._atual))
        self._entrada.pack(side="left", padx=6)
        self._entrada.bind("<Return>",   self._ao_confirmar_entrada)
        self._entrada.bind("<FocusOut>", self._ao_confirmar_entrada)

        ctk.CTkButton(controles, text="+", width=36, height=30,
                      font=ctk.CTkFont(size=18),
                      fg_color="#2a2a2a", hover_color="#3a3a3a",
                      command=self._incrementar).pack(side="left")

        ctk.CTkButton(controles, text="máx", width=46, height=30,
                      font=ctk.CTkFont(size=11),
                      fg_color="transparent", border_width=1,
                      border_color="#444444", text_color="#888888",
                      command=self._editar_maximo).pack(side="right")

    # ── Helpers internos ──────────────────────────────────────────────────────

    def _texto_fracao(self) -> str:
        return f"{self._atual} / {self._maximo}"

    def _atualizar_barra(self):
        prog = max(0.0, min(1.0, self._atual / self._maximo)) if self._maximo > 0 else 0.0
        self._barra.set(prog)

    def _atualizar_ui(self):
        self._lbl_fracao.configure(text=self._texto_fracao())
        self._atualizar_barra()
        self._entrada.delete(0, "end")
        self._entrada.insert(0, str(self._atual))
        if self._on_change:
            self._on_change(self._atual)

    # ── Ações ─────────────────────────────────────────────────────────────────

    def _decrementar(self):
        self._atual = max(0, self._atual - 1)
        self._atualizar_ui()

    def _incrementar(self):
        self._atual = min(self._maximo, self._atual + 1)
        self._atualizar_ui()

    def _ao_confirmar_entrada(self, _event=None):
        try:
            valor = int(self._entrada.get())
            self._atual = max(0, min(self._maximo, valor))
        except ValueError:
            pass
        self._atualizar_ui()

    def _editar_maximo(self):
        popup = ctk.CTkToplevel(self.winfo_toplevel())
        popup.title("Editar máximo")
        popup.geometry("280x150")
        popup.resizable(False, False)
        popup.after(100, popup.grab_set)

        ctk.CTkLabel(popup, text="Novo valor máximo:",
                     font=ctk.CTkFont(size=13)).pack(pady=(20, 6))

        entrada = ctk.CTkEntry(popup, width=100, justify="center",
                               font=ctk.CTkFont(size=14))
        entrada.insert(0, str(self._maximo))
        entrada.pack()
        entrada.focus()

        def confirmar():
            try:
                novo = int(entrada.get())
                if novo >= 0:
                    self._maximo = novo
                    self._atual  = min(self._atual, self._maximo)
                    self._atualizar_ui()
            except ValueError:
                pass
            popup.destroy()

        entrada.bind("<Return>", lambda _: confirmar())
        ctk.CTkButton(popup, text="Confirmar", command=confirmar).pack(pady=12)

    # ── API pública ───────────────────────────────────────────────────────────

    def get_atual(self) -> int:
        return self._atual

    def get_maximo(self) -> int:
        return self._maximo

    def set_valores(self, atual: int, maximo: int):
        self._atual  = atual
        self._maximo = maximo
        self._atualizar_ui()


# ══════════════════════════════════════════════════════════════════════════════
# Painéis das abas
# ══════════════════════════════════════════════════════════════════════════════

class PainelPericias(ctk.CTkFrame):
    """Aba: nós de skill tree comprados, agrupados por atributo."""

    CORES = {
        "AGI": "#e67e22", "FOR": "#e74c3c", "INT": "#3498db",
        "VIG": "#2ecc71", "PRE": "#9b59b6", "GERAL": "#95a5a6",
    }

    def __init__(self, parent, ficha: dict, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._ficha = ficha
        self._construir()

    def _construir(self):
        for w in self.winfo_children():
            w.destroy()

        nos_comprados = self._ficha.get("nos_comprados", {})

        if not any(nos_comprados.values()):
            ctk.CTkLabel(self, text="Nenhuma perícia comprada ainda.",
                         font=ctk.CTkFont(size=13), text_color="gray").pack(pady=40)
            return

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        for aba, nos in nos_comprados.items():
            if not nos:
                continue
            cor = self.CORES.get(aba, "#888888")

            header = ctk.CTkFrame(scroll, fg_color="transparent")
            header.pack(fill="x", pady=(12, 4))

            ctk.CTkFrame(header, width=4, height=16,
                         fg_color=cor, corner_radius=2).pack(side="left", padx=(0, 8))
            ctk.CTkLabel(header, text=aba,
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=cor).pack(side="left")
            ctk.CTkLabel(header, text=f"{len(nos)} nós",
                         font=ctk.CTkFont(size=11),
                         text_color="#555555").pack(side="right")

            grade = ctk.CTkFrame(scroll, fg_color="transparent")
            grade.pack(fill="x", pady=(0, 4))

            for no_id in nos:
                chip = ctk.CTkFrame(grade, fg_color="#1e1e1e",
                                    corner_radius=6, border_width=1,
                                    border_color="#333333")
                chip.pack(side="left", padx=4, pady=3)
                ctk.CTkLabel(chip, text=no_id,
                             font=ctk.CTkFont(size=11),
                             text_color="#aaaaaa").pack(padx=8, pady=4)

    def atualizar(self):
        self._construir()


class PainelFeiticos(ctk.CTkFrame):
    """Aba: feitiços escolhidos (padrão + custom)."""

    CAMINHO_FEITICOS = "data/feiticos.json"
    CAMINHO_CUSTOM   = "data/feiticos_custom.json"

    def __init__(self, parent, ficha: dict, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._ficha = ficha
        self._db    = self._carregar_db()
        self._construir()

    def _carregar_db(self) -> dict:
        db = {}
        for caminho in [self.CAMINHO_FEITICOS, self.CAMINHO_CUSTOM]:
            if os.path.exists(caminho):
                try:
                    with open(caminho, "r", encoding="utf-8") as f:
                        for item in json.load(f):
                            db[item["id"]] = item
                except Exception:
                    pass
        return db

    def _construir(self):
        for w in self.winfo_children():
            w.destroy()

        ids = self._ficha.get("feiticos", []) + self._ficha.get("feiticos_custom", [])

        if not ids:
            ctk.CTkLabel(self, text="Nenhum feitiço escolhido.",
                         font=ctk.CTkFont(size=13), text_color="gray").pack(pady=40)
            return

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        for fid in ids:
            f = self._db.get(fid)
            if f:
                self._card_completo(scroll, f)
            else:
                self._card_simples(scroll, fid)

    def _card_completo(self, parent, f: dict):
        card = ctk.CTkFrame(parent, fg_color="#1e1e1e",
                            corner_radius=8, border_width=1,
                            border_color="#333333")
        card.pack(fill="x", pady=4)

        topo = ctk.CTkFrame(card, fg_color="transparent")
        topo.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(topo, text=f.get("nome", f.get("id", "?")),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")

        classe = f.get("classe", "")
        if classe:
            ctk.CTkLabel(topo, text=classe,
                         font=ctk.CTkFont(size=11),
                         text_color="#666666").pack(side="right")

        desc = f.get("descricao", "")
        if desc:
            ctk.CTkLabel(card, text=desc, wraplength=500, justify="left",
                         font=ctk.CTkFont(size=12),
                         text_color="#aaaaaa").pack(anchor="w", padx=12, pady=(0, 10))

    def _card_simples(self, parent, fid: str):
        card = ctk.CTkFrame(parent, fg_color="#1a1a1a",
                            corner_radius=6, border_width=1,
                            border_color="#2a2a2a")
        card.pack(fill="x", pady=2)
        ctk.CTkLabel(card, text=fid, font=ctk.CTkFont(size=12),
                     text_color="#666666").pack(anchor="w", padx=12, pady=6)

    def atualizar(self):
        self._db = self._carregar_db()
        self._construir()


class PainelEstiloLuta(ctk.CTkFrame):
    """Aba dedicada ao Estilo de Luta."""

    def __init__(self, parent, ficha: dict, on_save=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._ficha = ficha
        self._on_save = on_save
        self._construir()

    def _construir(self):
        for w in self.winfo_children():
            w.destroy()

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        self._secao(scroll, "Estilo de Luta", "estilo_luta")

    def _secao(self, parent, titulo: str, chave: str):
        # Código idêntico ao método _secao da classe PainelEstiloTecnica
        dados = self._ficha.get(chave, {}) or {}

        ctk.CTkLabel(parent, text=titulo,
                     font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", pady=(0, 8))

        card = ctk.CTkFrame(parent, fg_color="#1e1e1e",
                            corner_radius=8, border_width=1,
                            border_color="#333333")
        card.pack(fill="x", pady=(0, 8))

        linha = ctk.CTkFrame(card, fg_color="transparent")
        linha.pack(fill="x", padx=12, pady=(10, 4))

        nome_exib = dados.get("nome") or "Não definido"
        ctk.CTkLabel(linha, text=nome_exib,
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")

        if dados.get("origem") == "custom":
            ctk.CTkLabel(linha, text="personalizado",
                         font=ctk.CTkFont(size=11),
                         text_color="#9b59b6").pack(side="right")

        efeito = dados.get("efeito") or dados.get("descricao") or ""
        if efeito:
            ctk.CTkLabel(card, text=efeito, wraplength=500, justify="left",
                         font=ctk.CTkFont(size=12),
                         text_color="#aaaaaa").pack(anchor="w", padx=12, pady=(0, 10))

        ctk.CTkButton(parent, text=f"Editar {titulo}", width=160,
                      fg_color="transparent", border_width=1,
                      border_color="#444444",
                      command=lambda: self._popup_editar(chave, titulo)
                      ).pack(anchor="w")

    def _popup_editar(self, chave: str, titulo: str):
        # Exatamente igual ao popup original
        dados = self._ficha.get(chave, {}) or {}

        popup = ctk.CTkToplevel(self.winfo_toplevel())
        popup.title(f"Editar {titulo}")
        popup.geometry("480x400")
        popup.after(100, popup.grab_set)

        ctk.CTkLabel(popup, text=titulo,
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 12))

        ctk.CTkLabel(popup, text="Nome:", anchor="w").pack(fill="x", padx=20)
        e_nome = ctk.CTkEntry(popup, width=440)
        e_nome.insert(0, dados.get("nome") or "")
        e_nome.pack(padx=20, pady=(4, 12))

        ctk.CTkLabel(popup, text="Efeito / Descrição:", anchor="w").pack(fill="x", padx=20)
        e_efeito = ctk.CTkTextbox(popup, height=140, width=440)
        e_efeito.insert("1.0", dados.get("efeito") or dados.get("descricao") or "")
        e_efeito.pack(padx=20, pady=(4, 16))

        def salvar():
            self._ficha[chave] = {
                "id":       dados.get("id"),
                "nome":     e_nome.get().strip() or None,
                "descricao": None,
                "origem":   "custom",
                "efeito":   e_efeito.get("1.0", "end-1c").strip() or None,
            }
            if self._on_save:
                self._on_save()
            popup.destroy()
            self._construir()

        ctk.CTkButton(popup, text="Salvar", command=salvar).pack()

    def atualizar(self):
        self._construir()


class PainelTecnica(PainelEstiloLuta):
    """Aba dedicada à Técnica. Herda de PainelEstiloLuta e só muda o título/chave."""

    def __init__(self, parent, ficha: dict, on_save=None, **kwargs):
        # Inicializa normalmente, mas forçamos a chave e título específicos
        super().__init__(parent, ficha, on_save, **kwargs)

    def _construir(self):
        for w in self.winfo_children():
            w.destroy()

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        self._secao(scroll, "Técnica", "tecnica")


class PainelInventario(ctk.CTkFrame):
    """Aba: dinheiro e lista de itens."""

    def __init__(self, parent, ficha: dict, on_save=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._ficha   = ficha
        self._on_save = on_save
        self._construir()

    def _construir(self):
        for w in self.winfo_children():
            w.destroy()

        inv = self._ficha.get("inventario", {})

        # Dinheiro
        d_frame = ctk.CTkFrame(self, fg_color="#1e1e1e",
                               corner_radius=8, border_width=1,
                               border_color="#333333")
        d_frame.pack(fill="x", pady=(0, 12))

        linha = ctk.CTkFrame(d_frame, fg_color="transparent")
        linha.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(linha, text="Dinheiro",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")

        self._entrada_dinheiro = ctk.CTkEntry(linha, width=110, justify="center",
                                              font=ctk.CTkFont(size=13))
        self._entrada_dinheiro.insert(0, str(inv.get("dinheiro", 0)))
        self._entrada_dinheiro.pack(side="right")
        self._entrada_dinheiro.bind("<Return>",   self._salvar_dinheiro)
        self._entrada_dinheiro.bind("<FocusOut>", self._salvar_dinheiro)

        # Cabeçalho itens
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(header, text="Itens",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="+ Adicionar", width=110, height=28,
                      font=ctk.CTkFont(size=12),
                      command=self._popup_novo_item).pack(side="right")

        # Lista
        self._lista_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._lista_frame.pack(fill="both", expand=True)
        self._renderizar_itens()

    def _renderizar_itens(self):
        for w in self._lista_frame.winfo_children():
            w.destroy()

        itens = self._ficha.get("inventario", {}).get("itens", [])

        if not itens:
            ctk.CTkLabel(self._lista_frame, text="Inventário vazio.",
                         text_color="gray", font=ctk.CTkFont(size=12)).pack(pady=20)
            return

        CORES_TIPO = {"arma": "#e74c3c", "armor": "#3498db", "item": "#2ecc71"}

        for i, item in enumerate(itens):
            card = ctk.CTkFrame(self._lista_frame, fg_color="#1e1e1e",
                                corner_radius=6, border_width=1,
                                border_color="#2a2a2a")
            card.pack(fill="x", pady=3)

            linha = ctk.CTkFrame(card, fg_color="transparent")
            linha.pack(fill="x", padx=10, pady=(8, 4))

            cor = CORES_TIPO.get(item.get("tipo", "item"), "#888888")
            ctk.CTkFrame(linha, width=3, height=16,
                         fg_color=cor, corner_radius=1).pack(side="left", padx=(0, 8))

            ctk.CTkLabel(linha,
                         text=f"{item.get('nome', '?')}  ×{item.get('quantidade', 1)}",
                         font=ctk.CTkFont(size=13)).pack(side="left")

            ctk.CTkButton(linha, text="×", width=24, height=24,
                          fg_color="transparent", text_color="#666666",
                          hover_color="#2a2a2a",
                          command=lambda idx=i: self._remover_item(idx)).pack(side="right")

            desc = item.get("descricao", "")
            if desc:
                ctk.CTkLabel(card, text=desc, wraplength=480,
                             justify="left", font=ctk.CTkFont(size=11),
                             text_color="#666666").pack(anchor="w", padx=10, pady=(0, 8))

    def _salvar_dinheiro(self, _event=None):
        try:
            valor = float(self._entrada_dinheiro.get())
            self._ficha.setdefault("inventario", {})["dinheiro"] = valor
            if self._on_save:
                self._on_save()
        except ValueError:
            pass

    def _popup_novo_item(self):
        popup = ctk.CTkToplevel(self.winfo_toplevel())
        popup.title("Novo item")
        popup.geometry("400x360")
        popup.after(100, popup.grab_set)

        ctk.CTkLabel(popup, text="Nome:", anchor="w").pack(fill="x", padx=20, pady=(20, 0))
        e_nome = ctk.CTkEntry(popup, width=360)
        e_nome.pack(padx=20, pady=(4, 10))

        ctk.CTkLabel(popup, text="Descrição:", anchor="w").pack(fill="x", padx=20)
        e_desc = ctk.CTkEntry(popup, width=360)
        e_desc.pack(padx=20, pady=(4, 10))

        tipo_var = ctk.StringVar(value="item")
        tipos = ctk.CTkFrame(popup, fg_color="transparent")
        tipos.pack(padx=20, pady=(0, 10), fill="x")
        ctk.CTkLabel(tipos, text="Tipo:").pack(side="left", padx=(0, 10))
        for t in ("item", "arma", "armor"):
            ctk.CTkRadioButton(tipos, text=t, value=t,
                               variable=tipo_var).pack(side="left", padx=6)

        ctk.CTkLabel(popup, text="Quantidade:", anchor="w").pack(fill="x", padx=20)
        e_qtd = ctk.CTkEntry(popup, width=100)
        e_qtd.insert(0, "1")
        e_qtd.pack(anchor="w", padx=20, pady=(4, 16))

        def salvar():
            nome = e_nome.get().strip()
            if not nome:
                return
            try:
                qtd = int(e_qtd.get())
            except ValueError:
                qtd = 1
            self._ficha.setdefault("inventario", {}).setdefault("itens", []).append({
                "nome":       nome,
                "descricao":  e_desc.get().strip(),
                "tipo":       tipo_var.get(),
                "quantidade": qtd,
            })
            if self._on_save:
                self._on_save()
            popup.destroy()
            self._renderizar_itens()

        ctk.CTkButton(popup, text="Adicionar", command=salvar).pack()

    def _remover_item(self, idx: int):
        itens = self._ficha.get("inventario", {}).get("itens", [])
        if 0 <= idx < len(itens):
            itens.pop(idx)
            if self._on_save:
                self._on_save()
            self._renderizar_itens()

    def atualizar(self):
        self._construir()


class PainelAnotacoes(ctk.CTkFrame):
    """Aba: texto livre para anotações de sessão com autosave por debounce."""

    def __init__(self, parent, ficha: dict, on_save=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._ficha          = ficha
        self._on_save        = on_save
        self._timer_autosave = None
        self._construir()

    def _construir(self):
        ctk.CTkLabel(self, text="Anotações de sessão",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 8))

        self._texto = ctk.CTkTextbox(self, font=ctk.CTkFont(size=13),
                                     fg_color="#1e1e1e", corner_radius=8,
                                     border_width=1, border_color="#333333")
        self._texto.pack(fill="both", expand=True)
        self._texto.insert("1.0", self._ficha.get("anotacoes", ""))
        self._texto.bind("<KeyRelease>", self._ao_digitar)

    def _ao_digitar(self, _event=None):
        if self._timer_autosave:
            self.after_cancel(self._timer_autosave)
        self._timer_autosave = self.after(1500, self._salvar)

    def _salvar(self):
        self._ficha["anotacoes"] = self._texto.get("1.0", "end-1c")
        if self._on_save:
            self._on_save()

    def atualizar(self):
        self._texto.delete("1.0", "end")
        self._texto.insert("1.0", self._ficha.get("anotacoes", ""))


# ══════════════════════════════════════════════════════════════════════════════
# Tela principal: FichaPersonagem
# ══════════════════════════════════════════════════════════════════════════════

class FichaPersonagem:
    """
    Tela de gerenciamento de ficha — substitui a janela do gerenciador.

    Parâmetros
    ----------
    app       : janela ctk.CTk existente (reutilizada)
    ficha     : dict normalizado com _arquivo preenchido
    on_voltar : callback chamado ao clicar Voltar
    """

    ABA_NOMES = [
        "Perícias",
        "Skill Tree",
        "Feitiços",
        "Estilo de Luta",
        "Técnica",
        "Inventário",
        "Anotações",
    ]

    CORES_RECURSO = {
        "pv":  "#e74c3c",
        "san": "#3498db",
        "pe":  "#f39c12",
    }

    CORES_ATRIBUTO = {
        "AGI": "#e67e22", "FOR": "#e74c3c",
        "INT": "#3498db", "VIG": "#2ecc71",
        "PRE": "#9b59b6",
    }

    def __init__(self, app: ctk.CTk, ficha: dict, on_voltar=None):
        self.app       = app
        self.ficha     = normalizar_ficha(ficha)
        self.on_voltar = on_voltar

        self._aba_ativa   = 0
        self._paineis_aba: dict[int, ctk.CTkFrame] = {}
        self._barras:      dict[str, BarraRecurso]  = {}

        # ══════════════════════════════════════════════════════════════════════
        # NOVO: Controle de atributos editáveis
        # ══════════════════════════════════════════════════════════════════════
        self._attr_widgets = {}        # guarda referências aos labels de valor
        self._lbl_pontos_disponiveis = None  # será criado depois
        # ══════════════════════════════════════════════════════════════════════

        self._fontes()
        self._construir()

    # ── Fontes ────────────────────────────────────────────────────────────────

    def _fontes(self):
        self.f_titulo    = ctk.CTkFont(size=22, weight="bold")
        self.f_subtitulo = ctk.CTkFont(size=13)
        self.f_secao     = ctk.CTkFont(size=12, weight="bold")
        self.f_valor     = ctk.CTkFont(size=20, weight="bold")
        self.f_label     = ctk.CTkFont(size=11)
        self.f_botao     = ctk.CTkFont(size=13)

    # ── Layout geral ──────────────────────────────────────────────────────────

    def _construir(self):
        for w in self.app.winfo_children():
            w.destroy()

        self.app.geometry("1100x700")
        self.app.minsize(900, 560)
        self.app.title(f"Projeto BITE — {self.ficha.get('nome', 'Ficha')}")

        raiz = ctk.CTkFrame(self.app, fg_color="transparent")
        raiz.pack(fill="both", expand=True, padx=16, pady=16)
        raiz.columnconfigure(1, weight=1)
        raiz.rowconfigure(0, weight=1)

        # Painel lateral fixo
        self._lateral = ctk.CTkFrame(raiz, width=280, corner_radius=12,
                                     fg_color="#161616", border_width=1,
                                     border_color="#2a2a2a")
        self._lateral.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self._lateral.grid_propagate(False)

        # Área principal
        self._area = ctk.CTkFrame(raiz, corner_radius=12,
                                  fg_color="#161616", border_width=1,
                                  border_color="#2a2a2a")
        self._area.grid(row=0, column=1, sticky="nsew")
        self._area.rowconfigure(1, weight=1)
        self._area.columnconfigure(0, weight=1)

        self._construir_lateral()
        self._construir_abas()
        self._mostrar_aba(0)

    # ── Painel lateral ────────────────────────────────────────────────────────

    def _construir_lateral(self):
        lat = self._lateral

        # Botão voltar
        ctk.CTkButton(lat, text="← Voltar", font=self.f_botao, width=90,
                      fg_color="transparent", border_width=1,
                      border_color="#333333",
                      command=self._voltar).pack(anchor="nw", padx=12, pady=(12, 0))

        # Identidade
        ctk.CTkLabel(lat, text=self.ficha.get("nome", "—"),
                     font=self.f_titulo,
                     wraplength=240).pack(pady=(10, 2), padx=16)

        ctk.CTkLabel(lat,
                     text=f"{self.ficha.get('classe','—')}  ·  {self.ficha.get('trilha','—')}",
                     font=self.f_subtitulo, text_color="#888888",
                     wraplength=240).pack(pady=(0, 2), padx=16)

        ctk.CTkLabel(lat,
                     text=f"NEX {self.ficha.get('nex','—')}  ·  {self.ficha.get('grau','—')}",
                     font=ctk.CTkFont(size=11), text_color="#555555",
                     wraplength=240).pack(pady=(0, 10), padx=16)

        ctk.CTkFrame(lat, height=1, fg_color="#2a2a2a").pack(fill="x", padx=12)

                # Barras de recursos – agora fixas, sem scroll
        rec_frame = ctk.CTkFrame(lat, fg_color="transparent")
        rec_frame.pack(fill="x", padx=16, pady=12)

        estado = self.ficha["estado"]
        specs = [
            ("PV",       "pv",  "pv_atual",  "pv_maximo"),
            ("Sanidade", "san", "san_atual",  "san_maximo"),
            ("PE",       "pe",  "pe_atual",   "pe_maximo"),
        ]

        for nome_exib, chave, k_atual, k_max in specs:
            barra = BarraRecurso(
                rec_frame,   # <--- aqui muda de rec_scroll para rec_frame
                label    = nome_exib,
                atual    = estado.get(k_atual, 0),
                maximo   = estado.get(k_max,   0),
                cor_barra= self.CORES_RECURSO[chave],
                on_change= self._make_callback(chave, k_atual, k_max),
            )
            barra.pack(fill="x", pady=(0, 14))
            self._barras[chave] = barra

        ctk.CTkFrame(lat, height=1, fg_color="#2a2a2a").pack(fill="x", padx=12)

        # ══════════════════════════════════════════════════════════════════════
        # Atributos (EDITÁVEIS)
        # ══════════════════════════════════════════════════════════════════════
        ctk.CTkFrame(lat, height=1, fg_color="#2a2a2a").pack(fill="x", padx=12, pady=(6, 6))

        # Cabeçalho com pontos disponíveis
        header_attr = ctk.CTkFrame(lat, fg_color="transparent")
        header_attr.pack(fill="x", padx=16, pady=(4, 6))

        ctk.CTkLabel(header_attr, text="ATRIBUTOS",
                     font=self.f_secao, text_color="#555555").pack(side="left")

        pontos_disp = calcular_pontos_disponiveis_ficha(self.ficha)
        self._lbl_pontos_disponiveis = ctk.CTkLabel(
            header_attr,
            text=f"{pontos_disp} pts",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#f1c40f" if pontos_disp > 0 else "#888888"
        )
        self._lbl_pontos_disponiveis.pack(side="right")

        # Scroll frame para os atributos (caso haja muitos)
        attr_scroll = ctk.CTkScrollableFrame(lat, fg_color="transparent", height=200)
        attr_scroll.pack(fill="x", padx=8, pady=(0, 8))

        # Container interno (para alinhamento)
        attr_container = ctk.CTkFrame(attr_scroll, fg_color="transparent")
        attr_container.pack(fill="x")

        # Para cada atributo, criar uma linha com: sigla | valor | [+] [-]
        for sigla, valor in self.ficha.get("atributos", {}).items():
            cor = self.CORES_ATRIBUTO.get(sigla, "#888888")

            linha = ctk.CTkFrame(attr_container, fg_color="transparent")
            linha.pack(fill="x", pady=2)

            # Sigla do atributo
            ctk.CTkLabel(linha, text=sigla,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=cor, width=40).pack(side="left", padx=(8, 4))

            # Valor atual
            lbl_valor = ctk.CTkLabel(linha, text=str(valor),
                                     font=ctk.CTkFont(size=16, weight="bold"),
                                     text_color="#ffffff", width=30)
            lbl_valor.pack(side="left", padx=4)
            self._attr_widgets[sigla] = lbl_valor

            # Botão diminuir (-)
            btn_menos = ctk.CTkButton(
                linha, text="−", width=28, height=28,
                font=ctk.CTkFont(size=14),
                fg_color="#2a2a2a", hover_color="#3a3a3a",
                command=lambda s=sigla: self._ajustar_atributo(s, -1)
            )
            btn_menos.pack(side="right", padx=2)

            # Botão aumentar (+)
            btn_mais = ctk.CTkButton(
                linha, text="+", width=28, height=28,
                font=ctk.CTkFont(size=14),
                fg_color="#2a2a2a", hover_color="#3a3a3a",
                command=lambda s=sigla: self._ajustar_atributo(s, +1)
            )
            btn_mais.pack(side="right", padx=2)

        # ══════════════════════════════════════════════════════════════════════
        # Pontos extras (buffs temporários)
        # ══════════════════════════════════════════════════════════════════════
        extras_frame = ctk.CTkFrame(lat, fg_color="transparent")
        extras_frame.pack(fill="x", padx=16, pady=(4, 8))

        ctk.CTkLabel(extras_frame, text="Pontos extras:",
                     font=ctk.CTkFont(size=11), text_color="#666666").pack(side="left")

        self._entrada_extras = ctk.CTkEntry(extras_frame, width=50, height=26,
                                            font=ctk.CTkFont(size=12),
                                            placeholder_text="0")
        self._entrada_extras.pack(side="left", padx=(4, 4))

        ctk.CTkButton(extras_frame, text="Adicionar", width=70, height=26,
                      font=ctk.CTkFont(size=11),
                      fg_color="#2a2a2a", hover_color="#3a3a3a",
                      command=self._adicionar_pontos_extras).pack(side="left")

        # Indicador de salvamento
        self._lbl_salvo = ctk.CTkLabel(lat, text="",
                                       font=ctk.CTkFont(size=10),
                                       text_color="#444444")
        self._lbl_salvo.pack(pady=(8, 4), padx=16)

    def _make_callback(self, chave: str, k_atual: str, k_max: str):
        """Fábrica de callbacks para as barras de recurso."""
        def callback(_valor_ignorado: int):
            barra = self._barras[chave]
            self.ficha["estado"][k_atual] = barra.get_atual()
            self.ficha["estado"][k_max]   = barra.get_maximo()
            self._salvar()
        return callback

    # ── Abas ──────────────────────────────────────────────────────────────────

    def _construir_abas(self):
        area = self._area

        # Barra de navegação das abas
        nav = ctk.CTkFrame(area, fg_color="#0f0f0f", height=42, corner_radius=0)
        nav.grid(row=0, column=0, sticky="ew")
        nav.pack_propagate(False)

        self._botoes_aba: list[ctk.CTkButton] = []
        for i, nome in enumerate(self.ABA_NOMES):
            btn = ctk.CTkButton(
                nav, text=nome, height=42, font=self.f_botao,
                fg_color="transparent", text_color="#666666",
                hover_color="#1a1a1a", corner_radius=0,
                command=lambda idx=i: self._mostrar_aba(idx),
            )
            btn.pack(side="left", padx=2)
            self._botoes_aba.append(btn)

        # Frame de conteúdo das abas
        self._frame_conteudo = ctk.CTkFrame(area, fg_color="transparent")
        self._frame_conteudo.grid(row=1, column=0, sticky="nsew", padx=16, pady=16)
        self._frame_conteudo.rowconfigure(0, weight=1)
        self._frame_conteudo.columnconfigure(0, weight=1)

    def _mostrar_aba(self, idx: int):
        self._aba_ativa = idx

        # Destaca aba ativa
        for i, btn in enumerate(self._botoes_aba):
            if i == idx:
                btn.configure(text_color="#ffffff", fg_color="#1e1e1e")
            else:
                btn.configure(text_color="#666666", fg_color="transparent")

        # Oculta todos os painéis
        for painel in self._paineis_aba.values():
            painel.grid_forget()

        # Cria painel sob demanda (lazy)
        if idx not in self._paineis_aba:
            self._paineis_aba[idx] = self._criar_painel(idx)

        self._paineis_aba[idx].grid(row=0, column=0, sticky="nsew")

    def _criar_painel(self, idx: int) -> ctk.CTkFrame:
        """Instancia o painel correto para cada índice de aba."""
        nome = self.ABA_NOMES[idx]
        pai  = self._frame_conteudo

        fabricas = {
            "Perícias":        lambda: PainelPericias(pai, self.ficha),
            "Skill Tree":      lambda: PainelPericias(pai, self.ficha),  # placeholder
            "Feitiços":        lambda: PainelFeiticos(pai, self.ficha),
            "Estilo de Luta":  lambda: PainelEstiloLuta(pai, self.ficha, on_save=self._salvar),
            "Técnica":         lambda: PainelTecnica(pai, self.ficha, on_save=self._salvar),
            "Inventário":      lambda: PainelInventario(pai, self.ficha, on_save=self._salvar),
            "Anotações":       lambda: PainelAnotacoes(pai, self.ficha, on_save=self._salvar),
        }

        fabrica = fabricas.get(nome)
        if fabrica:
            return fabrica()

        # Fallback genérico para abas ainda não implementadas
        frame = ctk.CTkFrame(pai, fg_color="transparent")
        ctk.CTkLabel(frame, text=f"'{nome}' em construção.",
                     text_color="gray").pack(pady=40)
        return frame

    # ── Persistência ──────────────────────────────────────────────────────────

    def _salvar(self):
        salvar_ficha(self.ficha)
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self._lbl_salvo.configure(text=f"salvo às {ts}")

    # ── Navegação ─────────────────────────────────────────────────────────────

    # ══════════════════════════════════════════════════════════════════════════
    # Manipulação de atributos (edição na lateral)
    # ══════════════════════════════════════════════════════════════════════════

    def _atualizar_ui_atributos(self):
        """Atualiza labels de valor e pontos disponíveis após alteração."""
        # Atualiza labels de valor
        for sigla, lbl in self._attr_widgets.items():
            valor = self.ficha["atributos"][sigla]
            lbl.configure(text=str(valor))

        # Recalcula e atualiza pontos disponíveis
        pontos = calcular_pontos_disponiveis_ficha(self.ficha)
        if self._lbl_pontos_disponiveis:
            self._lbl_pontos_disponiveis.configure(
                text=f"{pontos} pts",
                text_color="#f1c40f" if pontos > 0 else "#888888"
            )

        # Salva automaticamente
        self._salvar()

    def _ajustar_atributo(self, sigla: str, delta: int):
        """Aumenta ou diminui o valor do atributo, respeitando limites e pontos disponíveis."""
        valor_atual = self.ficha["atributos"][sigla]
        pontos_disp = calcular_pontos_disponiveis_ficha(self.ficha)

        if delta > 0:
            # Aumentar: precisa de pontos e não pode ultrapassar LIMITE_NORMAL
            if pontos_disp <= 0:
                return  # Poderia tocar um aviso sonoro, mas por ora silencioso
            if valor_atual >= LIMITE_NORMAL:
                return
            self.ficha["atributos"][sigla] += 1
            self.ficha["pontos_atributo_gastos"] = self.ficha.get("pontos_atributo_gastos", 0) + 1
        else:  # delta < 0
            # Diminuir: não pode ficar abaixo de 0
            if valor_atual <= 0:
                return
            self.ficha["atributos"][sigla] -= 1
            self.ficha["pontos_atributo_gastos"] = max(0, self.ficha.get("pontos_atributo_gastos", 0) - 1)

        self._atualizar_ui_atributos()

    def _adicionar_pontos_extras(self):
        """Adiciona pontos temporários (buffs) ao pool disponível."""
        texto = self._entrada_extras.get().strip()
        if not texto:
            return
        try:
            qtd = int(texto)
        except ValueError:
            return
        if qtd <= 0:
            return

        # Armazena como campo separado (não interfere nos gastos fixos)
        self.ficha["pontos_extras_temp"] = self.ficha.get("pontos_extras_temp", 0) + qtd
        self._entrada_extras.delete(0, "end")
        self._atualizar_ui_atributos()

    def _voltar(self):
        if self.on_voltar:
            self.on_voltar()