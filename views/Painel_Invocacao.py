# views/Painel_Invocacao.py
import os, json
import customtkinter as ctk
import uuid
from tkinter import messagebox
from ficha import construir_contexto_base
from utils.invocacao import executar_ataque_invocacao as executar_atq_inv
from views.EfeitosEditorFrame import EfeitosEditorFrame
from utils.dados import avaliar_dado_str
from utils.helpers import formatar_numero_grande

class PainelInvocacao(ctk.CTkFrame):
    """Aba: gerenciamento de invocações (summons)."""

    ATRIBUTOS = ["AGI", "FOR", "INT", "VIG", "PRE"]
    GRAUS = [
        "Grau 4", "Grau 3", "Grau 2", "Grau 1",
        "Grau Semi Especial", "Grau Especial", "Grau Ultra Especial"
    ]

    def __init__(self, parent, ficha: dict, on_save=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._ficha = ficha
        self._on_save = on_save
        self._construir()

    def _construir(self):
        for w in self.winfo_children():
            w.destroy()

        # Cabeçalho
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(5, 10))

        ctk.CTkLabel(header, text="Invocações",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")

        btn_adicionar = ctk.CTkButton(
            header, text="➕ Nova Invocação", width=150, height=30,
            font=ctk.CTkFont(size=12), fg_color="#1a5c1a", hover_color="#145214",
            command=self._abrir_popup_criacao
        )
        btn_adicionar.pack(side="right")

        invocacoes = self._ficha.setdefault("invocacoes", [])
        if not invocacoes:
            ctk.CTkLabel(self, text="Nenhuma invocação criada.",
                         font=ctk.CTkFont(size=13), text_color="gray").pack(pady=40)
            return

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        for inv in invocacoes:
            self._criar_card(scroll, inv)

        self._aplicar_scroll(scroll)

    # Métodos de scroll (iguaise)
    def _aplicar_scroll(self, scroll):
        def _scroll(delta):
            scroll._parent_canvas.yview_scroll(delta, "units")

        def _on_mousewheel(event):
            delta = -1 if event.delta > 0 else 1
            _scroll(delta)

        def _on_button4(event):
            _scroll(-1)

        def _on_button5(event):
            _scroll(1)

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



    def _criar_card(self, parent, inv: dict):
        card = ctk.CTkFrame(parent, fg_color="#1e1e1e", corner_radius=8,
                            border_width=1, border_color="#333333")
        card.pack(fill="x", pady=4, padx=2)

        # ── Linha superior: Nome e Grau ──
        topo = ctk.CTkFrame(card, fg_color="transparent")
        topo.pack(fill="x", padx=12, pady=(10, 4))

        nome = inv.get("nome", "Sem nome")
        grau = inv.get("grau", "Grau 4")
        ctk.CTkLabel(topo, text=f"{nome} ({grau})",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")

        # ── Atributos resumidos ──
        attr = inv.get("atributos", {})
        attr_str = ", ".join(f"{sigla}: {attr.get(sigla, 0)}" for sigla in self.ATRIBUTOS)
        ctk.CTkLabel(card, text=attr_str, font=ctk.CTkFont(size=11),
                     text_color="#aaaaaa").pack(anchor="w", padx=12, pady=(0,4))

        # ── Ataque principal (fórmula) ──
        atq = inv.get("ataque_principal", {})
        dano = atq.get("dano", "")
        if dano:
            ctk.CTkLabel(card, text=f"Ataque: {dano}", font=ctk.CTkFont(size=11),
                         text_color="#e67e22").pack(anchor="w", padx=12, pady=(0,4))

        # ── Barra de vida interativa ──
        pv_atual = inv.get("pv_atual", 0)
        pv_max = inv.get("pv_maximo", 100)

        vida_outer = ctk.CTkFrame(card, fg_color="transparent")
        vida_outer.pack(fill="x", padx=12, pady=(4, 4))

        # Label com números (ex.: "120/150")
        lbl_pv = ctk.CTkLabel(vida_outer, text=f"PV: {pv_atual}/{pv_max}",
                              font=ctk.CTkFont(size=11), text_color="#f1c40f")
        lbl_pv.pack(side="left", padx=(0, 8))

        # Barra de progresso
        barra_pv = ctk.CTkProgressBar(vida_outer, width=150, height=12,
                                      fg_color="#333333", progress_color="#2ecc71")
        barra_pv.pack(side="left")
        barra_pv.set(pv_atual / pv_max if pv_max > 0 else 0)

        # Entry para valor de ajuste
        e_ajuste = ctk.CTkEntry(card, width=60, height=24,
                                font=ctk.CTkFont(size=11),
                                placeholder_text="0")
        e_ajuste.pack(padx=12, pady=(4,2), anchor="w")

        # Botões de ajuste
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=(0, 8))

        btn_menos_pv = ctk.CTkButton(btn_frame, text="−", width=30, height=24,
                                     fg_color="#8B0000", hover_color="#5a0000",
                                     command=lambda: self._ajustar_pv_invocacao(inv, -1, e_ajuste, lbl_pv, barra_pv))
        btn_menos_pv.pack(side="left", padx=2)

        btn_mais_pv = ctk.CTkButton(btn_frame, text="+", width=30, height=24,
                                    fg_color="#1a5c1a", hover_color="#145214",
                                    command=lambda: self._ajustar_pv_invocacao(inv, 1, e_ajuste, lbl_pv, barra_pv))
        btn_mais_pv.pack(side="left", padx=2)

        # ── Botões de ação (Usar Ataque, Abrir Ficha, Remover) ──
        botoes_frame = ctk.CTkFrame(card, fg_color="transparent")
        botoes_frame.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkButton(botoes_frame, text="Usar Ataque", width=90, height=28,
                      font=ctk.CTkFont(size=11), fg_color="#2a6b2a", hover_color="#1a4a1a",
                      command=lambda: self._executar_ataque_invocacao(inv)).pack(side="left")

        ctk.CTkButton(botoes_frame, text="Abrir Ficha", width=80, height=28,
                      font=ctk.CTkFont(size=11), fg_color="#1a5c1a",
                      command=lambda: self._abrir_ficha_completa(inv)).pack(side="right", padx=(2,0))
        ctk.CTkButton(botoes_frame, text="Remover", width=70, height=28,
                      font=ctk.CTkFont(size=11), fg_color="#8B0000",
                      hover_color="#5a0000",
                      command=lambda: self._remover_invocacao(inv)).pack(side="right", padx=2)

    # ── Método auxiliar para ajustar PV (agora também atualiza a barra) ──
    def _ajustar_pv_invocacao(self, inv: dict, sinal: int, entry_widget, lbl_pv: ctk.CTkLabel, barra_pv: ctk.CTkProgressBar):
        """
        Ajusta o PV atual da invocação com o valor da entry.
        sinal = +1 para aumentar, -1 para diminuir.
        """
        texto = entry_widget.get().strip()
        if not texto:
            return

        try:
            valor = int(texto)
        except ValueError:
            return

        if valor <= 0:
            return

        delta = valor * sinal
        pv_atual = inv.get("pv_atual", 0)
        pv_max = inv.get("pv_maximo", 100)

        novo_pv = pv_atual + delta
        novo_pv = max(0, min(novo_pv, pv_max))

        inv["pv_atual"] = novo_pv
        lbl_pv.configure(text=f"PV: {novo_pv}/{pv_max}")
        barra_pv.set(novo_pv / pv_max if pv_max > 0 else 0)

        if self._on_save:
            self._on_save()


    def _executar_ataque_invocacao(self, inv: dict):
        resultado = executar_atq_inv(inv, inv.get("ataque_principal", {}), self._ficha)
        self._mostrar_resultado(self, resultado)

        
    # ======================== POPUP DE CRIAÇÃO / EDIÇÃO =========================
    def _abrir_popup_criacao(self):
        self._abrir_popup_edicao(None)

    def _abrir_popup_edicao(self, inv: dict = None):
        editando = inv is not None
        titulo = "Editar Invocação" if editando else "Nova Invocação"

        popup = ctk.CTkToplevel(self.winfo_toplevel())
        popup.title(titulo)
        popup.geometry("600x800")
        popup.minsize(550, 700)
        popup.resizable(False, False)
        popup.after(100, popup.grab_set)

        scroll = ctk.CTkScrollableFrame(popup, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(20, 10))

        main = ctk.CTkFrame(scroll, fg_color="transparent")
        main.pack(fill="both", expand=True)

        ctk.CTkLabel(main, text=titulo, font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0,15))

        # Nome
        ctk.CTkLabel(main, text="Nome:", anchor="w").pack(fill="x")
        e_nome = ctk.CTkEntry(main)
        if editando:
            e_nome.insert(0, inv.get("nome", ""))
        e_nome.pack(fill="x", pady=(2, 12))

        # Grau
        ctk.CTkLabel(main, text="Grau:", anchor="w").pack(fill="x")
        grau_var = ctk.StringVar(value=inv.get("grau", "Grau 4") if editando else "Grau 4")
        grau_menu = ctk.CTkOptionMenu(main, values=self.GRAUS, variable=grau_var)

        # Perícia Base (do invocador)
        ctk.CTkLabel(main, text="Perícia Base (do invocador):", anchor="w").pack(fill="x", pady=(12,2))
        pericias_invocador = list(self._ficha.get("pericias", {}).keys())
        pericia_base_var = ctk.StringVar(value=inv.get("pericia_base", "Luta") if editando else "Luta")
        if pericias_invocador:
            pericia_menu = ctk.CTkOptionMenu(main, values=pericias_invocador, variable=pericia_base_var)
        else:
            pericia_menu = ctk.CTkOptionMenu(main, values=["Luta"], variable=pericia_base_var)
        pericia_menu.pack(fill="x", pady=(2, 12))
        grau_menu.pack(fill="x", pady=(2, 12))

        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        caminho_invoc = os.path.join(base_dir, "data", "invocacoes.json")
        with open(caminho_invoc, "r", encoding="utf-8") as f:
            dados_invoc = json.load(f)["graus"]

        def obter_dados_grau(grau_nome: str):
            return dados_invoc.get(grau_nome, dados_invoc["Grau 4"])

        dados_grau_atual = obter_dados_grau(grau_var.get())

        # ══════════════════════════════════════════════════════════════════════
        # Informações do grau (pontos de atributo e máximo)
        # ══════════════════════════════════════════════════════════════════════
        pontos_total = dados_grau_atual["pontos_atributo"]
        max_por_atrib = dados_grau_atual["maximo_atributo"]

        # Calcula pontos já gastos (se editando, soma dos atributos atuais)
        if editando:
            attr_atuais = inv.get("atributos", {})
            # Pontos gastos = soma dos valores que excedem 1 em cada atributo
            pontos_gastos = sum(max(0, attr_atuais.get(s, 1) - 1) for s in self.ATRIBUTOS)
        else:
            pontos_gastos = 0  # todos começam com 1, nada gasto ainda

        pontos_restantes = pontos_total - pontos_gastos

        # Label que mostra pontos disponíveis
        lbl_pontos = ctk.CTkLabel(main, text=f"Pontos de Atributo: {pontos_restantes}/{pontos_total}  |  Máximo por atributo: {max_por_atrib}",
                                  font=ctk.CTkFont(size=12, weight="bold"), text_color="#f1c40f")
        lbl_pontos.pack(anchor="w", pady=(5, 10))

        # ══════════════════════════════════════════════════════════════════════
        # Atributos (agora com botões +/-)
        # ══════════════════════════════════════════════════════════════════════
        attr_vars = {}  # guarda IntVar para cada atributo

        def atualizar_label_pontos():
            # Gasto é a soma de (valor - 1) para cada atributo, nunca negativo
            gastos = sum(max(0, var.get() - 1) for var in attr_vars.values())
            restantes = pontos_total - gastos
            lbl_pontos.configure(
                text=f"Pontos para distribuir: {restantes}/{pontos_total}  |  Máximo por atributo: {max_por_atrib}"
            )

        for sigla in self.ATRIBUTOS:
            row = ctk.CTkFrame(main, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=sigla, width=30).pack(side="left")

            valor_inicial = inv.get("atributos", {}).get(sigla, 0) if editando else 1
            var = ctk.IntVar(value=valor_inicial)
            attr_vars[sigla] = var

            # Botão -
            btn_menos = ctk.CTkButton(row, text="−", width=28, height=28,
                                      fg_color="#2a2a2a", hover_color="#3a3a3a")
            btn_menos.pack(side="left", padx=2)

            # Label do valor
            lbl_valor = ctk.CTkLabel(row, textvariable=var, width=30, font=ctk.CTkFont(size=14, weight="bold"))
            lbl_valor.pack(side="left", padx=4)

            # Botão +
            btn_mais = ctk.CTkButton(row, text="+", width=28, height=28,
                                      fg_color="#2a2a2a", hover_color="#3a3a3a")
            btn_mais.pack(side="left", padx=2)

            # Comandos dos botões (capturam sigla e var corretamente)
            def fazer_diminuir(s=sigla, v=var):
                if v.get() > 0:   
                    v.set(v.get() - 1)
                    atualizar_label_pontos()

            def fazer_aumentar(s=sigla, v=var):
                # Verifica se ainda há pontos disponíveis e se não atingiu o máximo por atributo
                gastos = sum(max(0, x.get() - 1) for x in attr_vars.values())
                if v.get() < max_por_atrib and gastos < pontos_total:
                    v.set(v.get() + 1)
                    atualizar_label_pontos()

            btn_menos.configure(command=fazer_diminuir)
            btn_mais.configure(command=fazer_aumentar)

        # Atualiza a label uma vez
        atualizar_label_pontos()

        # ══════════════════════════════════════════════════════════════════════
        # Quando o grau mudar, recarregar dados e reiniciar atributos
        # ══════════════════════════════════════════════════════════════════════
        def ao_mudar_grau(*args):
            nonlocal dados_grau_atual, pontos_total, max_por_atrib, pontos_restantes
            dados_grau_atual = obter_dados_grau(grau_var.get())
            pontos_total = dados_grau_atual["pontos_atributo"]
            max_por_atrib = dados_grau_atual["maximo_atributo"]
            # Reseta todos os atributos para 1
            for var in attr_vars.values():
                var.set(1)
            atualizar_label_pontos()
            # Atualiza dano base se estiver no modo base
            if dano_tipo_var.get() == "base":
                e_atq_dano.configure(state="normal")
                e_atq_dano.delete(0, "end")
                e_atq_dano.insert(0, dados_grau_atual["dano_base"])
                e_atq_dano.configure(state="disabled")

        grau_var.trace_add("write", ao_mudar_grau)

        # Fórmula de PV
        ctk.CTkLabel(main, text="Cálculo de PV:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(15,2))
        pv_tipo_var = ctk.StringVar(value="auto" if not editando or inv.get("pv_formula") == "auto" else "custom")
        ctk.CTkRadioButton(main, text="Automático (VIG * 100)", variable=pv_tipo_var, value="auto").pack(anchor="w")
        ctk.CTkRadioButton(main, text="Fórmula customizada", variable=pv_tipo_var, value="custom").pack(anchor="w")

        e_pv_formula = ctk.CTkEntry(main, placeholder_text="VIG * 1000 + NEX * LP_NATURAL + EA")
        if editando and inv.get("pv_formula") not in (None, "auto"):
            e_pv_formula.insert(0, inv.get("pv_formula", ""))
        e_pv_formula.pack(fill="x", pady=(2, 12))

        def toggle_pv_formula(*args):
            if pv_tipo_var.get() == "custom":
                e_pv_formula.configure(state="normal")
            else:
                e_pv_formula.configure(state="disabled")
        pv_tipo_var.trace_add("write", toggle_pv_formula)
        toggle_pv_formula()

        # Ataque Principal
        ctk.CTkLabel(main, text="Ataque Principal:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(15,5))

        # Tipo
        ctk.CTkLabel(main, text="Tipo:").pack(anchor="w")
        tipo_mec_options = ["Ataque", "Teste de Resistência"]
        tipo_mec_var = ctk.StringVar(value=inv.get("ataque_principal", {}).get("tipo_mecanica", "Ataque") if editando else "Ataque")
        tipo_mec_menu = ctk.CTkOptionMenu(main, values=tipo_mec_options, variable=tipo_mec_var)
        tipo_mec_menu.pack(fill="x", pady=(2,10))

        # Dano Base / Custom
        dano_tipo_var = ctk.StringVar(value="base" if not editando else "custom")
        ctk.CTkRadioButton(main, text="Dano Base do Grau", variable=dano_tipo_var, value="base").pack(anchor="w")
        ctk.CTkRadioButton(main, text="Dano Customizado", variable=dano_tipo_var, value="custom").pack(anchor="w")

        e_atq_dano = ctk.CTkEntry(main, placeholder_text="2d10+FOR")
        if editando:
            e_atq_dano.insert(0, inv.get("ataque_principal", {}).get("dano", ""))
        else:
            e_atq_dano.insert(0, dados_grau_atual["dano_base"])
        e_atq_dano.pack(fill="x", pady=(2,6))

        def toggle_dano_formula(*args):
            if dano_tipo_var.get() == "base":
                e_atq_dano.delete(0, "end")
                e_atq_dano.insert(0, dados_grau_atual["dano_base"])
                e_atq_dano.configure(state="disabled")
            else:
                e_atq_dano.configure(state="normal")
        dano_tipo_var.trace_add("write", toggle_dano_formula)
        toggle_dano_formula()

        # Checkbox aplicar passo
        atq_passo_var = ctk.BooleanVar(value=inv.get("ataque_principal", {}).get("aplicar_passo", False) if editando else False)
        ctk.CTkCheckBox(main, text="Aplicar Passo de Invocação", variable=atq_passo_var).pack(anchor="w", pady=(2,8))

        # Frame para configurações de Ataque (margem, multiplicador) – visível só se tipo "Ataque"
        frame_atq_extra = ctk.CTkFrame(main, fg_color="transparent")
        frame_atq_extra.pack(fill="x", pady=(0, 12))

        row_crit = ctk.CTkFrame(frame_atq_extra, fg_color="transparent")
        row_crit.pack(fill="x")
        row_crit.columnconfigure(0, weight=1)
        row_crit.columnconfigure(1, weight=1)

        ctk.CTkLabel(row_crit, text="Margem de Ameaça:", anchor="w").grid(row=0, column=0, sticky="w", padx=(0,5))
        e_margem_inv = ctk.CTkEntry(row_crit, placeholder_text="20")
        if editando:
            e_margem_inv.insert(0, str(inv.get("ataque_principal", {}).get("margem_ameaca", 20)))
        else:
            e_margem_inv.insert(0, "20")
        e_margem_inv.grid(row=1, column=0, sticky="ew", padx=(0,5))

        ctk.CTkLabel(row_crit, text="Mult. Crítico:", anchor="w").grid(row=0, column=1, sticky="w", padx=(5,0))
        e_mult_inv = ctk.CTkEntry(row_crit, placeholder_text="2")
        if editando:
            e_mult_inv.insert(0, str(inv.get("ataque_principal", {}).get("multiplicador_critico", 2)))
        else:
            e_mult_inv.insert(0, "2")
        e_mult_inv.grid(row=1, column=1, sticky="ew", padx=(5,0))

        def toggle_frame_atq(*args):
            if tipo_mec_var.get() == "Ataque":
                frame_atq_extra.pack(fill="x", pady=(0, 12))
            else:
                frame_atq_extra.pack_forget()
        tipo_mec_var.trace_add("write", toggle_frame_atq)
        toggle_frame_atq()

        # Botões Salvar/Cancelar
        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))

        def salvar():
            nome = e_nome.get().strip()
            if not nome:
                messagebox.showwarning("Aviso", "O nome da invocação é obrigatório.")
                return

            novos_attr = {sigla: var.get() for sigla, var in attr_vars.items()}

            pv_formula = pv_tipo_var.get()
            if pv_formula == "custom":
                pv_formula = e_pv_formula.get().strip() or "auto"

            if pv_formula == "auto":
                pv_maximo = self._calcular_pv_por_grau(grau_var.get(), novos_attr)
            else:
                pv_maximo = self._calcular_pv_custom(pv_formula, novos_attr)
            pv_atual = pv_maximo

            ataque_principal = {
                "dano": e_atq_dano.get().strip() or "1d6",
                "aplicar_passo": atq_passo_var.get(),
                "tipo_mecanica": tipo_mec_var.get(),
                "tipo_efeito": "invocacao"
            }
            if tipo_mec_var.get() == "Ataque":
                try:
                    ataque_principal["margem_ameaca"] = int(e_margem_inv.get())
                except:
                    ataque_principal["margem_ameaca"] = 20
                try:
                    ataque_principal["multiplicador_critico"] = int(e_mult_inv.get())
                except:
                    ataque_principal["multiplicador_critico"] = 2
            nova_inv = {
                "id": inv.get("id") if editando else str(uuid.uuid4()),
                "nome": nome,
                "grau": grau_var.get(),
                "atributos": novos_attr,
                "pericia_base": pericia_base_var.get(),
                "pv_formula": pv_formula,
                "pv_maximo": pv_maximo,
                "pv_atual": pv_atual if not editando else inv.get("pv_atual", pv_atual),
                "ataque_principal": ataque_principal,
                "ataques_secundarios": inv.get("ataques_secundarios", []) if editando else []
            }

            invocacoes = self._ficha.setdefault("invocacoes", [])
            if editando:
                for i, inv_existente in enumerate(invocacoes):
                    if inv_existente.get("id") == inv.get("id"):
                        invocacoes[i] = nova_inv
                        break
            else:
                invocacoes.append(nova_inv)

            if self._on_save:
                self._on_save()
            popup.destroy()
            self._construir()

        ctk.CTkButton(btn_frame, text="Salvar", fg_color="#1a6b1a", command=salvar).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Cancelar", fg_color="transparent", border_width=1,
                      command=popup.destroy).pack(side="right")
    def _calcular_pv_por_grau(self, grau: str, atributos_invoc: dict) -> int:
        with open("data/invocacoes.json", "r") as f:
            dados = json.load(f)["graus"][grau]
        
        vig = atributos_invoc.get("VIG", 0)
        ctx = construir_contexto_base(self._ficha)
        dt = ctx.get("DT_BASE", 10)      # ou DT_TECNICA?
        lp = ctx.get("LP", 1)
        
        # Substitui VIG, DT, LP na fórmula
        formula = dados["vida_formula"]
        # Avalia a fórmula (similar ao que já fazemos)
        from utils.Efeitos_Scalling import string_para_tokens
        from ficha import avaliar_formula
        # Monta contexto local
        ctx_local = {"VIG": vig, "DT": dt, "LP": lp}
        tokens = string_para_tokens(formula)
        pv = int(avaliar_formula(tokens, ctx_local))
        
        # Adiciona bônus extra por Vigor
        bonus_vig = dados["vida_bonus_por_vig"] * vig
        return pv + bonus_vig

    def _calcular_pv_custom(self, formula_str: str, attr_invoc: dict) -> int:
        """Avalia fórmula customizada usando atributos da invocação + contexto do personagem."""
        from ficha import construir_contexto_base
        ctx = construir_contexto_base(self._ficha)
        # Adiciona atributos da invocação ao contexto (com prefixo ou diretamente? usar sigla)
        for sigla, val in attr_invoc.items():
            ctx[sigla] = val
        from utils.Efeitos_Scalling import string_para_tokens
        from ficha import avaliar_formula
        try:
            tokens = string_para_tokens(formula_str)
            return int(avaliar_formula(tokens, ctx))
        except Exception as e:
            print(f"Erro ao calcular PV custom: {e}")
            return 100

    # ======================== GERENCIAMENTO RÁPIDO =========================

    def _mostrar_resultado(self, parent, resultado: dict):
        popup = ctk.CTkToplevel(parent)
        popup.title("Resultado")
        popup.geometry("400x300")
        popup.after(100, popup.grab_set)

        main = ctk.CTkFrame(popup, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=20)

        dano = resultado.get("detalhes", {}).get("dano", 0)
        texto = resultado.get("mensagem", "")
        if dano and dano > 9999:
            dano_formatado = formatar_numero_grande(dano)
            texto = texto.replace(str(dano), dano_formatado)

        ctk.CTkLabel(main, text=texto, wraplength=350, justify="left").pack(anchor="w", pady=(0,20))
        ctk.CTkButton(main, text="Fechar", command=popup.destroy).pack()

    # ======================== ABRIR FICHA COMPLETA =========================
    def _abrir_ficha_completa(self, inv: dict):
        from views.Tela_Invocacao import TelaInvocacao
        TelaInvocacao(self.winfo_toplevel(), inv, self._ficha, on_save=self._on_save)

    # ======================== REMOÇÃO =========================
    def _remover_invocacao(self, inv: dict):
        if not messagebox.askyesno("Confirmar", f"Remover '{inv.get('nome')}'?"):
            return
        invocacoes = self._ficha.get("invocacoes", [])
        invocacoes = [i for i in invocacoes if i.get("id") != inv.get("id")]
        self._ficha["invocacoes"] = invocacoes
        if self._on_save:
            self._on_save()
        self._construir()

    def atualizar(self):
        self._construir()