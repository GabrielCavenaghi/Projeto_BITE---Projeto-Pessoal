import customtkinter as ctk
import json
import os

from utils.skilltree import calcular_posicoes, pode_comprar, tem_filhos_comprados

class EditorSkilltree:
    def __init__(self, parent, ficha, on_close=None):
        self.parent = parent
        self.ficha_original = ficha
        self.on_close = on_close
        self.window = None

        # Carrega dados da skill tree
        self.skilltrees_data = self._carregar_skilltrees()
        # Cria cópia local dos dados editáveis
        self._criar_copia_temporaria()

    def _carregar_skilltrees(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        caminho = os.path.join(base_dir, "data", "skilltrees.json")
        if os.path.exists(caminho):
            with open(caminho, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _criar_copia_temporaria(self):
        import copy
        self.nos_comprados = copy.deepcopy(self.ficha_original.get("nos_comprados", {}))
        self.pontos_skilltree = copy.deepcopy(self.ficha_original.get("pontos_skilltree", {}))
        self.abas_confirmadas = copy.deepcopy(self.ficha_original.get("abas_confirmadas", []))

        # Inicializa defaults se necessário
        atributos = self.ficha_original.get("atributos", {})
        for sigla in ["AGI", "FOR", "INT", "VIG", "PRE"]:
            if sigla not in self.pontos_skilltree:
                valor = atributos.get(sigla, 1)
                self.pontos_skilltree[sigla] = valor * 2
        if "GERAL" not in self.pontos_skilltree:
            self.pontos_skilltree["GERAL"] = 0

        for sigla in ["AGI", "FOR", "INT", "VIG", "PRE", "GERAL"]:
            if sigla not in self.nos_comprados:
                self.nos_comprados[sigla] = []

    def abrir(self):
        self.window = ctk.CTkToplevel(self.parent)
        self.window.title("Editar Skill Tree")
        self.window.geometry("900x700")
        self.window.minsize(800, 600)
        self.window.after(100, self.window.grab_set)

        self._construir_interface()
        self.window.protocol("WM_DELETE_WINDOW", self._cancelar)

    def _cancelar(self):
        self.window.destroy()

    def _salvar(self):
        # Aplica as mudanças na ficha original
        self.ficha_original["nos_comprados"] = self.nos_comprados
        self.ficha_original["pontos_skilltree"] = self.pontos_skilltree
        self.ficha_original["abas_confirmadas"] = self.abas_confirmadas
        if self.on_close:
            self.on_close()
        self.window.destroy()

    # ===============================================================
    # Construção da interface
    # ===============================================================
    def _construir_interface(self):
        main = ctk.CTkFrame(self.window, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # Barra superior: abas, pontos, botões
        top_bar = ctk.CTkFrame(main, fg_color="transparent")
        top_bar.pack(fill="x", pady=(0,5))

        # Abas
        self.tab_buttons = {}
        self.aba_ativa = "INT"
        for sigla in ["AGI", "FOR", "INT", "VIG", "PRE", "GERAL"]:
            btn = ctk.CTkButton(
                top_bar, text=sigla, width=60, height=30,
                command=lambda s=sigla: self._trocar_aba(s)
            )
            btn.pack(side="left", padx=2)
            self.tab_buttons[sigla] = btn

        # Label pontos
        self.lbl_pontos = ctk.CTkLabel(top_bar, text="", font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_pontos.pack(side="right", padx=10)

         # Botão Confirmar Aba (posicionado à direita)
        self.btn_confirmar = ctk.CTkButton(
            top_bar, text="✓ Confirmar Aba", width=120, height=30,
            fg_color="#1a5c1a", hover_color="#145214",
            command=self._confirmar_aba_atual
        )
        self.btn_confirmar.pack(side="right", padx=5)
        self.btn_confirmar.pack_forget()  # começa oculto

        # Botão Resetar
        btn_reset = ctk.CTkButton(
            top_bar, text="⟲ Resetar", width=90, height=30,
            fg_color="#8B0000", hover_color="#5a0000",
            command=self._resetar_aba_ativa
        )
        btn_reset.pack(side="right", padx=5)

        # Área do canvas
        self.canvas_frame = ctk.CTkFrame(main, fg_color="transparent")
        self.canvas_frame.pack(fill="both", expand=True)

        self.canvas = ctk.CTkCanvas(self.canvas_frame, bg="#1a1a1a", highlightthickness=0)
        scroll_x = ctk.CTkScrollbar(self.canvas_frame, orientation="horizontal", command=self.canvas.xview)
        scroll_y = ctk.CTkScrollbar(self.canvas_frame, orientation="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)
        scroll_x.pack(side="bottom", fill="x")
        scroll_y.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Eventos de scroll
        self.canvas.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))
        self.canvas.bind("<MouseWheel>", lambda e: self.canvas.yview_scroll(-1*(e.delta//120), "units"))
        self.canvas.bind("<Configure>", lambda e: self._desenhar_skilltree())

        # Barra inferior: Salvar / Cancelar
        bottom_bar = ctk.CTkFrame(main, fg_color="transparent")
        bottom_bar.pack(fill="x", pady=(10,0))

        ctk.CTkButton(bottom_bar, text="Salvar", width=100, fg_color="#1a6b1a", hover_color="#145214",
                      command=self._salvar).pack(side="right", padx=5)
        ctk.CTkButton(bottom_bar, text="Cancelar", width=100, fg_color="#555555", hover_color="#444444",
                      command=self._cancelar).pack(side="right", padx=5)

        self._trocar_aba(self.aba_ativa)

    def _trocar_aba(self, sigla):
        if sigla == "GERAL" and not self._todas_abas_confirmadas():
            self.aba_ativa = sigla
            self._atualizar_interface_aba()
            return

        self.aba_ativa = sigla
        for s, btn in self.tab_buttons.items():
            if s == sigla:
                btn.configure(fg_color="#1a6b1a", hover_color="#145214")
            else:
                btn.configure(fg_color="#2a2a2a", hover_color="#3a3a3a")

        self._atualizar_interface_aba()
        self._desenhar_skilltree()

    def _atualizar_interface_aba(self):
        aba = self.aba_ativa
        # Mostra/esconde botão Confirmar (à direita)
        if aba in self.abas_confirmadas or aba == "GERAL":
            self.btn_confirmar.pack_forget()
        else:
            self.btn_confirmar.pack(side="right", padx=5)
        pontos = self.pontos_skilltree.get(aba, 0)
        self.lbl_pontos.configure(text=f"Pontos em {aba}: {pontos}")

    def _todas_abas_confirmadas(self):
        return all(s in self.abas_confirmadas for s in ["AGI","FOR","INT","VIG","PRE"])

    def _confirmar_aba_atual(self):
        aba = self.aba_ativa
        if aba in self.abas_confirmadas or aba == "GERAL":
            return
        self.abas_confirmadas.append(aba)
        if self._todas_abas_confirmadas():
            pontos_geral = sum(self.pontos_skilltree[s] for s in ["AGI","FOR","INT","VIG","PRE"])
            self.pontos_skilltree["GERAL"] = pontos_geral
            self.tab_buttons["GERAL"].configure(state="normal")
        self._trocar_aba(aba)

    def _resetar_aba_ativa(self):
        aba = self.aba_ativa
        if aba in self.abas_confirmadas:
            self.abas_confirmadas.remove(aba)
            self.tab_buttons["GERAL"].configure(state="disabled")
            self.pontos_skilltree["GERAL"] = 0

        self.nos_comprados[aba] = []
        if aba != "GERAL":
            valor_attr = self.ficha_original.get("atributos", {}).get(aba, 1)
            self.pontos_skilltree[aba] = valor_attr * 2
        else:
            self.pontos_skilltree["GERAL"] = 0

        self._trocar_aba(aba)

    # ===============================================================
    # Desenho da árvore
    # ===============================================================
    def _desenhar_skilltree(self):

        self.canvas.delete("all")
        aba = self.aba_ativa

        if aba == "GERAL" and not self._todas_abas_confirmadas():
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()
            if w > 10 and h > 10:
                self.canvas.create_text(w//2, h//2, text="Confirme todas as árvores de atributo primeiro.",
                                        fill="#e67e22", font=("Arial", 14))
            self.canvas.configure(scrollregion=(0,0,w,h))
            return

        nos = self.skilltrees_data.get(aba, {}).get("nos", [])
        if not nos:
            return

        comprados = set(self.nos_comprados.get(aba, []))
        pontos = self.pontos_skilltree.get(aba, 0)

        posicoes_grid = calcular_posicoes(nos)
        no_r = 36
        padding = 5
        espaco = no_r*2 + padding
        margem = no_r + 10

        max_col = max(c for c, l in posicoes_grid.values()) if posicoes_grid else 0
        max_linha = max(l for c, l in posicoes_grid.values()) if posicoes_grid else 0
        canvas_w = max(margem*2 + espaco*(max_col+1), self.canvas.winfo_width())
        canvas_h = max(margem*2 + espaco*(max_linha+1), self.canvas.winfo_height())

        self.posicoes = {}
        for no_id, (col, linha) in posicoes_grid.items():
            self.posicoes[no_id] = (margem + espaco*col + no_r,
                                    margem + espaco*linha + no_r)

        self.canvas.configure(scrollregion=(0,0,canvas_w,canvas_h))

        # Linhas de requisito
        for no in nos:
            if no["id"] not in self.posicoes:
                continue
            x2, y2 = self.posicoes[no["id"]]
            for req in no["requisitos"]:
                if req in self.posicoes:
                    x1, y1 = self.posicoes[req]
                    cor = "#4a7a4a" if req in comprados else "#444444"
                    self.canvas.create_line(x1, y1, x2, y2, fill=cor, width=2)

        # Nós
        for no in nos:
            if no["id"] not in self.posicoes:
                continue
            x, y = self.posicoes[no["id"]]
            comprado = no["id"] in comprados
            disponivel = pode_comprar(no, comprados, pontos) if not comprado else False

            if comprado:
                cor_fill, cor_borda, cor_texto = "#7a6000", "#FFD700", "#FFD700"
            elif disponivel:
                cor_fill, cor_borda, cor_texto = "#1a4a1a", "#2ecc71", "#2ecc71"
            else:
                cor_fill, cor_borda, cor_texto = "#2b2b2b", "#555555", "#555555"

            self.canvas.create_oval(x-no_r, y-no_r, x+no_r, y+no_r,
                                    fill=cor_fill, outline=cor_borda, width=2,
                                    tags=(no["id"], "no"))
            nome_curto = no["nome"][:14] + "…" if len(no["nome"]) > 14 else no["nome"]
            self.canvas.create_text(x, y-8, text=nome_curto,
                                    fill=cor_texto, font=("Arial", 9, "bold"),
                                    width=no_r*1.8, tags=(no["id"], "no"))
            self.canvas.create_text(x, y+12, text=f"{no['custo']}pt",
                                    fill=cor_texto, font=("Arial", 8),
                                    tags=(no["id"], "no"))
            self.canvas.tag_bind(no["id"], "<Button-1>", lambda e, n=no: self._abrir_popup_no(n))

    def _abrir_popup_no(self, no):
        from utils.skilltree import pode_comprar, tem_filhos_comprados

        aba = self.aba_ativa
        comprados = set(self.nos_comprados.get(aba, []))
        pontos = self.pontos_skilltree.get(aba, 0)
        comprado = no["id"] in comprados

        popup = ctk.CTkToplevel(self.window)
        popup.title(no["nome"])
        popup.geometry("440x420")
        popup.resizable(False, False)
        popup.after(100, popup.grab_set)

        frame = ctk.CTkFrame(popup, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text=no["nome"], font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0,5))
        ctk.CTkLabel(frame, text=f"Custo: {no['custo']} ponto(s)", font=ctk.CTkFont(size=12), text_color="gray").pack()
        ctk.CTkLabel(frame, text=no["descricao"], font=ctk.CTkFont(size=12), wraplength=380, justify="left").pack(pady=(10,10))

        if no["requisitos"]:
            nos_por_id = {n["id"]: n for n in self.skilltrees_data[aba]["nos"]}
            nomes_req = [nos_por_id[r]["nome"] for r in no["requisitos"] if r in nos_por_id]
            ctk.CTkLabel(frame, text=f"Requer: {', '.join(nomes_req)}",
                         font=ctk.CTkFont(size=12), text_color="#e67e22").pack(pady=(0,10))

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20,0))

        if comprado:
            tem_filhos = tem_filhos_comprados(no["id"], self.skilltrees_data[aba]["nos"], comprados)
            if tem_filhos:
                ctk.CTkLabel(btn_frame, text="Não é possível vender: há habilidades dependentes.",
                             font=ctk.CTkFont(size=11), text_color="#e74c3c").pack()
            else:
                ctk.CTkButton(btn_frame, text=f"Vender (+{no['custo']} pt)",
                              fg_color="#8B0000", hover_color="#5a0000",
                              command=lambda: self._vender_no(no, popup)).pack(fill="x")
        else:
            disponivel = pode_comprar(no, comprados, pontos)
            if disponivel:
                ctk.CTkButton(btn_frame, text=f"Comprar (-{no['custo']} pt)",
                              fg_color="#1a6b1a", hover_color="#145214",
                              command=lambda: self._comprar_no(no, popup)).pack(fill="x")
            else:
                motivo = "Pontos insuficientes" if no["custo"] > pontos else "Requisitos não atendidos"
                ctk.CTkLabel(btn_frame, text=f"Não disponível: {motivo}",
                             font=ctk.CTkFont(size=12), text_color="#e74c3c").pack()

        ctk.CTkButton(frame, text="Fechar", fg_color="transparent", border_width=1,
                      command=popup.destroy).pack(pady=(10,0))

    def _comprar_no(self, no, popup):
        aba = self.aba_ativa
        self.nos_comprados[aba].append(no["id"])
        self.pontos_skilltree[aba] -= no["custo"]
        self._atualizar_interface_aba()  # Atualiza label de pontos
        popup.destroy()
        self._desenhar_skilltree()

    def _vender_no(self, no, popup):
        aba = self.aba_ativa
        self.nos_comprados[aba].remove(no["id"])
        self.pontos_skilltree[aba] += no["custo"]
        self._atualizar_interface_aba()
        popup.destroy()
        self._desenhar_skilltree()
