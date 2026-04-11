import customtkinter as ctk
import uuid
from tkinter import messagebox

class PainelHabilidades(ctk.CTkFrame):
    """Aba: gerenciamento de habilidades gerais (não feitiços)."""

    TIPOS = ["Passiva", "Ativa"]

    def __init__(self, parent, ficha: dict, on_change=None, on_save=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._ficha = ficha
        self._on_change = on_change
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

        ctk.CTkLabel(header, text="Habilidades Gerais",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")

        btn_adicionar = ctk.CTkButton(
            header, text="➕ Nova Habilidade", width=150, height=30,
            font=ctk.CTkFont(size=12), fg_color="#1a5c1a", hover_color="#145214",
            command=self._abrir_popup_criacao
        )
        btn_adicionar.pack(side="right")

        # ══════════════════════════════════════════════════════════════════════
        # Lista de habilidades
        # ══════════════════════════════════════════════════════════════════════
        habilidades = self._ficha.setdefault("habilidades_gerais", [])

        if not habilidades:
            ctk.CTkLabel(self, text="Nenhuma habilidade criada. Clique em 'Nova Habilidade' para começar.",
                         font=ctk.CTkFont(size=13), text_color="gray").pack(pady=40)
            return

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        for hab in habilidades:
            self._criar_card(scroll, hab)

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

    def _criar_card(self, parent, hab: dict):
        card = ctk.CTkFrame(parent, fg_color="#1e1e1e", corner_radius=8,
                            border_width=1, border_color="#333333")
        card.pack(fill="x", pady=4, padx=2)

        # Linha superior: Nome e Tipo
        topo = ctk.CTkFrame(card, fg_color="transparent")
        topo.pack(fill="x", padx=12, pady=(10, 4))

        nome = hab.get("nome", "Sem nome")
        tipo = hab.get("tipo", "Ativa")
        cor_tipo = "#2ecc71" if tipo == "Passiva" else "#e67e22"
        ctk.CTkLabel(topo, text=nome, font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        ctk.CTkLabel(topo, text=tipo, font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=cor_tipo).pack(side="right")

        # Custo PE (se houver)
        custo = hab.get("custo_pe", 0)
        if custo > 0:
            ctk.CTkLabel(card, text=f"Custo: {custo} PE", font=ctk.CTkFont(size=11),
                         text_color="#f1c40f").pack(anchor="w", padx=12, pady=(0,4))

        # Descrição resumida
        desc = hab.get("descricao", "")
        if desc:
            previa = (desc[:80] + "…") if len(desc) > 80 else desc
            ctk.CTkLabel(card, text=previa, wraplength=500, justify="left",
                         font=ctk.CTkFont(size=11),
                         text_color="#aaaaaa").pack(anchor="w", padx=12, pady=(0, 8))

        # Botões de ação
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkButton(btn_frame, text="Editar", width=70, height=28,
                      font=ctk.CTkFont(size=11), fg_color="transparent",
                      border_width=1, border_color="#444444",
                      command=lambda: self._abrir_popup_edicao(hab)).pack(side="left", padx=(0, 5))

        ctk.CTkButton(btn_frame, text="Remover", width=70, height=28,
                      font=ctk.CTkFont(size=11), fg_color="#8B0000",
                      hover_color="#5a0000",
                      command=lambda: self._remover_habilidade(hab)).pack(side="left")

        # Controles de ativação para passivas
        if tipo == "Passiva" and hab.get("efeitos"):
            self._criar_controles_passiva(card, hab)

    def _criar_controles_passiva(self, parent, hab: dict):
        """Cria checkbox para ativar/desativar passiva (similar a feitiços)."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=12, pady=(0, 8))

        passivas_ativas = self._ficha.get("passivas_ativas", {})
        hab_id = hab["id"]
        ativa = hab_id in passivas_ativas

        var_ativa = ctk.BooleanVar(value=ativa)
        cb = ctk.CTkCheckBox(frame, text="Ativar", variable=var_ativa,
                             font=ctk.CTkFont(size=12),
                             command=lambda: self._toggle_passiva(hab_id, var_ativa))
        cb.pack(side="left")

    def _toggle_passiva(self, hab_id: str, var_ativa: ctk.BooleanVar):
        ativa = var_ativa.get()
        passivas = self._ficha.setdefault("passivas_ativas", {})
        if ativa:
            passivas[hab_id] = "BASE"  # Habilidades não têm versões, sempre BASE
        else:
            passivas.pop(hab_id, None)
        if self._on_change:
            self._on_change()
        if self._on_save:
            self._on_save()

    # ──────────────────────────────────────────────────────────────────────────
    # Popup de Criação / Edição
    # ──────────────────────────────────────────────────────────────────────────

    def _abrir_popup_criacao(self):
        self._abrir_popup_edicao(None)

    def _abrir_popup_edicao(self, hab: dict = None):
        editando = hab is not None
        titulo = "Editar Habilidade" if editando else "Nova Habilidade"

        popup = ctk.CTkToplevel(self.winfo_toplevel())
        popup.title(titulo)
        popup.geometry("600x650")
        popup.minsize(500, 500)
        popup.resizable(False, False)
        popup.after(100, popup.grab_set)

        # Área rolável
        scroll = ctk.CTkScrollableFrame(popup, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(20, 10))

        main = ctk.CTkFrame(scroll, fg_color="transparent")
        main.pack(fill="both", expand=True)

        ctk.CTkLabel(main, text=titulo, font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0,15))

        # Nome
        ctk.CTkLabel(main, text="Nome:", anchor="w").pack(fill="x")
        e_nome = ctk.CTkEntry(main)
        if editando:
            e_nome.insert(0, hab.get("nome", ""))
        e_nome.pack(fill="x", pady=(2, 12))

        # Tipo (Passiva/Ativa)
        ctk.CTkLabel(main, text="Tipo:", anchor="w").pack(fill="x")
        tipo_var = ctk.StringVar(value=hab.get("tipo", "Ativa") if editando else "Ativa")
        tipo_menu = ctk.CTkOptionMenu(main, values=self.TIPOS, variable=tipo_var)
        tipo_menu.pack(fill="x", pady=(2, 12))

        # Custo PE (opcional)
        ctk.CTkLabel(main, text="Custo PE (opcional):", anchor="w").pack(fill="x")
        e_custo = ctk.CTkEntry(main)
        if editando:
            e_custo.insert(0, str(hab.get("custo_pe", 0)))
        else:
            e_custo.insert(0, "0")
        e_custo.pack(fill="x", pady=(2, 12))

        # Descrição
        ctk.CTkLabel(main, text="Descrição:", anchor="w").pack(fill="x")
        e_desc = ctk.CTkTextbox(main, height=100)
        if editando:
            e_desc.insert("1.0", hab.get("descricao", ""))
        e_desc.pack(fill="x", pady=(2, 12))

        # Efeitos (para passivas) - placeholder
        ctk.CTkLabel(main, text="Efeitos (em breve - use o editor JSON por enquanto)",
                     font=ctk.CTkFont(size=12, slant="italic"), text_color="#888888").pack(anchor="w", pady=(10,0))

        # Barra de botões fixa
        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))

        def salvar():
            nome = e_nome.get().strip()
            if not nome:
                messagebox.showwarning("Aviso", "O nome da habilidade é obrigatório.")
                return

            try:
                custo = int(e_custo.get())
            except ValueError:
                custo = 0

            nova_hab = {
                "id": hab.get("id") if editando else str(uuid.uuid4()),
                "nome": nome,
                "tipo": tipo_var.get(),
                "custo_pe": custo,
                "descricao": e_desc.get("1.0", "end-1c").strip(),
                "efeitos": hab.get("efeitos", []) if editando else []
            }

            habilidades = self._ficha.setdefault("habilidades_gerais", [])
            if editando:
                for i, h in enumerate(habilidades):
                    if h.get("id") == hab.get("id"):
                        habilidades[i] = nova_hab
                        break
            else:
                habilidades.append(nova_hab)

            if self._on_save:
                self._on_save()
            if self._on_change:
                self._on_change()
            popup.destroy()
            self._construir()

        # Botão para gerenciar efeitos (inicialmente só abre popup vazio)
        btn_efeitos = ctk.CTkButton(
            main,
            text="⚙️ Gerenciar Efeitos",
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
            command=lambda: self._abrir_popup_efeitos(hab if editando else None)
        )
        btn_efeitos.pack(pady=(10, 5))
        
        ctk.CTkButton(btn_frame, text="Salvar", fg_color="#1a6b1a", hover_color="#145214",
                      command=salvar).pack(side="right", padx=(5,0))
        ctk.CTkButton(btn_frame, text="Cancelar", fg_color="transparent", border_width=1,
                      command=popup.destroy).pack(side="right")


    # ──────────────────────────────────────────────────────────────────────────
    # Efeitos (em construção)
    # ──────────────────────────────────────────────────────────────────────────
    
    def _abrir_popup_efeitos(self, hab: dict = None):
        from views.Efeitos_Popup import EfeitosPopup
        efeitos = hab.get("efeitos", []) if hab else []
        popup = EfeitosPopup(self.winfo_toplevel(), efeitos,
                            on_save=lambda novos: self._salvar_efeitos(hab, novos))
        popup.abrir()

    def _salvar_efeitos(self, hab: dict, novos_efeitos: list):
        if hab:
            hab["efeitos"] = novos_efeitos
        # Se for criação, os efeitos serão salvos quando o popup principal for salvo

    # ──────────────────────────────────────────────────────────────────────────
    # Remoção
    # ──────────────────────────────────────────────────────────────────────────

    def _remover_habilidade(self, hab: dict):
        if not messagebox.askyesno("Confirmar", f"Remover '{hab.get('nome', 'esta habilidade')}'?"):
            return

        habilidades = self._ficha.get("habilidades_gerais", [])
        habilidades = [h for h in habilidades if h.get("id") != hab.get("id")]
        self._ficha["habilidades_gerais"] = habilidades

        # Remove das passivas ativas se estiver lá
        passivas = self._ficha.get("passivas_ativas", {})
        if hab["id"] in passivas:
            del passivas[hab["id"]]

        if self._on_save:
            self._on_save()
        if self._on_change:
            self._on_change()
        self._construir()

    def atualizar(self):
        self._construir()