# views/Painel_Combate.py
import customtkinter as ctk
import uuid
from tkinter import messagebox
from utils.combate import executar_ataque_personalizado
from utils.dados import avaliar_dado_str
from utils.helpers import formatar_numero_grande

class PainelCombate(ctk.CTkFrame):
    """Aba: gerenciamento de ataques (armas, corpo a corpo, etc.)."""

    TIPO_EFEITO_OPCOES = ["tecnica", "corpo", "desarmado", "invocacao", "maldicao", "shinobi", "estilo_luta", "energia_amaldicoada"]
    TIPO_EFEITO_NOMES = {
        "tecnica": "Técnica",
        "corpo": "Corpo a Corpo",
        "desarmado": "Desarmado",
        "invocacao": "Invocação",
        "maldicao": "Maldição",
        "shinobi": "Shinobi",
        "estilo_luta": "Estilo de Luta",
        "energia_amaldicoada": "Energia Amaldiçoada"
    }

    def __init__(self, parent, ficha: dict, on_save=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._ficha = ficha
        self._on_save = on_save
        self._pericias_disponiveis = self._obter_pericias()
        self._construir()

    def _obter_pericias(self):
        """Retorna a lista de nomes de perícias disponíveis na ficha."""
        pericias = self._ficha.get("pericias", {})
        return list(pericias.keys())

    def _construir(self):
        for w in self.winfo_children():
            w.destroy()

        # Cabeçalho
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(5, 10))

        ctk.CTkLabel(header, text="Ataques e Combate",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")

        btn_adicionar = ctk.CTkButton(
            header, text="➕ Novo Ataque", width=140, height=30,
            font=ctk.CTkFont(size=12), fg_color="#1a5c1a", hover_color="#145214",
            command=self._abrir_popup_criacao
        )
        btn_adicionar.pack(side="right")

        # Lista de ataques
        ataques = self._ficha.setdefault("ataques_personalizados", [])

        if not ataques:
            ctk.CTkLabel(self, text="Nenhum ataque criado. Clique em 'Novo Ataque' para começar.",
                         font=ctk.CTkFont(size=13), text_color="gray").pack(pady=40)
            return

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        for ataque in ataques:
            self._criar_card(scroll, ataque)

        self._aplicar_scroll(scroll)

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

    def _criar_card(self, parent, ataque: dict):
        card = ctk.CTkFrame(parent, fg_color="#1e1e1e", corner_radius=8,
                            border_width=1, border_color="#333333")
        card.pack(fill="x", pady=4, padx=2)

        # Linha superior: Nome e Perícia
        topo = ctk.CTkFrame(card, fg_color="transparent")
        topo.pack(fill="x", padx=12, pady=(10, 4))

        nome = ataque.get("nome", "Sem nome")
        pericia = ataque.get("pericia", "Luta")
        ctk.CTkLabel(topo, text=nome,
             font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")

        tipo_efeito = ataque.get("tipo_efeito", "corpo")
        tipo_nome = self.TIPO_EFEITO_NOMES.get(tipo_efeito, tipo_efeito)
        ctk.CTkLabel(topo, text=f"[{tipo_nome}]",
                     font=ctk.CTkFont(size=11), text_color="#888888").pack(side="right")

        # Linha: Dano e Crítico
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(fill="x", padx=12, pady=(0, 4))

        dano = ataque.get("dano", "1d6")
        margem = ataque.get("margem_ameaca", 20)
        mult = ataque.get("multiplicador_critico", 2)
        aplicar_passo = "Passo: Sim" if ataque.get("aplicar_passo", False) else "Passo: Não"

        ctk.CTkLabel(info_frame, text=f"Dano: {dano}  |  Crítico: {margem}/x{mult}  |  {aplicar_passo}",
                     font=ctk.CTkFont(size=11), text_color="#aaaaaa").pack(side="left")

        # Botões de ação
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkButton(btn_frame, text="Editar", width=70, height=28,
                      font=ctk.CTkFont(size=11), fg_color="transparent",
                      border_width=1, border_color="#444444",
                      command=lambda: self._abrir_popup_edicao(ataque)).pack(side="left", padx=(0, 5))

        ctk.CTkButton(btn_frame, text="Atacar", width=70, height=28,
                      font=ctk.CTkFont(size=11), fg_color="#2a6b2a", hover_color="#1a4a1a",
                      command=lambda: self._executar_ataque(ataque)).pack(side="left", padx=5)

        ctk.CTkButton(btn_frame, text="Remover", width=70, height=28,
                      font=ctk.CTkFont(size=11), fg_color="#8B0000",
                      hover_color="#5a0000",
                      command=lambda: self._remover_ataque(ataque)).pack(side="right")

    # ──────────────────────────────────────────────────────────────────────────
    # Popup de Criação / Edição
    # ──────────────────────────────────────────────────────────────────────────

    def _abrir_popup_criacao(self):
        self._abrir_popup_edicao(None)

    def _abrir_popup_edicao(self, ataque: dict = None):
        editando = ataque is not None
        titulo = "Editar Ataque" if editando else "Novo Ataque"

        popup = ctk.CTkToplevel(self.winfo_toplevel())
        popup.title(titulo)
        popup.minsize(500, 500)
        popup.resizable(True, True)
        # Centraliza na tela
        popup.after(10, lambda: popup.geometry(
            f"{min(700, popup.winfo_screenwidth()-100)}x{min(800, popup.winfo_screenheight()-100)}"
        ))

        scroll = ctk.CTkScrollableFrame(popup, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(20, 10))

        main = ctk.CTkFrame(scroll, fg_color="transparent")
        main.pack(fill="both", expand=True)

        ctk.CTkLabel(main, text=titulo, font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 15))

        # Nome
        ctk.CTkLabel(main, text="Nome do Ataque:", anchor="w").pack(fill="x")
        e_nome = ctk.CTkEntry(main)
        if editando:
            e_nome.insert(0, ataque.get("nome", ""))
        e_nome.pack(fill="x", pady=(2, 12))

        # Dano (fórmula)
        ctk.CTkLabel(main, text="Dano (fórmula):", anchor="w").pack(fill="x")
        e_dano = ctk.CTkEntry(main, placeholder_text="ex: 2d6+FOR, 1d8+AGI")
        if editando:
            e_dano.insert(0, ataque.get("dano", ""))
        e_dano.pack(fill="x", pady=(2, 12))

        # Substitua o OptionMenu de tipo único por checkboxes
        ctk.CTkLabel(main, text="Tipos de Dano (pode combinar):", anchor="w").pack(fill="x")
        tipos_vars = {}
        tipos_frame = ctk.CTkFrame(main, fg_color="transparent")
        tipos_frame.pack(fill="x", pady=(2, 12))

        tipos_selecionados = ataque.get("tipos_efeito", [ataque.get("tipo_efeito", "corpo")]) if editando else ["corpo"]

        for chave, nome in self.TIPO_EFEITO_NOMES.items():
            var = ctk.BooleanVar(value=chave in tipos_selecionados)
            cb = ctk.CTkCheckBox(tipos_frame, text=nome, variable=var)
            cb.pack(anchor="w", pady=1)
            tipos_vars[chave] = var

        # Checkbox aplicar passo
        aplicar_passo_var = ctk.BooleanVar(value=ataque.get("aplicar_passo", False) if editando else False)
        cb_passo = ctk.CTkCheckBox(main, text="Aplicar bônus de Passo e Dados Extras", variable=aplicar_passo_var)
        cb_passo.pack(anchor="w", pady=(0, 12))

        # Linha Margem / Multiplicador
        row_crit = ctk.CTkFrame(main, fg_color="transparent")
        row_crit.pack(fill="x", pady=(0, 12))
        row_crit.columnconfigure(0, weight=1)
        row_crit.columnconfigure(1, weight=1)

        ctk.CTkLabel(row_crit, text="Margem de Ameaça:", anchor="w").grid(row=0, column=0, sticky="w", padx=(0,5))
        e_margem = ctk.CTkEntry(row_crit, placeholder_text="20")
        if editando:
            e_margem.insert(0, str(ataque.get("margem_ameaca", 20)))
        else:
            e_margem.insert(0, "20")
        e_margem.grid(row=1, column=0, sticky="ew", padx=(0,5))

        ctk.CTkLabel(row_crit, text="Multiplicador Crítico:", anchor="w").grid(row=0, column=1, sticky="w", padx=(5,0))
        e_mult = ctk.CTkEntry(row_crit, placeholder_text="2")
        if editando:
            e_mult.insert(0, str(ataque.get("multiplicador_critico", 2)))
        else:
            e_mult.insert(0, "2")
        e_mult.grid(row=1, column=1, sticky="ew", padx=(5,0))

        # Perícia Base
        ctk.CTkLabel(main, text="Perícia de Ataque:", anchor="w").pack(fill="x")
        pericia_var = ctk.StringVar()
        if self._pericias_disponiveis:
            pericia_menu = ctk.CTkOptionMenu(main, values=self._pericias_disponiveis, variable=pericia_var)
            if editando:
                pericia_var.set(ataque.get("pericia", "Luta"))
            else:
                pericia_var.set("Luta" if "Luta" in self._pericias_disponiveis else self._pericias_disponiveis[0])
        else:
            pericia_menu = ctk.CTkOptionMenu(main, values=["Luta"], variable=pericia_var)
            pericia_var.set("Luta")
        pericia_menu.pack(fill="x", pady=(2, 20))

        # Botões Salvar / Cancelar
        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))

        def salvar():
            nome = e_nome.get().strip()
            nome = e_nome.get().strip()
            if not nome:
                messagebox.showwarning("Aviso", "O nome do ataque é obrigatório.")
                return

            tipos_efeito = [chave for chave, var in tipos_vars.items() if var.get()]
            if not tipos_efeito:
                tipos_efeito = ["corpo"]  # fallback

            try:
                margem = int(e_margem.get())
            except:
                margem = 20
            try:
                mult = int(e_mult.get())
            except:
                mult = 2
            
            
            novo_ataque = {
                "id": ataque.get("id") if editando else str(uuid.uuid4()),
                "nome": nome,
                "dano": e_dano.get().strip() or "1d6",
                "tipos_efeito": tipos_efeito,
                "tipo_efeito": tipos_efeito[0],
                "aplicar_passo": aplicar_passo_var.get(),
                "margem_ameaca": margem,
                "multiplicador_critico": mult,
                "pericia": pericia_var.get(),
            }

            ataques = self._ficha.setdefault("ataques_personalizados", [])
            if editando:
                for i, a in enumerate(ataques):
                    if a.get("id") == ataque.get("id"):
                        ataques[i] = novo_ataque
                        break
            else:
                ataques.append(novo_ataque)

            if self._on_save:
                self._on_save()
            popup.destroy()
            self._construir()

        ctk.CTkButton(btn_frame, text="Salvar", fg_color="#1a6b1a", hover_color="#145214",
                      command=salvar).pack(side="right", padx=(5,0))
        ctk.CTkButton(btn_frame, text="Cancelar", fg_color="transparent", border_width=1,
                      command=popup.destroy).pack(side="right")

    # ──────────────────────────────────────────────────────────────────────────
    # Execução e Resultado
    # ──────────────────────────────────────────────────────────────────────────

    def _executar_ataque(self, ataque: dict):
        """Executa a rolagem de ataque usando o módulo de combate."""
        resultado = executar_ataque_personalizado(self._ficha, ataque)
        self._mostrar_resultado(resultado)

    def _mostrar_resultado(self, resultado: dict):
        popup = ctk.CTkToplevel(self.winfo_toplevel())
        popup.title("Resultado do Ataque")
        popup.geometry("450x350")
        popup.after(100, popup.grab_set)

        main = ctk.CTkFrame(popup, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=20)

        dano = resultado.get("detalhes", {}).get("dano", 0)
        texto = resultado.get("mensagem", "")

        if dano and dano > 9999:
            dano_formatado = formatar_numero_grande(dano)
            texto = texto.replace(str(dano), dano_formatado)
            mostrar_botao_exato = True
        else:
            mostrar_botao_exato = False

        ctk.CTkLabel(main, text=texto, wraplength=400, justify="left",
                     font=ctk.CTkFont(size=13)).pack(anchor="w", pady=(0, 20))

        if mostrar_botao_exato:
            def mostrar_exato():
                messagebox.showinfo("Valor exato", f"{dano:,}".replace(',', '.'))
            ctk.CTkButton(main, text="Ver valor exato", command=mostrar_exato,
                          fg_color="transparent", border_width=1).pack(pady=(0,10))

        ctk.CTkButton(main, text="Fechar", command=popup.destroy).pack()

    # ──────────────────────────────────────────────────────────────────────────
    # Remoção
    # ──────────────────────────────────────────────────────────────────────────

    def _remover_ataque(self, ataque: dict):
        if not messagebox.askyesno("Confirmar", f"Remover '{ataque.get('nome', 'este ataque')}'?"):
            return

        ataques = self._ficha.get("ataques_personalizados", [])
        ataques = [a for a in ataques if a.get("id") != ataque.get("id")]
        self._ficha["ataques_personalizados"] = ataques

        if self._on_save:
            self._on_save()
        self._construir()

    def atualizar(self):
        self._pericias_disponiveis = self._obter_pericias()
        self._construir()