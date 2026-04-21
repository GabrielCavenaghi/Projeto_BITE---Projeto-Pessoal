# views/EfeitosEditorFrame.py
import customtkinter as ctk
from tkinter import messagebox
from utils.Efeitos_Scalling import ALVOS_DISPONIVEIS, OPERACOES_PERMITIDAS, VARIAVEIS_BASE, string_para_tokens

class EfeitosEditorFrame(ctk.CTkFrame):
    """Componente embutível para gerenciar uma lista de efeitos (Scaling)."""

    def __init__(self, master, efeitos_iniciais=None, on_change=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.efeitos = list(efeitos_iniciais) if efeitos_iniciais else []
        self.on_change = on_change
        self._modo_edicao = False
        self._efeito_editando = None  # índice ou None
        self._construir()
        self._mostrar_lista()

    def _construir(self):
        # Container para o cabeçalho (fixo)
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(0, 5))

        self.lbl_titulo = ctk.CTkLabel(self.header_frame, text="Efeitos Passivos",
                                       font=ctk.CTkFont(weight="bold"))
        self.lbl_titulo.pack(side="left")

        self.btn_adicionar = ctk.CTkButton(self.header_frame, text="➕ Adicionar", width=100,
                                           command=self._iniciar_adicao)
        self.btn_adicionar.pack(side="right")

        # Frame dinâmico (lista ou formulário)
        self.conteudo_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.conteudo_frame.pack(fill="both", expand=True)

    # ──────────────────────────────────────────────────────────────────────────
    # Modo Lista
    # ──────────────────────────────────────────────────────────────────────────
    def _mostrar_lista(self):
        self._modo_edicao = False
        self._limpar_conteudo()

        self.lbl_titulo.configure(text="Efeitos Passivos")
        self.btn_adicionar.configure(text="➕ Adicionar", command=self._iniciar_adicao)

        if not self.efeitos:
            ctk.CTkLabel(self.conteudo_frame, text="Nenhum efeito adicionado.",
                         text_color="gray").pack(pady=20)
            return

        # Scroll para a lista
        scroll = ctk.CTkScrollableFrame(self.conteudo_frame, fg_color="transparent", height=200)
        scroll.pack(fill="both", expand=True)

        for i, efeito in enumerate(self.efeitos):
            self._criar_card_efeito(scroll, efeito, i)

    def _criar_card_efeito(self, parent, efeito: dict, index: int):
        alvo_nome = ALVOS_DISPONIVEIS.get(efeito["alvo"], {}).get("nome", efeito["alvo"])
        operacao = efeito["operacao"]
        formula_str = self._formula_para_string(efeito["formula"])

        card = ctk.CTkFrame(parent, fg_color="#2a2a2a", corner_radius=6)
        card.pack(fill="x", pady=2)

        info = f"{alvo_nome} {operacao} {formula_str}"
        ctk.CTkLabel(card, text=info, font=ctk.CTkFont(size=12),
                     anchor="w").pack(side="left", padx=10, pady=8, fill="x", expand=True)

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(side="right", padx=5)

        ctk.CTkButton(btn_frame, text="✎", width=30, height=30,
                      fg_color="transparent", hover_color="#3a3a3a",
                      command=lambda idx=index: self._iniciar_edicao(idx)).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="✕", width=30, height=30,
                      fg_color="transparent", hover_color="#3a3a3a",
                      command=lambda idx=index: self._remover_efeito(idx)).pack(side="left", padx=2)

    def _formula_para_string(self, formula: list) -> str:
        partes = []
        for token in formula:
            tipo = token["tipo"]
            if tipo == "constante":
                partes.append(str(token["valor"]))
            elif tipo == "variavel":
                partes.append(token["valor"])
            elif tipo == "operador":
                partes.append(f" {token['valor']} ")
            elif tipo == "expressao":
                partes.append(f"({self._formula_para_string(token['valor'])})")
        return "".join(partes)

    # ──────────────────────────────────────────────────────────────────────────
    # Modo Edição (Formulário)
    # ──────────────────────────────────────────────────────────────────────────
    def _iniciar_adicao(self):
        self._efeito_editando = None
        self._mostrar_formulario()

    def _iniciar_edicao(self, index):
        self._efeito_editando = index
        self._mostrar_formulario(self.efeitos[index])

    def _mostrar_formulario(self, efeito_existente=None):
        self._modo_edicao = True
        self._limpar_conteudo()

        self.lbl_titulo.configure(text="Editar Efeito" if efeito_existente else "Novo Efeito")
        self.btn_adicionar.configure(text="Voltar à Lista", command=self._mostrar_lista)

        # Categorias e alvos
        categorias = sorted(set(v['categoria'] for v in ALVOS_DISPONIVEIS.values()))
        alvos_por_categoria = {}
        for k, v in ALVOS_DISPONIVEIS.items():
            cat = v['categoria']
            alvos_por_categoria.setdefault(cat, []).append((k, v['nome']))

        ctk.CTkLabel(self.conteudo_frame, text="Categoria:", anchor="w").pack(fill="x", pady=(0,2))
        cat_var = ctk.StringVar()
        cat_menu = ctk.CTkOptionMenu(self.conteudo_frame, values=categorias, variable=cat_var,
                                     command=lambda _: atualizar_alvos())
        cat_menu.pack(fill="x", pady=(0,10))

        ctk.CTkLabel(self.conteudo_frame, text="Alvo:", anchor="w").pack(fill="x", pady=(0,2))
        alvo_var = ctk.StringVar()
        alvo_menu = ctk.CTkOptionMenu(self.conteudo_frame, values=[], variable=alvo_var)
        alvo_menu.pack(fill="x", pady=(0,10))

        def atualizar_alvos():
            cat = cat_var.get()
            alvos = alvos_por_categoria.get(cat, [])
            opcoes = [f"{nome} ({k})" for k, nome in alvos]
            alvo_menu.configure(values=opcoes)
            if opcoes:
                alvo_var.set(opcoes[0])

        # Operação
        ctk.CTkLabel(self.conteudo_frame, text="Operação:", anchor="w").pack(fill="x", pady=(0,2))
        op_var = ctk.StringVar(value="+")
        op_menu = ctk.CTkOptionMenu(self.conteudo_frame, values=OPERACOES_PERMITIDAS, variable=op_var)
        op_menu.pack(fill="x", pady=(0,10))

        # Fórmula
        ctk.CTkLabel(self.conteudo_frame, text="Fórmula (expressão):", anchor="w").pack(fill="x", pady=(0,2))
        formula_entry = ctk.CTkEntry(self.conteudo_frame, placeholder_text="ex: LP*2+10, AB/2")
        formula_entry.pack(fill="x", pady=(0,5))

        vars_label = ctk.CTkLabel(self.conteudo_frame, text="Variáveis: " + ", ".join(VARIAVEIS_BASE),
                                  font=ctk.CTkFont(size=11), text_color="#888888")
        vars_label.pack(anchor="w", pady=(0,15))

        # Preencher se edição
        if efeito_existente:
            alvo_key = efeito_existente["alvo"]
            if alvo_key in ALVOS_DISPONIVEIS:
                cat_alvo = ALVOS_DISPONIVEIS[alvo_key]['categoria']
                cat_var.set(cat_alvo)
                atualizar_alvos()
                nome_alvo = ALVOS_DISPONIVEIS[alvo_key]['nome']
                alvo_var.set(f"{nome_alvo} ({alvo_key})")
            else:
                cat_var.set(categorias[0])
                atualizar_alvos()
            op_var.set(efeito_existente.get("operacao", "+"))
            formula_entry.insert(0, self._formula_para_string(efeito_existente.get("formula", [])))
        else:
            cat_var.set(categorias[0])
            atualizar_alvos()

        # Botões Salvar/Cancelar
        btn_frame = ctk.CTkFrame(self.conteudo_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10,0))

        def salvar_efeito():
            sel = alvo_var.get()
            if not sel:
                messagebox.showerror("Erro", "Selecione um alvo.")
                return
            alvo_key = sel.split('(')[-1].rstrip(')')
            if alvo_key not in ALVOS_DISPONIVEIS:
                messagebox.showerror("Erro", "Alvo inválido.")
                return

            operacao = op_var.get()
            formula_str = formula_entry.get().strip()
            if not formula_str:
                messagebox.showerror("Erro", "A fórmula não pode estar vazia.")
                return

            try:
                formula_tokens = string_para_tokens(formula_str)
            except ValueError as e:
                messagebox.showerror("Erro de sintaxe", str(e))
                return

            novo_efeito = {
                "alvo": alvo_key,
                "operacao": operacao,
                "formula": formula_tokens
            }

            if self._efeito_editando is not None:
                self.efeitos[self._efeito_editando] = novo_efeito
            else:
                self.efeitos.append(novo_efeito)

            if self.on_change:
                self.on_change(self.efeitos)

            self._mostrar_lista()

        ctk.CTkButton(btn_frame, text="Aplicar", fg_color="#1a6b1a", hover_color="#145214",
                      command=salvar_efeito).pack(side="right", padx=(5,0))
        ctk.CTkButton(btn_frame, text="Cancelar", fg_color="transparent", border_width=1,
                      command=self._mostrar_lista).pack(side="right")

    # ──────────────────────────────────────────────────────────────────────────
    # Remoção
    # ──────────────────────────────────────────────────────────────────────────
    def _remover_efeito(self, index: int):
        if not messagebox.askyesno("Confirmar", "Remover este efeito?"):
            return
        del self.efeitos[index]
        if self.on_change:
            self.on_change(self.efeitos)
        self._mostrar_lista()

    # ──────────────────────────────────────────────────────────────────────────
    # Utilitários
    # ──────────────────────────────────────────────────────────────────────────
    def _limpar_conteudo(self):
        for w in self.conteudo_frame.winfo_children():
            w.destroy()

    def get_efeitos(self):
        return self.efeitos