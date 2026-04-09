import customtkinter as ctk

class PainelResumo(ctk.CTkFrame):
    """Aba: exibe os bônus passivos acumulados e outras estatísticas derivadas."""

    def __init__(self, parent, ficha: dict, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._ficha = ficha
        self._construir()

    def _construir(self):
        for w in self.winfo_children():
            w.destroy()

        bonus = self._ficha.get("bonus_passivos", {})

        if not bonus:
            ctk.CTkLabel(self, text="Nenhum bônus passivo ativo.",
                         font=ctk.CTkFont(size=13), text_color="gray").pack(pady=40)
            return

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Agrupa por categoria (DEF, TR, DADO_CORPO, etc.)
        categorias = {}
        for alvo, valor in bonus.items():
            if valor == 0:
                continue
            cat = alvo.split("_")[0] if "_" in alvo else "Geral"
            categorias.setdefault(cat, []).append((alvo, valor))

        for cat, itens in categorias.items():
            frame_cat = ctk.CTkFrame(scroll, fg_color="#1e1e1e", corner_radius=8)
            frame_cat.pack(fill="x", pady=4, padx=4)

            ctk.CTkLabel(frame_cat, text=cat, font=ctk.CTkFont(size=14, weight="bold"),
                         text_color="#cccccc").pack(anchor="w", padx=12, pady=(8,4))

            for alvo, valor in itens:
                linha = ctk.CTkFrame(frame_cat, fg_color="transparent")
                linha.pack(fill="x", padx=12, pady=2)
                ctk.CTkLabel(linha, text=alvo, font=ctk.CTkFont(size=12),
                             text_color="#aaaaaa").pack(side="left")
                ctk.CTkLabel(linha, text=f"{valor:+}", font=ctk.CTkFont(size=13, weight="bold"),
                             text_color="#2ecc71" if valor >=0 else "#e74c3c").pack(side="right")
                
        scroll.pack(fill="both", expand=True)

        # ══════════════════════════════════════════════════════════════════════
        # Habilita scroll com roda do mouse
        # ══════════════════════════════════════════════════════════════════════
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
     