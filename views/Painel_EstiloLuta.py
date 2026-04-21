# views/Painel_EstiloLuta.py
import customtkinter as ctk
import uuid
from tkinter import messagebox
from views.EfeitosEditorFrame import EfeitosEditorFrame
from views.Efeitos_Popup import EfeitosPopup
from utils.helpers import formatar_numero_grande
from utils.estiloLuta import executar_estilo_luta

class PainelEstiloLuta(ctk.CTkFrame):
    """Aba: gerenciamento de habilidades de estilo de luta."""

    TIPO_MECANICA_OPCOES = ["Ataque", "Teste de Resistência", "Passiva"]

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

        ctk.CTkLabel(header, text="Estilos de Luta",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")

        btn_adicionar = ctk.CTkButton(
            header, text="➕ Nova Habilidade", width=160, height=30,
            font=ctk.CTkFont(size=12), fg_color="#1a5c1a", hover_color="#145214",
            command=self._abrir_popup_criacao
        )
        btn_adicionar.pack(side="right")

        # Lista de habilidades de estilo
        habilidades = self._ficha.setdefault("habilidades_estilo_luta", [])

        if not habilidades:
            ctk.CTkLabel(self, text="Nenhuma habilidade de estilo criada. Clique em 'Nova Habilidade' para começar.",
                         font=ctk.CTkFont(size=13), text_color="gray").pack(pady=40)
            return

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        for hab in habilidades:
            self._criar_card(scroll, hab)

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

    def _criar_card(self, parent, hab: dict):
        card = ctk.CTkFrame(parent, fg_color="#1e1e1e", corner_radius=8,
                            border_width=1, border_color="#333333")
        card.pack(fill="x", pady=4, padx=2)

        # Linha superior: Nome e Tipo Mecânica
        topo = ctk.CTkFrame(card, fg_color="transparent")
        topo.pack(fill="x", padx=12, pady=(10, 4))

        nome = hab.get("nome", "Sem nome")
        tipo_mec = hab.get("tipo_mecanica", "Ataque")
        ctk.CTkLabel(topo, text=nome, font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        ctk.CTkLabel(topo, text=f"[{tipo_mec}]", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="#3498db").pack(side="right")

        # Descrição resumida
        desc = hab.get("descricao", "")
        if desc:
            previa = (desc[:80] + "…") if len(desc) > 80 else desc
            ctk.CTkLabel(card, text=previa, wraplength=500, justify="left",
                         font=ctk.CTkFont(size=11),
                         text_color="#aaaaaa").pack(anchor="w", padx=12, pady=(0, 8))

        # Dano (se houver)
        params = hab.get("parametros", {})
        dano = params.get("dano", "")
        if dano:
            ctk.CTkLabel(card, text=f"Dano: {dano}", font=ctk.CTkFont(size=11),
                         text_color="#e67e22").pack(anchor="w", padx=12, pady=(0,4))

        # Efeitos configurados
        efeitos = hab.get("efeitos", [])
        if efeitos:
            ctk.CTkLabel(card, text=f"⚡ {len(efeitos)} efeito(s) configurado(s)",
                         font=ctk.CTkFont(size=10), text_color="#888888").pack(anchor="w", padx=12, pady=(0,4))

        # Botões de ação
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkButton(btn_frame, text="Editar", width=70, height=28,
                      font=ctk.CTkFont(size=11), fg_color="transparent",
                      border_width=1, border_color="#444444",
                      command=lambda: self._abrir_popup_edicao(hab)).pack(side="left", padx=(0, 5))

        if tipo_mec != "Passiva":
            ctk.CTkButton(btn_frame, text="Usar", width=70, height=28,
                          font=ctk.CTkFont(size=11), fg_color="#2a6b2a", hover_color="#1a4a1a",
                          command=lambda: self._executar_habilidade(hab)).pack(side="left", padx=5)
        else:
            # Controle de ativação para passivas
            hab_id = hab["id"]
            passivas_ativas = self._ficha.setdefault("passivas_ativas", {})
            ativa = hab_id in passivas_ativas
            var_ativa = ctk.BooleanVar(value=ativa)
            cb = ctk.CTkCheckBox(btn_frame, text="Ativar", variable=var_ativa,
                                 font=ctk.CTkFont(size=11),
                                 command=lambda: self._toggle_passiva(hab_id, var_ativa))
            cb.pack(side="left", padx=5)

        ctk.CTkButton(btn_frame, text="Remover", width=70, height=28,
                      font=ctk.CTkFont(size=11), fg_color="#8B0000",
                      hover_color="#5a0000",
                      command=lambda: self._remover_habilidade(hab)).pack(side="right")

    def _toggle_passiva(self, hab_id: str, var_ativa: ctk.BooleanVar):
        ativa = var_ativa.get()
        passivas = self._ficha.setdefault("passivas_ativas", {})
        if ativa:
            passivas[hab_id] = "BASE"
        else:
            passivas.pop(hab_id, None)
        if self._on_save:
            self._on_save()
        self._construir()

    # ──────────────────────────────────────────────────────────────────────────
    # Popup de Criação / Edição
    # ──────────────────────────────────────────────────────────────────────────

    def _abrir_popup_criacao(self):
        self._abrir_popup_edicao(None)

    def _abrir_popup_edicao(self, hab: dict = None):
        editando = hab is not None
        titulo = "Editar Habilidade" if editando else "Nova Habilidade de Estilo"

        popup = ctk.CTkToplevel(self.winfo_toplevel())
        popup.title(titulo)
        popup.geometry("650x750")
        popup.minsize(550, 600)
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
            e_nome.insert(0, hab.get("nome", ""))
        e_nome.pack(fill="x", pady=(2, 12))

        # Tipo Mecânica
        ctk.CTkLabel(main, text="Tipo Mecânica:", anchor="w").pack(fill="x")
        tipo_mec_var = ctk.StringVar(value=hab.get("tipo_mecanica", "Ataque") if editando else "Ataque")
        tipo_mec_menu = ctk.CTkOptionMenu(main, values=self.TIPO_MECANICA_OPCOES, variable=tipo_mec_var)
        tipo_mec_menu.pack(fill="x", pady=(2, 12))

        # Dano (fórmula)
        ctk.CTkLabel(main, text="Dano / Efeito (fórmula):", anchor="w").pack(fill="x")
        e_dano = ctk.CTkEntry(main, placeholder_text="ex: 4d6+12, 2d10+FOR")
        if editando and "dano" in hab.get("parametros", {}):
            e_dano.insert(0, hab["parametros"]["dano"])
        e_dano.pack(fill="x", pady=(2, 12))

        # Checkbox aplicar passo
        aplicar_passo_var = ctk.BooleanVar(value=hab.get("parametros", {}).get("aplicar_passo", False) if editando else False)
        cb_passo = ctk.CTkCheckBox(main, text="Aplicar bônus de Passo e Dados Extras", variable=aplicar_passo_var)
        cb_passo.pack(anchor="w", pady=(0, 12))

        # Descrição
        ctk.CTkLabel(main, text="Descrição / Efeito:", anchor="w").pack(fill="x")
        e_desc = ctk.CTkTextbox(main, height=100)
        if editando:
            e_desc.insert("1.0", hab.get("descricao", ""))
        e_desc.pack(fill="x", pady=(2, 12))

        # Efeitos (para passivas)
        efeitos_temp = list(hab.get("efeitos", [])) if editando else []

        def abrir_efeitos():
            nonlocal efeitos_temp
            popup_efeitos = EfeitosPopup(
                popup,
                efeitos_existentes=efeitos_temp,
                on_save=lambda novos: efeitos_temp.clear() or efeitos_temp.extend(novos)
            )
            popup_efeitos.abrir()

        efeitos_frame = EfeitosEditorFrame(
            main,
            efeitos_iniciais=efeitos_temp,
            on_change=lambda novos: efeitos_temp.clear() or efeitos_temp.extend(novos)
        )
        efeitos_frame.pack(fill="both", expand=True, pady=(10, 5))

        # Botões Salvar / Cancelar
        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))

        def salvar():
            nome = e_nome.get().strip()
            if not nome:
                messagebox.showwarning("Aviso", "O nome da habilidade é obrigatório.")
                return

            params = hab.get("parametros", {}) if editando else {}
            params["dano"] = e_dano.get().strip() or "0"
            params["aplicar_passo"] = aplicar_passo_var.get()

            nova_hab = {
                "id": hab.get("id") if editando else str(uuid.uuid4()),
                "nome": nome,
                "tipo_mecanica": tipo_mec_var.get(),
                "descricao": e_desc.get("1.0", "end-1c").strip(),
                "parametros": params,
                "efeitos": efeitos_temp
            }

            habilidades = self._ficha.setdefault("habilidades_estilo_luta", [])
            if editando:
                for i, h in enumerate(habilidades):
                    if h.get("id") == hab.get("id"):
                        habilidades[i] = nova_hab
                        break
            else:
                habilidades.append(nova_hab)

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

    def _executar_habilidade(self, hab: dict):
        resultado = executar_estilo_luta(hab, self._ficha)
        self._mostrar_resultado(resultado)

    def _mostrar_resultado(self, resultado: dict):
        popup = ctk.CTkToplevel(self.winfo_toplevel())
        popup.title("Resultado")
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

    def _remover_habilidade(self, hab: dict):
        if not messagebox.askyesno("Confirmar", f"Remover '{hab.get('nome', 'esta habilidade')}'?"):
            return

        habilidades = self._ficha.get("habilidades_estilo_luta", [])
        habilidades = [h for h in habilidades if h.get("id") != hab.get("id")]
        self._ficha["habilidades_estilo_luta"] = habilidades

        # Remove das passivas ativas se estiver lá
        passivas = self._ficha.get("passivas_ativas", {})
        if hab["id"] in passivas:
            del passivas[hab["id"]]

        if self._on_save:
            self._on_save()
        self._construir()

    def atualizar(self):
        self._construir()