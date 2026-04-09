from datetime import datetime

import customtkinter as ctk
import json
import os

class PainelFeiticos(ctk.CTkFrame):
    """Aba: feitiços escolhidos (padrão + custom)."""

    CAMINHO_FEITICOS = "data/feiticos.json"
    CAMINHO_CUSTOM   = "data/feiticos_custom.json"

    def __init__(self, parent, ficha: dict, on_passiva_change=None, on_save=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._ficha = ficha
        self._cache_abas = {}          # guarda os scrolls de cada aba já criados
        self._container_ativo = None   # referência ao container principal do popup
        self._on_passiva_change = on_passiva_change
        self._on_save = on_save
        self._db = self._carregar_db()
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

        # ══════════════════════════════════════════════════════════════════════
        # Cabeçalho com pontos e botão Adicionar
        # ══════════════════════════════════════════════════════════════════════
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(5, 10))

        pontos_disponiveis = self._ficha.get("totais_nex", {}).get("feiticos", 0)
        qtd_atual = len(self._ficha.get("feiticos", [])) + len(self._ficha.get("feiticos_custom", []))

        self._lbl_pontos_feiticos = ctk.CTkLabel(
            header, text=f"Feitiços: {qtd_atual} / {pontos_disponiveis}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#f1c40f" if qtd_atual < pontos_disponiveis else "#e74c3c"
        )
        self._lbl_pontos_feiticos.pack(side="left")

        btn_adicionar = ctk.CTkButton(
            header, text="+ Adicionar Feitiço", width=150, height=30,
            font=ctk.CTkFont(size=12), fg_color="#1a5c1a", hover_color="#145214",
            command=self._abrir_popup_selecao_feiticos
        )
        btn_adicionar.pack(side="right")

        # Lista de feitiços atuais
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
            
        # ══════════════════════════════════════════════════════════════════════
        # Habilita scroll com roda do mouse (compatível Windows/Linux)
        # ══════════════════════════════════════════════════════════════════════
        def _scroll(delta):
            """Movimenta a rolagem verticalmente."""
            scroll._parent_canvas.yview_scroll(delta, "units")

        def _bind_scroll_recursivo(widget):
            """Aplica os binds de scroll ao widget e a todos os seus filhos."""
            # Windows/Mac
            widget.bind("<MouseWheel>", lambda e: _scroll(-1 if e.delta > 0 else 1))
            # Linux
            widget.bind("<Button-4>", lambda e: _scroll(-1))
            widget.bind("<Button-5>", lambda e: _scroll(1))
            for child in widget.winfo_children():
                _bind_scroll_recursivo(child)

        # Aplica binds recursivamente a partir do scroll
        _bind_scroll_recursivo(scroll)

        # Garante também no canvas interno (redundante, mas seguro)
        scroll._parent_canvas.bind("<MouseWheel>", lambda e: _scroll(-1 if e.delta > 0 else 1))
        scroll._parent_canvas.bind("<Button-4>", lambda e: _scroll(-1))
        scroll._parent_canvas.bind("<Button-5>", lambda e: _scroll(1))

        # Força foco (útil no Linux)
        scroll.focus_set()

    def _abrir_criador_customizado(self, popup_pai=None):
        """Abre janela para criar um novo feitiço customizado."""
        popup = ctk.CTkToplevel(self.winfo_toplevel())
        popup.title("Criar Feitiço Customizado")
        popup.geometry("550x650")
        popup.minsize(500, 600)
        popup.after(100, popup.grab_set)

        main = ctk.CTkScrollableFrame(popup, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(main, text="Novo Feitiço Customizado",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0,10))

        # Nome
        ctk.CTkLabel(main, text="Nome:", anchor="w").pack(fill="x")
        e_nome = ctk.CTkEntry(main, placeholder_text="Ex: Bola de Fogo")
        e_nome.pack(fill="x", pady=(2,10))

        # Tipo (Passiva/Ativa)
        ctk.CTkLabel(main, text="Tipo:", anchor="w").pack(fill="x")
        tipo_var = ctk.StringVar(value="Ativa")
        frame_tipo = ctk.CTkFrame(main, fg_color="transparent")
        frame_tipo.pack(fill="x", pady=(2,10))
        ctk.CTkRadioButton(frame_tipo, text="Passiva", variable=tipo_var, value="Passiva").pack(side="left", padx=10)
        ctk.CTkRadioButton(frame_tipo, text="Ativa", variable=tipo_var, value="Ativa").pack(side="left", padx=10)

        # Grau Base
        ctk.CTkLabel(main, text="Grau Base:", anchor="w").pack(fill="x")
        grau_var = ctk.StringVar(value="4")
        grau_menu = ctk.CTkOptionMenu(main, values=["4", "3", "2", "1", "Semi Especial", "Especial", "Ultra Especial"],
                                      variable=grau_var)
        grau_menu.pack(fill="x", pady=(2,10))

        # Descrição Base
        ctk.CTkLabel(main, text="Descrição (versão base):", anchor="w").pack(fill="x")
        e_desc_base = ctk.CTkTextbox(main, height=80)
        e_desc_base.pack(fill="x", pady=(2,10))

        # Versões melhoradas (opcional)
        ctk.CTkLabel(main, text="Versões melhoradas (opcional):", anchor="w",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(10,5))

        frame_versoes = ctk.CTkFrame(main, fg_color="transparent")
        frame_versoes.pack(fill="x", pady=(0,10))

        versoes_adicionadas = []  # lista de (grau, descricao)

        def adicionar_versao():
            win = ctk.CTkToplevel(popup)
            win.title("Nova Versão")
            win.geometry("400x300")
            win.grab_set()

            ctk.CTkLabel(win, text="Grau:").pack(pady=(10,2))
            grau_ver = ctk.StringVar(value="3")
            menu_ver = ctk.CTkOptionMenu(win, values=["3", "2", "1", "Semi Especial", "Especial", "Ultra Especial"],
                                         variable=grau_ver)
            menu_ver.pack()

            ctk.CTkLabel(win, text="Descrição:").pack(pady=(10,2))
            txt_ver = ctk.CTkTextbox(win, height=100)
            txt_ver.pack(fill="both", expand=True, padx=10)

            def salvar_versao():
                grau = grau_ver.get()
                desc = txt_ver.get("1.0", "end-1c").strip()
                if desc:
                    versoes_adicionadas.append((grau, desc))
                    atualizar_lista_versoes()
                win.destroy()

            ctk.CTkButton(win, text="Salvar", command=salvar_versao).pack(pady=10)

        def atualizar_lista_versoes():
            for w in frame_versoes.winfo_children():
                w.destroy()
            for grau, desc in versoes_adicionadas:
                linha = ctk.CTkFrame(frame_versoes, fg_color="#1e1e1e", corner_radius=6)
                linha.pack(fill="x", pady=2)
                ctk.CTkLabel(linha, text=f"{grau}:", width=80, font=ctk.CTkFont(size=12, weight="bold"),
                             text_color="#f1c40f").pack(side="left", padx=5)
                ctk.CTkLabel(linha, text=desc[:50]+"…" if len(desc)>50 else desc,
                             font=ctk.CTkFont(size=11), text_color="#cccccc").pack(side="left", padx=5)

        btn_add_versao = ctk.CTkButton(main, text="+ Adicionar Versão", width=150,
                                       command=adicionar_versao)
        btn_add_versao.pack(anchor="w", pady=(0,10))

        # Scaling (fórmulas) – simplificado por enquanto
        ctk.CTkLabel(main, text="Efeitos (scaling) – em breve",
                     font=ctk.CTkFont(size=12, slant="italic"), text_color="#888888").pack(anchor="w")

        # Botão Salvar
        def salvar_customizado():
            nome = e_nome.get().strip()
            if not nome:
                return
            # Gera ID único
            import uuid
            novo_id = f"custom_{uuid.uuid4().hex[:6]}"

            novo_feitico = {
                "id": novo_id,
                "nome": nome,
                "tipo": tipo_var.get(),
                "classe": "Customizado",
                "grau_base": grau_var.get(),
                "descricao_base": e_desc_base.get("1.0", "end-1c").strip(),
                "versoes": {grau: desc for grau, desc in versoes_adicionadas},
                "efeitos_por_versao": {}  # placeholder para futuro
            }

            # Salva no arquivo custom
            self._salvar_feitico_customizado(novo_feitico)
            # Adiciona à ficha
            self._ficha.setdefault("feiticos_custom", []).append(novo_id)
            self._db[novo_id] = novo_feitico  # atualiza cache
            if self._on_save:
                self._on_save()
            self._construir()
            popup.destroy()
            if popup_pai:
                popup_pai.destroy()

        ctk.CTkButton(main, text="Salvar Feitiço", fg_color="#1a6b1a", hover_color="#145214",
                      command=salvar_customizado).pack(fill="x", pady=(20,5))
        ctk.CTkButton(main, text="Cancelar", fg_color="transparent", border_width=1,
                      command=popup.destroy).pack(fill="x")
        
    def _salvar_feitico_customizado(self, feitico: dict):
        caminho = os.path.join(os.path.dirname(__file__), "data", "feiticos_custom.json")
        if os.path.exists(caminho):
            with open(caminho, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []
        data.append(feitico)
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def _tornar_clicavel(self, widget, callback):
        """Faz com que o widget e todos os seus filhos chamem o callback ao serem clicados."""
        widget.bind("<Button-1>", lambda e: callback())
        for child in widget.winfo_children():
            self._tornar_clicavel(child, callback)

    def _card_completo(self, parent, f: dict):
        card = ctk.CTkFrame(
            parent,
            fg_color="#1e1e1e",
            corner_radius=8,
            border_width=1,
            border_color="#333333"
        )
        card.pack(fill="x", pady=4)

        # Torna o card clicável para detalhes
        self._tornar_clicavel(card, lambda: self._mostrar_detalhes(f))

        topo = ctk.CTkFrame(card, fg_color="transparent")
        topo.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(topo, text=f.get("nome", f.get("id", "?")),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")

        classe = f.get("classe", "")
        if classe:
            ctk.CTkLabel(topo, text=classe,
                         font=ctk.CTkFont(size=11),
                         text_color="#666666").pack(side="right")

        desc = f.get("descricao_base") or f.get("descricao", "")
        if desc:
            previa = (desc[:60] + "…") if len(desc) > 60 else desc
            ctk.CTkLabel(card, text=previa, wraplength=500, justify="left",
                         font=ctk.CTkFont(size=12),
                         text_color="#aaaaaa").pack(anchor="w", padx=12, pady=(0, 10))

        # Frame de ações (remover + controles de passiva)
        acoes_frame = ctk.CTkFrame(card, fg_color="transparent")
        acoes_frame.pack(fill="x", padx=12, pady=(0, 8))

        # Botão Remover (alinhado à direita)
        btn_remover = ctk.CTkButton(
            acoes_frame,
            text="✕ Remover",
            width=90,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#8B0000",
            hover_color="#5a0000",
            command=lambda: self._remover_feitico(f["id"])
        )
        btn_remover.pack(side="right", padx=(0, 5))

        # Controles de passiva (se aplicável)
        if f.get("tipo") == "Passiva" and "efeitos_por_versao" in f:
            versoes = list(f["efeitos_por_versao"].keys())
            self._criar_controles_passiva(acoes_frame, f["id"], versoes)

    def _card_simples(self, parent, fid: str):
        card = ctk.CTkFrame(
            parent,
            fg_color="#1a1a1a",
            corner_radius=6,
            border_width=1,
            border_color="#2a2a2a"
        )
        card.pack(fill="x", pady=2)
        self._tornar_clicavel(card, lambda: self._mostrar_detalhes({"id": fid, "nome": fid}))

        ctk.CTkLabel(card, text=fid, font=ctk.CTkFont(size=12),
                     text_color="#666666").pack(anchor="w", padx=12, pady=6)
        
    def _mostrar_detalhes(self, feitico: dict):
        popup = ctk.CTkToplevel(self.winfo_toplevel())
        popup.title(feitico.get("nome", feitico.get("id", "Feitiço")))
        popup.geometry("550x500")
        popup.minsize(450, 400)
        popup.after(100, popup.grab_set)

        # Scroll para caso o conteúdo seja grande
        scroll = ctk.CTkScrollableFrame(popup, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # Título e tipo
        header = ctk.CTkFrame(scroll, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))

        nome = feitico.get("nome", feitico.get("id", "???"))
        ctk.CTkLabel(header, text=nome,
                     font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w")

        tipo = feitico.get("tipo", "—")
        cor_tipo = "#2ecc71" if tipo.lower() == "passiva" else "#e67e22"
        ctk.CTkLabel(header, text=f"Tipo: {tipo}",
                     font=ctk.CTkFont(size=13),
                     text_color=cor_tipo).pack(anchor="w", pady=(4, 0))

        # Classe (se houver)
        classe = feitico.get("classe", "")
        if classe:
            ctk.CTkLabel(scroll, text=f"Classe: {classe}",
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="#888888").pack(anchor="w", pady=(0, 8))

        # Descrição base
        desc_base = feitico.get("descricao_base") or feitico.get("descricao", "")
        if desc_base:
            frame_desc = ctk.CTkFrame(scroll, fg_color="#1e1e1e", corner_radius=8)
            frame_desc.pack(fill="x", pady=(0, 12))
            ctk.CTkLabel(frame_desc, text="📜 Descrição",
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color="#cccccc").pack(anchor="w", padx=12, pady=(10, 4))
            ctk.CTkLabel(frame_desc, text=desc_base, wraplength=480, justify="left",
                         font=ctk.CTkFont(size=12),
                         text_color="#bbbbbb").pack(anchor="w", padx=12, pady=(0, 10))

        # Versões (upgrades)
        versoes = feitico.get("versoes", {})
        if versoes:
            ctk.CTkLabel(scroll, text="⬆️ Versões melhoradas",
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color="#aaaaaa").pack(anchor="w", pady=(0, 6))

            for grau, texto in versoes.items():
                frame_ver = ctk.CTkFrame(scroll, fg_color="#1a1a1a", corner_radius=6)
                frame_ver.pack(fill="x", pady=2)
                ctk.CTkLabel(frame_ver, text=f"{grau}:", width=80,
                             font=ctk.CTkFont(size=12, weight="bold"),
                             text_color="#f1c40f").pack(side="left", padx=10, pady=8)
                ctk.CTkLabel(frame_ver, text=texto, wraplength=380, justify="left",
                             font=ctk.CTkFont(size=12),
                             text_color="#cccccc").pack(side="left", padx=(0, 10), pady=8)

        # Espaço reservado para efeitos futuros (não implementado ainda)
        if "efeitos_por_versao" in feitico:
            ctk.CTkLabel(scroll, text="⚙️ Efeitos mecânicos (em breve)",
                         font=ctk.CTkFont(size=12, slant="italic"),
                         text_color="#555555").pack(anchor="w", pady=(12, 0))

        # Botão fechar
        ctk.CTkButton(popup, text="Fechar", width=100,
                      command=popup.destroy).pack(pady=(0, 10))
        
    def _criar_controles_passiva(self, parent, feitico_id: str, versoes_disponiveis: list):
        """Cria checkbox e dropdown para ativar/versionar uma passiva."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=12, pady=(0, 8))

        # Estado atual
        passivas_ativas = self._ficha.get("passivas_ativas", {})
        ativa = feitico_id in passivas_ativas
        versao_atual = passivas_ativas.get(feitico_id, "BASE")

        var_ativa = ctk.BooleanVar(value=ativa)
        var_versao = ctk.StringVar(value=versao_atual)

        cb = ctk.CTkCheckBox(frame, text="Ativar", variable=var_ativa,
                             font=ctk.CTkFont(size=12),
                             command=lambda: self._toggle_passiva(feitico_id, var_ativa, var_versao, dropdown))
        cb.pack(side="left", padx=(0, 10))

        dropdown = ctk.CTkOptionMenu(frame, values=versoes_disponiveis, variable=var_versao,
                                    width=100, height=28, font=ctk.CTkFont(size=12),
                                    command=lambda val: self._mudar_versao_passiva(feitico_id, val))
        dropdown.pack(side="left")
        if not ativa:
            dropdown.configure(state="disabled")

        return cb, dropdown

    def _toggle_passiva(self, fid, var_ativa, var_versao, dropdown):
        ativa = var_ativa.get()
        passivas = self._ficha.setdefault("passivas_ativas", {})
        if ativa:
            passivas[fid] = var_versao.get()
            dropdown.configure(state="normal")
        else:
            passivas.pop(fid, None)
            dropdown.configure(state="disabled")
        self._aplicar_passivas()

    def _mudar_versao_passiva(self, fid, nova_versao):
        if fid in self._ficha.get("passivas_ativas", {}):
            self._ficha["passivas_ativas"][fid] = nova_versao
            self._aplicar_passivas()

    def _aplicar_passivas(self):
        """Dispara o recálculo na janela principal."""
        if self._on_passiva_change and self.winfo_exists():
            self.after(200, self._on_passiva_change)

    def _abrir_popup_selecao_feiticos(self):
        """Abre um popup com abas para escolher feitiços existentes ou criar customizado."""
        pontos_total = self._ficha.get("totais_nex", {}).get("feiticos", 0)
        qtd_atual = len(self._ficha.get("feiticos", [])) + len(self._ficha.get("feiticos_custom", []))
        disponiveis = pontos_total - qtd_atual

        popup = ctk.CTkToplevel(self.winfo_toplevel())
        self._popup_selecao = popup 
        popup.title("Adicionar Feitiço")
        popup.geometry("700x600")
        popup.minsize(600, 500)
        popup.after(100, popup.grab_set)
        popup.focus_force() 

        main = ctk.CTkFrame(popup, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # Cabeçalho com pontos
        header = ctk.CTkFrame(main, fg_color="transparent")
        header.pack(fill="x", pady=(0,10))

        ctk.CTkLabel(header, text="Selecione um feitiço para adicionar",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")

        ctk.CTkLabel(header, text=f"Pontos disponíveis: {disponiveis}",
                     font=ctk.CTkFont(size=13),
                     text_color="#f1c40f" if disponiveis > 0 else "#e74c3c").pack(side="right")

        # Abas (classes)
        classe_personagem = self._ficha.get("classe", "Geral")
        abas = self._listar_abas_feiticos(classe_personagem)

        tab_frame = ctk.CTkFrame(main, fg_color="transparent")
        tab_frame.pack(fill="x", pady=(0,5))

        self._tab_buttons = {}
        self._aba_ativa = abas[0] if abas else None
        for aba in abas:
            btn = ctk.CTkButton(
                tab_frame, text=aba, width=80, height=28,
                font=ctk.CTkFont(size=12),
                command=lambda a=aba: self._trocar_aba_selecao(a, container, disponiveis)
            )
            btn.pack(side="left", padx=2)
            self._tab_buttons[aba] = btn

        # Container da lista
        container = ctk.CTkFrame(main, fg_color="transparent")
        container.pack(fill="both", expand=True)

        # Inicializa cache para este popup
        self._cache_abas = {}

        # Botão Criar Customizado
        btn_custom = ctk.CTkButton(
            main, text="✨ Criar Feitiço Customizado", height=35,
            font=ctk.CTkFont(size=13), fg_color="#6a1b9a", hover_color="#4a1070",
            command=lambda: self._abrir_criador_customizado(popup)
        )
        btn_custom.pack(fill="x", pady=(10,5))

        if self._aba_ativa:
            self._trocar_aba_selecao(self._aba_ativa, container, disponiveis)
        
        def fechar_popup():
            self._cache_abas.clear()
            if self._popup_selecao:
                self._popup_selecao.destroy()
                self._popup_selecao = None
        
        ctk.CTkButton(main, text="Fechar", fg_color="transparent", border_width=1,
                      command=fechar_popup).pack(fill="x")

    def _listar_abas_feiticos(self, classe_personagem: str) -> list:
        """Retorna as abas disponíveis: Geral, classe do personagem, e outras."""
        abas = ["Geral", classe_personagem]
        # Adiciona outras classes que aparecem nos feitiços
        for feitico in self._db.values():
            classe = feitico.get("classe", "")
            if classe and classe not in abas:
                abas.append(classe)
        return abas

    def _trocar_aba_selecao(self, aba: str, container: ctk.CTkFrame, disponiveis: int):
        # Destaca botão ativo
        for nome, btn in self._tab_buttons.items():
            if nome == aba:
                btn.configure(fg_color="#1a6b1a", hover_color="#145214")
            else:
                btn.configure(fg_color="#2a2a2a", hover_color="#3a3a3a")

        # Oculta todos os containers cacheados
        for scroll in list(self._cache_abas.values()):
            if scroll and scroll.winfo_exists():
                scroll.pack_forget()

        # Se já existe cache para esta aba e o widget ainda é válido, apenas exibe
        if aba in self._cache_abas:
            scroll = self._cache_abas[aba]
            if scroll and scroll.winfo_exists():
                scroll.pack(fill="both", expand=True)
                self._aplicar_binds_scroll(scroll)
                scroll.focus_set()
                return
            else:
                # Widget inválido, remove do cache
                del self._cache_abas[aba]

        # Caso contrário, cria o conteúdo da aba
        for w in container.winfo_children():
            w.destroy()

        feiticos_aba = [f for f in self._db.values() if f.get("classe", "Geral") == aba]

        if not feiticos_aba:
            lbl = ctk.CTkLabel(container, text="Nenhum feitiço disponível nesta aba.",
                               font=ctk.CTkFont(size=13), text_color="gray")
            lbl.pack(pady=40)
            self._cache_abas[aba] = lbl
            return

        scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        self._aplicar_binds_scroll(scroll)
        scroll.focus_set()

        ids_atuais = self._ficha.get("feiticos", []) + self._ficha.get("feiticos_custom", [])
        for feitico in feiticos_aba:
            self._card_selecao_feitico(scroll, feitico, disponiveis, ids_atuais)

        self._aplicar_binds_scroll(scroll)

        # Armazena no cache
        self._cache_abas[aba] = scroll
        

    def _aplicar_binds_scroll(self, scroll):
        def _scroll(delta):
            scroll._parent_canvas.yview_scroll(delta, "units")
        def _bind_recursivo(widget):
            widget.bind("<MouseWheel>", lambda e: _scroll(-1 if e.delta > 0 else 1))
            widget.bind("<Button-4>", lambda e: _scroll(-1))
            widget.bind("<Button-5>", lambda e: _scroll(1))
            for child in widget.winfo_children():
                _bind_recursivo(child)
        _bind_recursivo(scroll)
        scroll._parent_canvas.bind("<MouseWheel>", lambda e: _scroll(-1 if e.delta > 0 else 1))
        scroll._parent_canvas.bind("<Button-4>", lambda e: _scroll(-1))
        scroll._parent_canvas.bind("<Button-5>", lambda e: _scroll(1))

    def _card_selecao_feitico(self, parent, feitico: dict, disponiveis: int, ids_atuais: list):
        """Card para exibir feitiço no popup de seleção."""
        ja_tem = feitico["id"] in ids_atuais
        pode_adicionar = disponiveis > 0 and not ja_tem

        if ja_tem:
            cor_borda = "#FFD700"
            cor_bg = "#3a3000"
        elif pode_adicionar:
            cor_borda = "#2ecc71"
            cor_bg = "#1a2b1a"
        else:
            cor_borda = "#555555"
            cor_bg = "#2b2b2b"

        card = ctk.CTkFrame(parent, corner_radius=8, border_width=2,
                            border_color=cor_borda, fg_color=cor_bg)
        card.pack(fill="x", padx=5, pady=4)

        topo = ctk.CTkFrame(card, fg_color="transparent")
        topo.pack(fill="x", padx=12, pady=(10,4))

        ctk.CTkLabel(topo, text=feitico.get("nome", feitico["id"]),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")

        grau = feitico.get("grau_base", "?")
        ctk.CTkLabel(topo, text=f"Grau {grau}",
                     font=ctk.CTkFont(size=11), text_color="#aaaaaa").pack(side="left", padx=8)

        if ja_tem:
            ctk.CTkLabel(topo, text="✓ Já possui",
                         text_color="#FFD700", font=ctk.CTkFont(size=12)).pack(side="right")

        desc = feitico.get("descricao_base", feitico.get("descricao", ""))
        if desc:
            previa = (desc[:80] + "…") if len(desc) > 80 else desc
            ctk.CTkLabel(card, text=previa, wraplength=550, justify="left",
                         font=ctk.CTkFont(size=11),
                         text_color="#cccccc").pack(anchor="w", padx=12, pady=(0,8))

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=(0,10))

        ctk.CTkButton(btn_frame, text="Ver detalhes", width=100, height=28,
                      font=ctk.CTkFont(size=11), fg_color="transparent", border_width=1,
                      command=lambda f=feitico: self._mostrar_detalhes(f)).pack(side="left")

        if pode_adicionar:
            ctk.CTkButton(btn_frame, text="Adicionar", width=100, height=28,
                          font=ctk.CTkFont(size=11), fg_color="#1a6b1a", hover_color="#145214",
                                command=lambda f=feitico: self._adicionar_feitico_existente(f, popup=self._popup_selecao)
                         ).pack(side="left", padx=8)
            
    def _adicionar_feitico_existente(self, feitico: dict, popup=None):
        pontos_total = self._ficha.get("totais_nex", {}).get("feiticos", 0)
        qtd_atual = len(self._ficha.get("feiticos", [])) + len(self._ficha.get("feiticos_custom", []))
        if qtd_atual >= pontos_total:
            return

        self._ficha.setdefault("feiticos", []).append(feitico["id"])
        self._salvar_ficha()

        # Fecha o popup imediatamente
        if popup:
            popup.destroy()
            if popup == getattr(self, '_popup_selecao', None):
                self._popup_selecao = None

        # Agenda a reconstrução e recálculo para depois que tudo estiver estável
        def reconstruir_e_recalcular():
            if not self.winfo_exists():
                return
            print("Reconstruindo painel de feitiços...")
            self._db = self._carregar_db()
            self._construir()
            if self._on_passiva_change:
                print("Agendando recálculo...")
                self.after(100, self._on_passiva_change)

        # Usa after_idle para executar quando não houver mais eventos pendentes
        self.after_idle(reconstruir_e_recalcular)
        

    def _remover_feitico(self, fid: str):
        if fid in self._ficha.get("feiticos", []):
            self._ficha["feiticos"].remove(fid)
        elif fid in self._ficha.get("feiticos_custom", []):
            self._ficha["feiticos_custom"].remove(fid)
        else:
            return

        passivas = self._ficha.get("passivas_ativas", {})
        if fid in passivas:
            del passivas[fid]

        self._salvar_ficha()

        def reconstruir_e_recalcular():
            if not self.winfo_exists():
                return
            self._db = self._carregar_db()
            self._construir()
            if self._on_passiva_change:
                self.after(100, self._on_passiva_change)

        self.after_idle(reconstruir_e_recalcular)

    def _salvar_ficha(self):
        """Dispara o salvamento via callback da janela principal."""
        # Acessa o método de salvamento da FichaPersonagem
        top = self.winfo_toplevel()
        if hasattr(top, '_ficha_personagem'):
            top._ficha_personagem._salvar()
        # Alternativa: chamar um callback passado no construtor
        if hasattr(self, '_on_save') and self._on_save:
            self._on_save()

    def atualizar(self):
        self._db = self._carregar_db()
        self._construir()

