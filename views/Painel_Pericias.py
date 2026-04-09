import customtkinter as ctk

from ficha import rolar_atributo

class PainelPericias(ctk.CTkFrame):
    """Aba: lista de todas as perícias com edição e rolagem."""

    ATRIBUTOS = ["AGI", "FOR", "INT", "VIG", "PRE"]
    TREINAMENTOS = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]

    def __init__(self, parent, ficha: dict, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._ficha = ficha
        self._construir()

    def _construir(self):
        for w in self.winfo_children():
            w.destroy()

        # Cabeçalho
        header = ctk.CTkFrame(self, fg_color="#1e1e1e", corner_radius=6)
        header.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(header, text="Perícia", width=130,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=4)
        ctk.CTkLabel(header, text="Atributo", width=60,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=2)
        ctk.CTkLabel(header, text="Treino", width=60,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=2)
        ctk.CTkLabel(header, text="Bônus", width=60,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=2)
        ctk.CTkLabel(header, text="Total", width=50,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=2)
        ctk.CTkLabel(header, text="", width=60).pack(side="left")  # espaço para botão

        # Área rolável
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Dicionário para guardar referências aos widgets de cada perícia
        self._pericia_widgets = {}

        pericias = self._ficha.setdefault("pericias", {})
        for nome, dados in pericias.items():
            self._criar_linha(scroll, nome, dados)

        # Scroll com roda do mouse
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

    def _criar_linha(self, parent, nome: str, dados: dict):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=1)

        # Nome
        ctk.CTkLabel(frame, text=nome, width=130, anchor="w",
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=4)

        # Atributo (dropdown com override)
        attr_override = dados.get("atributo_override")
        attr_base = dados.get("atributo_base", "FOR")
        attr_atual = attr_override if attr_override else attr_base

        attr_var = ctk.StringVar(value=attr_atual)
        attr_menu = ctk.CTkOptionMenu(
            frame,
            values=self.ATRIBUTOS + ["(padrão)"],
            variable=attr_var,
            width=70,
            height=28,
            font=ctk.CTkFont(size=12),
            command=lambda val, n=nome: self._ao_mudar_atributo(n, val)
        )
        attr_menu.pack(side="left", padx=2)
        # Se houver override, mostra o atributo; senão mostra "(padrão)"
        if not attr_override:
            attr_var.set("(padrão)")

        # Treinamento
        treino_var = ctk.StringVar(value=str(dados.get("treinamento", 0)))
        treino_menu = ctk.CTkOptionMenu(
            frame,
            values=[str(t) for t in self.TREINAMENTOS],
            variable=treino_var,
            width=60,
            height=28,
            font=ctk.CTkFont(size=12),
            command=lambda val, n=nome: self._ao_mudar_treinamento(n, int(val))
        )
        treino_menu.pack(side="left", padx=2)

        # Bônus (entry)
        bonus_var = ctk.StringVar(value=str(dados.get("bonus", 0)))
        bonus_entry = ctk.CTkEntry(
            frame,
            textvariable=bonus_var,
            width=50,
            height=28,
            font=ctk.CTkFont(size=12),
            justify="center"
        )
        bonus_entry.pack(side="left", padx=2)
        bonus_entry.bind("<FocusOut>", lambda e, n=nome, v=bonus_var: self._ao_mudar_bonus(n, v.get()))
        bonus_entry.bind("<Return>", lambda e, n=nome, v=bonus_var: self._ao_mudar_bonus(n, v.get()))

        # Valor total (label)
        total_label = ctk.CTkLabel(frame, text="", width=50,
                                   font=ctk.CTkFont(size=13, weight="bold"))
        total_label.pack(side="left", padx=2)

        # Botão Rolar
        btn_rolar = ctk.CTkButton(
            frame,
            text="🎲",
            width=40,
            height=28,
            font=ctk.CTkFont(size=14),
            fg_color="#2a2a2a",
            hover_color="#3a3a3a",
            command=lambda n=nome: self._rolar_pericia(n)
        )
        btn_rolar.pack(side="left", padx=2)

        # Guarda referências
        self._pericia_widgets[nome] = {
            "attr_var": attr_var,
            "attr_menu": attr_menu,
            "treino_var": treino_var,
            "bonus_var": bonus_var,
            "total_label": total_label
        }

        # Atualiza total inicial
        self._atualizar_total(nome)

    def _atualizar_total(self, nome: str):
        """Recalcula e atualiza o label de total da perícia."""
        dados = self._ficha["pericias"][nome]
        atributos = self._ficha.get("atributos", {})

        attr_override = dados.get("atributo_override")
        attr_base = dados.get("atributo_base", "FOR")
        attr_valor = atributos.get(attr_override if attr_override else attr_base, 0)

        treino = dados.get("treinamento", 0)
        bonus = dados.get("bonus", 0)
        total = treino + bonus

        self._pericia_widgets[nome]["total_label"].configure(text=str(total))

    def _ao_mudar_atributo(self, nome: str, valor: str):
        """Callback do dropdown de atributo."""
        if valor == "(padrão)":
            self._ficha["pericias"][nome]["atributo_override"] = None
        else:
            self._ficha["pericias"][nome]["atributo_override"] = valor
        self._atualizar_total(nome)

    def _ao_mudar_treinamento(self, nome: str, valor: int):
        self._ficha["pericias"][nome]["treinamento"] = valor
        self._atualizar_total(nome)

    def _ao_mudar_bonus(self, nome: str, valor_str: str):
        try:
            bonus = int(valor_str)
        except ValueError:
            bonus = 0
        self._ficha["pericias"][nome]["bonus"] = bonus
        self._pericia_widgets[nome]["bonus_var"].set(str(bonus))
        self._atualizar_total(nome)

    def _rolar_pericia(self, nome: str):
        """Executa a rolagem da perícia e exibe o resultado em um popup."""
        dados = self._ficha["pericias"][nome]
        atributos = self._ficha.get("atributos", {})

        attr_override = dados.get("atributo_override")
        attr_base = dados.get("atributo_base", "FOR")
        attr_nome = attr_override if attr_override else attr_base
        attr_valor = atributos.get(attr_nome, 0)

        treino = dados.get("treinamento", 0)
        bonus = dados.get("bonus", 0)

        resultado = rolar_atributo(attr_valor, treino, bonus)

        # Popup de resultado
        popup = ctk.CTkToplevel(self.winfo_toplevel())
        popup.title(f"Rolagem: {nome}")
        popup.geometry("300x220")
        popup.resizable(False, False)
        popup.after(100, popup.grab_set)

        frame = ctk.CTkFrame(popup, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(frame, text=nome, font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0,10))

        dados_str = ", ".join(str(d) for d in resultado["dados"])
        ctk.CTkLabel(frame, text=f"Dados: {dados_str}",
                     font=ctk.CTkFont(size=12)).pack()

        if attr_valor == 0:
            modo = "Desvantagem (menor)"
        else:
            modo = f"Vantagem ({attr_valor}d20, maior)"
        ctk.CTkLabel(frame, text=f"Modo: {modo}",
                     font=ctk.CTkFont(size=12), text_color="#888888").pack()

        ctk.CTkLabel(frame, text=f"Escolhido: {resultado['escolhido']}",
                     font=ctk.CTkFont(size=14)).pack(pady=(5,0))

        ctk.CTkLabel(frame, text=f"+ Treino: {treino}   + Bônus: {bonus}",
                     font=ctk.CTkFont(size=12), text_color="#aaaaaa").pack()

        ctk.CTkLabel(frame, text=f"TOTAL: {resultado['total']}",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color="#f1c40f").pack(pady=(5,10))

        ctk.CTkButton(popup, text="Fechar", command=popup.destroy).pack()

    def atualizar(self):
        self._construir()
