# views/Painel_EstiloLuta.py
import customtkinter as ctk
import uuid
from tkinter import messagebox
from views.EfeitosEditorFrame import EfeitosEditorFrame
from views.Efeitos_Popup import EfeitosPopup
from utils.helpers import formatar_numero_grande
from utils.estiloLuta import executar_estilo_luta

class PainelEstiloLuta(ctk.CTkFrame):
    """Aba: gerenciamento de habilidades de estilo de luta."""

    TIPO_MECANICA_OPCOES = ["Ataque", "Teste de Resistência", "Passiva"]

    TIPO_EFEITO_OPCOES = ["tecnica", "corpo", "desarmado", "invocacao", "maldicao", "shinobi", "estilo_luta", "energia_amaldicoada"]
    TIPO_EFEITO_NOMES = {
        "tecnica": "Técnica",
        "corpo": "Corpo a Corpo",
        "desarmado": "Desarmado",
        "invocacao": "Invocação",
        "maldicao": "Maldição",
        "shinobi": "Shinobi",
        "estilo_luta": "Estilo de Luta",
        "energia_amaldicoada": "Energia Amaldiçoada"
    }

    def __init__(self, parent, ficha: dict, on_save=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._ficha = ficha
        self._on_save = on_save
        self._construir()

    def _construir(self):
        for w in self.winfo_children():
            w.destroy()

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(5, 10))

        ctk.CTkLabel(header, text="Estilos de Luta",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")

        ctk.CTkButton(
            header, text="➕ Nova Habilidade", width=160, height=30,
            font=ctk.CTkFont(size=12), fg_color="#1a5c1a", hover_color="#145214",
            command=self._abrir_popup_criacao
        ).pack(side="right")

        habilidades = self._ficha.setdefault("habilidades_estilo_luta", [])

        if not habilidades:
            ctk.CTkLabel(self, text="Nenhuma habilidade de estilo criada. Clique em 'Nova Habilidade' para começar.",
                         font=ctk.CTkFont(size=13), text_color="gray").pack(pady=40)
            return

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        for hab in habilidades:
            self._criar_card(scroll, hab)

        self._aplicar_scroll(scroll)

    def _aplicar_scroll(self, scroll):
        def _scroll(delta):
            scroll._parent_canvas.yview_scroll(delta, "units")
        def _on_mousewheel(event):
            _scroll(-1 if event.delta > 0 else 1)
        def _on_button4(event): _scroll(-1)
        def _on_button5(event): _scroll(1)
        def _bind_scroll_recursivo(widget):
            widget.bind("<MouseWheel>", _on_mousewheel)
            widget.bind("<Button-4>", _on_button4)
            widget.bind("<Button-5>", _on_button5)
            for child in widget.winfo_children():
                _bind_scroll_recursivo(child)
        _bind_scroll_recursivo(scroll)
        scroll._parent_canvas.bind("<MouseWheel>", _on_mousewheel)
        scroll._parent_canvas.bind("<Button-4>", _on_button4)
        scroll._parent_canvas.bind("<Button-5>", _on_button5)
        scroll.focus_set()

    def _criar_card(self, parent, hab: dict):
        card = ctk.CTkFrame(parent, fg_color="#1e1e1e", corner_radius=8,
                            border_width=1, border_color="#333333")
        card.pack(fill="x", pady=4, padx=2)

        topo = ctk.CTkFrame(card, fg_color="transparent")
        topo.pack(fill="x", padx=12, pady=(10, 4))

        tipo_mec = hab.get("tipo_mecanica", "Ataque")
        ctk.CTkLabel(topo, text=hab.get("nome", "Sem nome"),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        ctk.CTkLabel(topo, text=f"[{tipo_mec}]", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="#3498db").pack(side="right")

        desc = hab.get("descricao", "")
        if desc:
            previa = (desc[:80] + "…") if len(desc) > 80 else desc
            ctk.CTkLabel(card, text=previa, wraplength=500, justify="left",
                         font=ctk.CTkFont(size=11), text_color="#aaaaaa").pack(anchor="w", padx=12, pady=(0, 4))

        params = hab.get("parametros", {})
        dano_base = params.get("dano_base", "")
        dano_estilo = params.get("dano_estilo", "")

        # REFORMULADO: Resumo de dano adaptado para as duas flags independentes de passos
        if tipo_mec != "Passiva" and (dano_base or dano_estilo):
            partes = []
            if dano_base:
                passo_b = " + Passo" if params.get("aplicar_passo_base", params.get("aplicar_passo", False)) else ""
                partes.append(f"Base: {dano_base}{passo_b}")
            if dano_estilo:
                passo_e = " + Passo" if params.get("aplicar_passo_estilo", False) else ""
                partes.append(f"Estilo: {dano_estilo}{passo_e}")
            ctk.CTkLabel(card, text="Dano: " + "  |  ".join(partes),
                         font=ctk.CTkFont(size=11), text_color="#e67e22").pack(anchor="w", padx=12, pady=(0, 4))

        # Tipos de dano
        tipos = hab.get("tipos_efeito", [])
        if tipos and tipo_mec != "Passiva":
            nomes_tipos = ", ".join(self.TIPO_EFEITO_NOMES.get(t, t) for t in tipos)
            ctk.CTkLabel(card, text=f"Tipo: {nomes_tipos}",
                         font=ctk.CTkFont(size=10), text_color="#888888").pack(anchor="w", padx=12, pady=(0, 4))

        efeitos = hab.get("efeitos", [])
        if efeitos and tipo_mec == "Passiva":
            ctk.CTkLabel(card, text=f"⚡ {len(efeitos)} efeito(s) passivo(s) ativo(s)",
                         font=ctk.CTkFont(size=10), text_color="#2ecc71").pack(anchor="w", padx=12, pady=(0, 4))

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkButton(btn_frame, text="Editar", width=70, height=28,
                      font=ctk.CTkFont(size=11), fg_color="transparent",
                      border_width=1, border_color="#444444",
                      command=lambda: self._abrir_popup_edicao(hab)).pack(side="left", padx=(0, 5))

        if tipo_mec != "Passiva":
            ctk.CTkButton(btn_frame, text="Usar", width=70, height=28,
                          font=ctk.CTkFont(size=11), fg_color="#2a6b2a", hover_color="#1a4a1a",
                          command=lambda: self._executar_habilidade(hab)).pack(side="left", padx=5)
        else:
            hab_id = hab["id"]
            passivas_ativas = self._ficha.setdefault("passivas_ativas", {})
            var_ativa = ctk.BooleanVar(value=hab_id in passivas_ativas)
            ctk.CTkCheckBox(btn_frame, text="Ativar", variable=var_ativa,
                            font=ctk.CTkFont(size=11),
                            command=lambda: self._toggle_passiva(hab_id, var_ativa)).pack(side="left", padx=5)

        ctk.CTkButton(btn_frame, text="Remover", width=70, height=28,
                      font=ctk.CTkFont(size=11), fg_color="#8B0000", hover_color="#5a0000",
                      command=lambda: self._remover_habilidade(hab)).pack(side="right")

    def _toggle_passiva(self, hab_id: str, var_ativa: ctk.BooleanVar):
        passivas = self._ficha.setdefault("passivas_ativas", {})
        if var_ativa.get():
            passivas[hab_id] = "BASE"
        else:
            passivas.pop(hab_id, None)
        if self._on_save:
            self._on_save()
        self._construir()

    # ── Popup de Criação / Edição ─────────────────────────────────────────────

    def _abrir_popup_criacao(self):
        self._abrir_popup_edicao(None)

    def _abrir_popup_edicao(self, hab: dict = None):
        editando = hab is not None
        titulo = "Editar Habilidade" if editando else "Nova Habilidade de Estilo"

        popup = ctk.CTkToplevel(self.winfo_toplevel())
        popup.title(titulo)
        popup.minsize(500, 500)
        popup.resizable(True, True)
        popup.after(10, lambda: popup.geometry(
            f"{min(700, popup.winfo_screenwidth()-100)}x{min(800, popup.winfo_screenheight()-100)}"
        ))

        scroll = ctk.CTkScrollableFrame(popup, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(20, 10))

        main = ctk.CTkFrame(scroll, fg_color="transparent")
        main.pack(fill="both", expand=True)

        ctk.CTkLabel(main, text=titulo,
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 15))

        # Nome
        ctk.CTkLabel(main, text="Nome:", anchor="w").pack(fill="x")
        e_nome = ctk.CTkEntry(main)
        if editando:
            e_nome.insert(0, hab.get("nome", ""))
        e_nome.pack(fill="x", pady=(2, 12))

        # Tipo Mecânica
        ctk.CTkLabel(main, text="Tipo Mecânica:", anchor="w").pack(fill="x")
        tipo_mec_var = ctk.StringVar(value=hab.get("tipo_mecanica", "Ataque") if editando else "Ataque")
        ctk.CTkOptionMenu(main, values=self.TIPO_MECANICA_OPCOES,
                          variable=tipo_mec_var).pack(fill="x", pady=(2, 12))

        # ── REFORMULADO: Containers Dinâmicos de Exibição ─────────────────────
        frame_mecanica_ativa = ctk.CTkFrame(main, fg_color="transparent")
        frame_descricao = ctk.CTkFrame(main, fg_color="transparent")
        frame_mecanica_passiva = ctk.CTkFrame(main, fg_color="transparent")

        # ── CONTEÚDO: MENSURAÇÃO DE ATAQUE / TR (Frame Ativa) ─────────────────
        # Dano base
        ctk.CTkLabel(frame_mecanica_ativa, text="Dano Base (ex: soco, arma):", anchor="w").pack(fill="x")
        e_dano_base = ctk.CTkEntry(frame_mecanica_ativa, placeholder_text="ex: 1d6+FOR, 2d8+AGI")
        if editando:
            e_dano_base.insert(0, hab.get("parametros", {}).get("dano_base", ""))
        e_dano_base.pack(fill="x", pady=(2, 6))

        # Checkbox Passo 1 (Dano Base)
        aplicar_passo_base_var = ctk.BooleanVar(
            value=hab.get("parametros", {}).get("aplicar_passo_base", hab.get("parametros", {}).get("aplicar_passo", False)) if editando else False
        )
        ctk.CTkCheckBox(frame_mecanica_ativa, text="Aplicar bônus de Passo no dano base",
                        variable=aplicar_passo_base_var).pack(anchor="w", pady=(0, 12))

        # Dano do estilo
        ctk.CTkLabel(frame_mecanica_ativa, text="Dano do Estilo de Luta (adicional):", anchor="w").pack(fill="x")
        e_dano_estilo = ctk.CTkEntry(frame_mecanica_ativa, placeholder_text="ex: 1d6, 2d10+FOR")
        if editando:
            e_dano_estilo.insert(0, hab.get("parametros", {}).get("dano_estilo", ""))
        e_dano_estilo.pack(fill="x", pady=(2, 6))

        # Checkbox Passo 2 (Dano Estilo) - NOVO!
        aplicar_passo_estilo_var = ctk.BooleanVar(
            value=hab.get("parametros", {}).get("aplicar_passo_estilo", False) if editando else False
        )
        ctk.CTkCheckBox(frame_mecanica_ativa, text="Aplicar bônus de Passo no dano do estilo",
                        variable=aplicar_passo_estilo_var).pack(anchor="w", pady=(0, 12))

        # Tipos de dano
        ctk.CTkLabel(frame_mecanica_ativa, text="Tipos de Dano (pode combinar):", anchor="w").pack(fill="x")
        tipos_vars = {}
        tipos_frame = ctk.CTkFrame(frame_mecanica_ativa, fg_color="transparent")
        tipos_frame.pack(fill="x", pady=(2, 12))

        tipos_selecionados = hab.get("tipos_efeito", ["corpo"]) if editando else ["corpo"]
        for chave, nome in self.TIPO_EFEITO_NOMES.items():
            var = ctk.BooleanVar(value=chave in tipos_selecionados)
            ctk.CTkCheckBox(tipos_frame, text=nome, variable=var).pack(anchor="w", pady=1)
            tipos_vars[chave] = var

        # ── CONTEÚDO: COMPARTILHADO (Sempre visível) ──────────────────────────
        ctk.CTkLabel(frame_descricao, text="Descrição / Efeito:", anchor="w").pack(fill="x")
        e_desc = ctk.CTkTextbox(frame_descricao, height=100)
        if editando:
            e_desc.insert("1.0", hab.get("descricao", ""))
        e_desc.pack(fill="x", pady=(2, 0))

        # ── CONTEÚDO: MODIFICADORES DE FICHA (Frame Passiva) ──────────────────
        efeitos_temp = list(hab.get("efeitos", [])) if editando else []
        efeitos_frame = EfeitosEditorFrame(
            frame_mecanica_passiva,
            efeitos_iniciais=efeitos_temp,
            on_change=lambda novos: efeitos_temp.clear() or efeitos_temp.extend(novos)
        )
        efeitos_frame.pack(fill="both", expand=True)

        # LÓGICA DE ALTERNÂNCIA DINÂMICA DE VISIBILIDADE
        def alternar_visibilidade(*args):
            frame_mecanica_ativa.pack_forget()
            frame_descricao.pack_forget()
            frame_mecanica_passiva.pack_forget()

            mec = tipo_mec_var.get()
            if mec == "Passiva":
                frame_descricao.pack(fill="x", pady=(0, 12))
                frame_mecanica_passiva.pack(fill="both", expand=True, pady=(10, 5))
            else:
                frame_mecanica_ativa.pack(fill="x", pady=(0, 12))
                frame_descricao.pack(fill="x", pady=(0, 12))

        tipo_mec_var.trace_add("write", alternar_visibilidade)
        alternar_visibilidade()  # Inicializa o estado visual

        # Botões do popup
        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))

        def salvar():
            nome = e_nome.get().strip()
            if not nome:
                messagebox.showwarning("Aviso", "O nome da habilidade é obrigatório.")
                return

            mec = tipo_mec_var.get()

            # Normaliza dados baseado no tipo mecânico escolhido para evitar lixo no JSON
            if mec == "Passiva":
                tipos_efeito = ["estilo_luta"]
                dano_base_str = ""
                dano_estilo_str = ""
                p_base = False
                p_estilo = False
                efeitos_finais = efeitos_temp
            else:
                tipos_efeito = [chave for chave, var in tipos_vars.items() if var.get()]
                if not tipos_efeito:
                    tipos_efeito = ["corpo"]
                dano_base_str = e_dano_base.get().strip()
                dano_estilo_str = e_dano_estilo.get().strip()
                p_base = aplicar_passo_base_var.get()
                p_estilo = aplicar_passo_estilo_var.get()
                efeitos_finais = []  # Esvazia a passiva se virar habilidade ativa

            nova_hab = {
                "id": hab.get("id") if editando else str(uuid.uuid4()),
                "nome": nome,
                "tipo_mecanica": mec,
                "descricao": e_desc.get("1.0", "end-1c").strip(),
                "tipos_efeito": tipos_efeito,
                "parametros": {
                    "dano_base":            dano_base_str,
                    "dano_estilo":          dano_estilo_str,
                    "aplicar_passo_base":   p_base,
                    "aplicar_passo_estilo": p_estilo,
                },
                "efeitos": efeitos_finais
            }

            habilidades = self._ficha.setdefault("habilidades_estilo_luta", [])
            if editando:
                for i, h in enumerate(habilidades):
                    if h.get("id") == hab.get("id"):
                        habilidades[i] = nova_hab
                        break
            else:
                habilidades.append(nova_hab)

            if self._on_save:
                self._on_save()
            popup.destroy()
            self._construir()

        ctk.CTkButton(btn_frame, text="Salvar", fg_color="#1a6b1a", hover_color="#145214",
                      command=salvar).pack(side="right", padx=(5, 0))
        ctk.CTkButton(btn_frame, text="Cancelar", fg_color="transparent", border_width=1,
                      command=popup.destroy).pack(side="right")

    # ── Execução ──────────────────────────────────────────────────────────────

    def _executar_habilidade(self, hab: dict):
        resultado = executar_estilo_luta(hab, self._ficha)
        self._mostrar_resultado(resultado)

    def _mostrar_resultado(self, resultado: dict):
        popup = ctk.CTkToplevel(self.winfo_toplevel())
        popup.title("Resultado")
        popup.geometry("450x350")
        popup.after(100, popup.grab_set)

        main = ctk.CTkFrame(popup, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=20)

        dano = resultado.get("detalhes", {}).get("dano", 0)
        texto = resultado.get("mensagem", "")

        if dano and dano > 9999:
            texto = texto.replace(str(dano), formatar_numero_grande(dano))
            mostrar_botao_exato = True
        else:
            mostrar_botao_exato = False

        ctk.CTkLabel(main, text=texto, wraplength=400, justify="left",
                     font=ctk.CTkFont(size=13)).pack(anchor="w", pady=(0, 20))

        if mostrar_botao_exato:
            ctk.CTkButton(main, text="Ver valor exato",
                          command=lambda: messagebox.showinfo("Valor exato", f"{dano:,}".replace(',', '.')),
                          fg_color="transparent", border_width=1).pack(pady=(0, 10))

        ctk.CTkButton(main, text="Fechar", command=popup.destroy).pack()

    # ── Remoção ───────────────────────────────────────────────────────────────

    def _remover_habilidade(self, hab: dict):
        if not messagebox.askyesno("Confirmar", f"Remover '{hab.get('nome', 'esta habilidade')}'?"):
            return

        self._ficha["habilidades_estilo_luta"] = [
            h for h in self._ficha.get("habilidades_estilo_luta", [])
            if h.get("id") != hab.get("id")
        ]

        passivas = self._ficha.get("passivas_ativas", {})
        passivas.pop(hab["id"], None)

        if self._on_save:
            self._on_save()
        self._construir()

    def atualizar(self):
        self._construir()