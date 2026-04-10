import customtkinter as ctk

class PainelResumo(ctk.CTkFrame):
    """Aba: exibe os bônus passivos acumulados e outras estatísticas derivadas."""

    def __init__(self, parent, ficha: dict, info_grau=None, atributos=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._ficha = ficha
        self._info_grau = info_grau or {}
        self._atributos = atributos or {}
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
                ctk.CTkLabel(linha, text=f"{int(valor):+}", font=ctk.CTkFont(size=13, weight="bold"),
                             text_color="#2ecc71" if valor >=0 else "#e74c3c").pack(side="right")
                
        scroll.pack(fill="both", expand=True)

        # ══════════════════════════════════════════════════════════════════════
        # Totais de NEX
        # ══════════════════════════════════════════════════════════════════════
        totais_nex = self._ficha.get("totais_nex", {})
        if totais_nex:
            frame_nex = ctk.CTkFrame(scroll, fg_color="#1e1e1e", corner_radius=8)
            frame_nex.pack(fill="x", pady=4, padx=4)

            ctk.CTkLabel(frame_nex, text="Totais de NEX",
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color="#cccccc").pack(anchor="w", padx=12, pady=(8,4))

            # Mapeamento de nomes amigáveis
            nomes_nex = {
                "pontos_atributo": "Pontos de Atributo",
                "feiticos": "Feitiços",
                "graus_treinamento": "Graus de Treinamento",
                "habilidade_trilha": "Habilidades de Trilha",
                "afinidade": "Afinidade",
                "expansao_modo": "Expansão ou Modo",
                "melhorias_superiores": "Melhorias Superiores",
                "habilidades_lendarias": "Habilidades Lendárias",
                "habilidade_tecnica_n6": "Hab. Técnica Nível 6"
            }

            for chave, valor in totais_nex.items():
                if valor == 0:
                    continue
                nome = nomes_nex.get(chave, chave.replace("_", " ").title())
                linha = ctk.CTkFrame(frame_nex, fg_color="transparent")
                linha.pack(fill="x", padx=12, pady=2)
                ctk.CTkLabel(linha, text=nome, font=ctk.CTkFont(size=12),
                             text_color="#aaaaaa").pack(side="left")
                ctk.CTkLabel(linha, text=str(valor), font=ctk.CTkFont(size=13, weight="bold"),
                             text_color="#3498db").pack(side="right")
    
        # ══════════════════════════════════════════════════════════════════════
        # Totais de Grau
        # ══════════════════════════════════════════════════════════════════════
        totais_grau = self._ficha.get("totais_grau", {})
        grau_atual = self._ficha.get("grau", "Grau 4")

        if totais_grau:
            frame_grau = ctk.CTkFrame(scroll, fg_color="#1e1e1e", corner_radius=8)
            frame_grau.pack(fill="x", pady=4, padx=4)

            ctk.CTkLabel(frame_grau, text=f"Totais de Grau ({grau_atual})",
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color="#cccccc").pack(anchor="w", padx=12, pady=(8,4))

            # Itens numéricos
            if "pontos_atributo" in totais_grau:
                self._adicionar_linha(frame_grau, "Pontos de Atributo", totais_grau["pontos_atributo"])
            if "graus_treinamento" in totais_grau:
                self._adicionar_linha(frame_grau, "Graus de Treinamento", totais_grau["graus_treinamento"])
            if "encantamentos" in totais_grau:
                valor = totais_grau["encantamentos"]
                texto = f"{valor:.1f}" if isinstance(valor, float) and valor != int(valor) else str(int(valor))
                self._adicionar_linha(frame_grau, "Encantamentos", texto)
            if "maldicoes" in totais_grau:
                self._adicionar_linha(frame_grau, "Maldições", totais_grau["maldicoes"])

            # Bônus especiais
            if "bonus_vigor" in totais_grau:
                bv = totais_grau["bonus_vigor"]
                self._adicionar_linha(frame_grau, bv["nome"], f"{bv['valor']} PV")
            if "bonus_presenca" in totais_grau:
                bp = totais_grau["bonus_presenca"]
                self._adicionar_linha(frame_grau, bp["nome"], f"{bp['valor']} PE")

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
    
    
    def _adicionar_linha(self, parent, nome: str, valor):
        linha = ctk.CTkFrame(parent, fg_color="transparent")
        linha.pack(fill="x", padx=12, pady=2)
        ctk.CTkLabel(linha, text=nome, font=ctk.CTkFont(size=12),
                     text_color="#aaaaaa").pack(side="left")
        cor = "#3498db"
        if isinstance(valor, (int, float)):
            if valor > 0:
                cor = "#2ecc71"
            elif valor < 0:
                cor = "#e74c3c"
        ctk.CTkLabel(linha, text=str(valor), font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=cor).pack(side="right")
     