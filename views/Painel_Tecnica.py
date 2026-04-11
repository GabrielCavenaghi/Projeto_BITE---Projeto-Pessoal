import customtkinter as ctk
import uuid
from tkinter import messagebox
from views.Efeitos_Popup import EfeitosPopup

class PainelTecnica(ctk.CTkFrame):
    """Aba: gerenciamento de habilidades de técnica customizadas."""

    NIVEL_OPCOES = ["0", "1", "2", "3", "4", "5", "6"]
    CONJURACAO_OPCOES = ["Turno", "Completa", "Padrão", "Movimento", "Livre", "Reação"]
    ALCANCE_OPCOES = ["Pessoal", "Toque", "Curto", "Médio", "Longo", "Extremo", "Ilimitado"]
    DURACAO_OPCOES = ["Instantânea", "1 rodada", "Cena", "Dia", "Semana", "Permanente", "Outro"]
    TIPO_MECANICA_OPCOES = ["Ataque", "Teste de Resistência", "Cura", "Passiva", "Extra"]

    def __init__(self, parent, ficha: dict, on_save=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._ficha = ficha
        self._on_save = on_save
        self._construir()

    def _construir(self):
        for w in self.winfo_children():
            w.destroy()

        # ══════════════════════════════════════════════════════════════════════
        # Cabeçalho
        # ══════════════════════════════════════════════════════════════════════
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(5, 10))

        ctk.CTkLabel(header, text="Habilidades de Técnica",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")

        btn_adicionar = ctk.CTkButton(
            header, text="➕ Nova Técnica", width=140, height=30,
            font=ctk.CTkFont(size=12), fg_color="#1a5c1a", hover_color="#145214",
            command=self._abrir_popup_criacao
        )
        btn_adicionar.pack(side="right")

        # ══════════════════════════════════════════════════════════════════════
        # Lista de técnicas
        # ══════════════════════════════════════════════════════════════════════
        tecnicas = self._ficha.setdefault("habilidades_tecnicas", [])

        if not tecnicas:
            ctk.CTkLabel(self, text="Nenhuma técnica criada. Clique em 'Nova Técnica' para começar.",
                         font=ctk.CTkFont(size=13), text_color="gray").pack(pady=40)
            return

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        for tecnica in tecnicas:
            self._criar_card(scroll, tecnica)

        # Scroll com roda do mouse
        self._aplicar_scroll(scroll)

    def _aplicar_scroll(self, scroll):
        def _scroll(delta):
            scroll._parent_canvas.yview_scroll(delta, "units")
        def _bind_scroll_recursivo(widget):
            widget.bind("<MouseWheel>", lambda e: _scroll(-1 if e.delta > 0 else 1))
            widget.bind("<Button-4>", lambda e: _scroll(-1))
            widget.bind("<Button-5>", lambda e: _scroll(1))
            for child in widget.winfo_children():
                _bind_scroll_recursivo(child)
        _bind_scroll_recursivo(scroll)
        scroll._parent_canvas.bind("<MouseWheel>", lambda e: _scroll(-1 if e.delta > 0 else 1))
        scroll._parent_canvas.bind("<Button-4>", lambda e: _scroll(-1))
        scroll._parent_canvas.bind("<Button-5>", lambda e: _scroll(1))
        scroll.focus_set()

    def _criar_card(self, parent, tecnica: dict):
        card = ctk.CTkFrame(parent, fg_color="#1e1e1e", corner_radius=8,
                            border_width=1, border_color="#333333")
        card.pack(fill="x", pady=4, padx=2)

        # Linha superior: Nome e Nível
        topo = ctk.CTkFrame(card, fg_color="transparent")
        topo.pack(fill="x", padx=12, pady=(10, 4))

        nome = tecnica.get("nome", "Sem nome")
        nivel = tecnica.get("nivel", 0)
        ctk.CTkLabel(topo, text=f"{nome} (Nível {nivel})",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")

        conj = tecnica.get("conjuracao", "Padrão")
        custo = tecnica.get("custo_pe", 0)
        ctk.CTkLabel(topo, text=f"{conj} • {custo} PE",
                     font=ctk.CTkFont(size=11), text_color="#888888").pack(side="right")

        # Segunda linha: Alcance, Alvo, Duração
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(fill="x", padx=12, pady=(0, 4))

        alcance = tecnica.get("alcance", "Curto")
        alvo = tecnica.get("alvo", "1 ser")
        duracao = tecnica.get("duracao", "Instantânea")
        tipo_mec = tecnica.get("tipo_mecanica", "Extra")

        ctk.CTkLabel(info_frame, text=f"Alcance: {alcance} • Alvo: {alvo} • Duração: {duracao}",
                     font=ctk.CTkFont(size=11), text_color="#888888").pack(side="left")
        ctk.CTkLabel(info_frame, text=f"[{tipo_mec}]",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="#3498db").pack(side="right")

        # Descrição resumida
        desc = tecnica.get("descricao", "")
        if desc:
            previa = (desc[:80] + "…") if len(desc) > 80 else desc
            ctk.CTkLabel(card, text=previa, wraplength=500, justify="left",
                         font=ctk.CTkFont(size=11),
                         text_color="#aaaaaa").pack(anchor="w", padx=12, pady=(0, 8))
        
        # Exibe dano se houver 
        params = tecnica.get("parametros", {})
        dano = params.get("dano", "")
        if dano:
            ctk.CTkLabel(card, text=f"Dano: {dano}", font=ctk.CTkFont(size=11),
                         text_color="#e67e22").pack(anchor="w", padx=12, pady=(0,4))
            
        # Exibe quantidade de efeitos
        efeitos = tecnica.get("efeitos", [])
        if efeitos:
            ctk.CTkLabel(card, text=f"⚡ {len(efeitos)} efeito(s) configurado(s)",
                         font=ctk.CTkFont(size=10), text_color="#888888").pack(anchor="w", padx=12, pady=(0,4))

        # ══════════════════════════════════════════════════════════════════════
        # Botões de ação
        # ══════════════════════════════════════════════════════════════════════
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkButton(btn_frame, text="Editar", width=70, height=28,
                      font=ctk.CTkFont(size=11), fg_color="transparent",
                      border_width=1, border_color="#444444",
                      command=lambda: self._abrir_popup_edicao(tecnica)).pack(side="left", padx=(0, 5))

        tipo_mec = tecnica.get("tipo_mecanica", "Extra")
        if tipo_mec == "Passiva":
            tecnicas_ativas = self._ficha.setdefault("tecnicas_ativas", [])
            ativa = tecnica["id"] in tecnicas_ativas
            var_ativa = ctk.BooleanVar(value=ativa)

            def toggle_passiva():
                if var_ativa.get():
                    if tecnica["id"] not in tecnicas_ativas:
                        tecnicas_ativas.append(tecnica["id"])
                else:
                    if tecnica["id"] in tecnicas_ativas:
                        tecnicas_ativas.remove(tecnica["id"])
                if self._on_save:
                    self._on_save()
                self._construir()

            cb = ctk.CTkCheckBox(btn_frame, text="Ativar", variable=var_ativa,
                                 font=ctk.CTkFont(size=11), command=toggle_passiva)
            cb.pack(side="left", padx=5)
        else:
            ctk.CTkButton(btn_frame, text="Usar", width=70, height=28,
                          font=ctk.CTkFont(size=11), fg_color="#2a6b2a", hover_color="#1a4a1a",
                          command=lambda: self._executar_tecnica(tecnica)).pack(side="left", padx=5)

        ctk.CTkButton(btn_frame, text="Remover", width=70, height=28,
                      font=ctk.CTkFont(size=11), fg_color="#8B0000",
                      hover_color="#5a0000",
                      command=lambda: self._remover_tecnica(tecnica)).pack(side="right")

    # ──────────────────────────────────────────────────────────────────────────
    # Popup de Criação / Edição
    # ──────────────────────────────────────────────────────────────────────────

    def _abrir_popup_criacao(self):
        self._abrir_popup_edicao(None)

    def _abrir_popup_edicao(self, tecnica: dict = None):
        editando = tecnica is not None
        titulo = "Editar Técnica" if editando else "Nova Técnica"

        popup = ctk.CTkToplevel(self.winfo_toplevel())
        popup.title(titulo)
        popup.geometry("700x800")
        popup.minsize(600, 650)
        popup.resizable(False, False)
        popup.after(100, popup.grab_set)

        # ══════════════════════════════════════════════════════════════════════
        # Área rolável (contém todos os campos de edição)
        # ══════════════════════════════════════════════════════════════════════
        scroll = ctk.CTkScrollableFrame(popup, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(20, 10))

        main = ctk.CTkFrame(scroll, fg_color="transparent")
        main.pack(fill="both", expand=True)

        ctk.CTkLabel(main, text=titulo, font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0,15))

        # --- Campos básicos (idênticos ao seu código) ---
        ctk.CTkLabel(main, text="Nome:", anchor="w").pack(fill="x")
        e_nome = ctk.CTkEntry(main)
        if editando:
            e_nome.insert(0, tecnica.get("nome", ""))
        e_nome.pack(fill="x", pady=(2, 12))

        # Linha com Nível e Conjuração
        row1 = ctk.CTkFrame(main, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 12))
        row1.columnconfigure(0, weight=1)
        row1.columnconfigure(1, weight=1)

        ctk.CTkLabel(row1, text="Nível:", anchor="w").grid(row=0, column=0, sticky="w", padx=(0,5))
        nivel_var = ctk.StringVar(value=str(tecnica.get("nivel", 0)) if editando else "0")
        nivel_menu = ctk.CTkOptionMenu(row1, values=self.NIVEL_OPCOES, variable=nivel_var)
        nivel_menu.grid(row=1, column=0, sticky="ew", padx=(0,5))

        ctk.CTkLabel(row1, text="Conjuração:", anchor="w").grid(row=0, column=1, sticky="w", padx=(5,0))
        conj_var = ctk.StringVar(value=tecnica.get("conjuracao", "Padrão") if editando else "Padrão")
        conj_menu = ctk.CTkOptionMenu(row1, values=self.CONJURACAO_OPCOES, variable=conj_var)
        conj_menu.grid(row=1, column=1, sticky="ew", padx=(5,0))

        # Linha com Alcance e Alvo
        row2 = ctk.CTkFrame(main, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 12))
        row2.columnconfigure(0, weight=1)
        row2.columnconfigure(1, weight=1)

        ctk.CTkLabel(row2, text="Alcance:", anchor="w").grid(row=0, column=0, sticky="w", padx=(0,5))
        alcance_var = ctk.StringVar(value=tecnica.get("alcance", "Curto") if editando else "Curto")
        alcance_menu = ctk.CTkOptionMenu(row2, values=self.ALCANCE_OPCOES, variable=alcance_var)
        alcance_menu.grid(row=1, column=0, sticky="ew", padx=(0,5))

        ctk.CTkLabel(row2, text="Alvo:", anchor="w").grid(row=0, column=1, sticky="w", padx=(5,0))
        e_alvo = ctk.CTkEntry(row2)
        if editando:
            e_alvo.insert(0, tecnica.get("alvo", "1 ser"))
        else:
            e_alvo.insert(0, "1 ser")
        e_alvo.grid(row=1, column=1, sticky="ew", padx=(5,0))

        # Linha com Duração e Tipo Mecânica
        row3 = ctk.CTkFrame(main, fg_color="transparent")
        row3.pack(fill="x", pady=(0, 12))
        row3.columnconfigure(0, weight=1)
        row3.columnconfigure(1, weight=1)

        ctk.CTkLabel(row3, text="Duração:", anchor="w").grid(row=0, column=0, sticky="w", padx=(0,5))
        duracao_var = ctk.StringVar(value=tecnica.get("duracao", "Instantânea") if editando else "Instantânea")
        duracao_menu = ctk.CTkOptionMenu(row3, values=self.DURACAO_OPCOES, variable=duracao_var)
        duracao_menu.grid(row=1, column=0, sticky="ew", padx=(0,5))

        ctk.CTkLabel(row3, text="Tipo Mecânica:", anchor="w").grid(row=0, column=1, sticky="w", padx=(5,0))
        tipo_mec_var = ctk.StringVar(value=tecnica.get("tipo_mecanica", "Extra") if editando else "Extra")
        tipo_mec_menu = ctk.CTkOptionMenu(row3, values=self.TIPO_MECANICA_OPCOES, variable=tipo_mec_var)
        tipo_mec_menu.grid(row=1, column=1, sticky="ew", padx=(5,0))

        # Campo de Dano (fórmula)
        ctk.CTkLabel(main, text="Dano / Efeito (fórmula):", anchor="w").pack(fill="x")
        e_dano = ctk.CTkEntry(main, placeholder_text="ex: 4d6+12, 2d10+AB")
        if editando and "dano" in tecnica.get("parametros", {}):
            e_dano.insert(0, tecnica["parametros"]["dano"])
        e_dano.pack(fill="x", pady=(2, 12))

        # Custo PE
        ctk.CTkLabel(main, text="Custo PE (calculado automaticamente):", anchor="w").pack(fill="x", pady=(0,2))
        lbl_custo = ctk.CTkLabel(main, text="", font=ctk.CTkFont(size=12, weight="bold"), text_color="#f1c40f")
        lbl_custo.pack(anchor="w", pady=(0,12))

        def atualizar_custo(*args):
            try:
                nivel = int(nivel_var.get())
            except ValueError:
                nivel = 0
            if nivel <= 5:
                custo = nivel * 2
            else:
                from ficha import construir_contexto_base
                ctx = construir_contexto_base(self._ficha)
                ab = ctx.get("AB", 1)
                lp = ctx.get("LP", 1)
                nex = ctx.get("NEX", 5)
                custo = int(nex * (ab + lp))
            lbl_custo.configure(text=f"{custo} PE")

        nivel_var.trace_add("write", atualizar_custo)
        atualizar_custo()

        # Descrição
        ctk.CTkLabel(main, text="Descrição / Efeito:", anchor="w").pack(fill="x")
        e_desc = ctk.CTkTextbox(main, height=100)
        if editando:
            e_desc.insert("1.0", tecnica.get("descricao", ""))
        e_desc.pack(fill="x", pady=(2, 12))

        # ══════════════════════════════════════════════════════════════════════
        # Gerenciamento de Efeitos (Scaling)
        # ══════════════════════════════════════════════════════════════════════
        efeitos_temp = list(tecnica.get("efeitos", [])) if editando else []

        def abrir_efeitos():
            nonlocal efeitos_temp
            popup_efeitos = EfeitosPopup(
                popup,
                efeitos_existentes=efeitos_temp,
                on_save=lambda novos: efeitos_temp.clear() or efeitos_temp.extend(novos)
            )
            popup_efeitos.abrir()

        btn_efeitos = ctk.CTkButton(
            main,
            text="⚙️ Gerenciar Efeitos (Scaling)",
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            command=abrir_efeitos
        )
        btn_efeitos.pack(fill="x", pady=(10, 5))

        # ══════════════════════════════════════════════════════════════════════
        # Barra de botões fixa na parte inferior
        # ══════════════════════════════════════════════════════════════════════
        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))

        def salvar():
            nome = e_nome.get().strip()
            if not nome:
                messagebox.showwarning("Aviso", "O nome da técnica é obrigatório.")
                return

            try:
                nivel = int(nivel_var.get())
                custo = int(lbl_custo.cget("text").split()[0])
            except ValueError:
                nivel = 0
                custo = 0

            params = tecnica.get("parametros", {}) if editando else {}
            params["dano"] = e_dano.get().strip() or "0"

            nova_tec = {
                "id": tecnica.get("id") if editando else str(uuid.uuid4()),
                "nome": nome,
                "nivel": nivel,
                "conjuracao": conj_var.get(),
                "alcance": alcance_var.get(),
                "alvo": e_alvo.get().strip() or "1 ser",
                "duracao": duracao_var.get(),
                "custo_pe": custo,
                "descricao": e_desc.get("1.0", "end-1c").strip(),
                "tipo_mecanica": tipo_mec_var.get(),
                "parametros": params,
                "efeitos": efeitos_temp 
            }

            tecnicas = self._ficha.setdefault("habilidades_tecnicas", [])
            if editando:
                for i, t in enumerate(tecnicas):
                    if t.get("id") == tecnica.get("id"):
                        tecnicas[i] = nova_tec
                        break
            else:
                tecnicas.append(nova_tec)

            if self._on_save:
                self._on_save()
            popup.destroy()
            self._construir()

        ctk.CTkButton(btn_frame, text="Salvar", fg_color="#1a6b1a", hover_color="#145214",
                      command=salvar).pack(side="right", padx=(5,0))
        ctk.CTkButton(btn_frame, text="Cancelar", fg_color="transparent", border_width=1,
                      command=popup.destroy).pack(side="right")
    # ──────────────────────────────────────────────────────────────────────────
    # Ações
    # ──────────────────────────────────────────────────────────────────────────

    def _executar_tecnica(self, tecnica: dict):
        """Executa a técnica (placeholder)."""
        messagebox.showinfo("Executar Técnica", f"Execução de '{tecnica.get('nome')}' será implementada no módulo utils/tecnicas.py")

    def _remover_tecnica(self, tecnica: dict):
        if not messagebox.askyesno("Confirmar", f"Remover '{tecnica.get('nome', 'esta técnica')}'?"):
            return

        tecnicas = self._ficha.get("habilidades_tecnicas", [])
        tecnicas = [t for t in tecnicas if t.get("id") != tecnica.get("id")]
        self._ficha["habilidades_tecnicas"] = tecnicas

        if self._on_save:
            self._on_save()
        self._construir()

    def atualizar(self):
        self._construir()