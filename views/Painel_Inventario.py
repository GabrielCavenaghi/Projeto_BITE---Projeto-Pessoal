import customtkinter as ctk

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

