import customtkinter as ctk

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

