# views/Efeitos_Popup.py
import customtkinter as ctk
from tkinter import messagebox
from utils.Efeitos_Scalling import ALVOS_DISPONIVEIS, OPERACOES_PERMITIDAS, VARIAVEIS_BASE, string_para_tokens
class EfeitosPopup:
    """
    Popup reutilizável para gerenciar uma lista de efeitos passivos.
    Pode ser usado por habilidades, técnicas, itens, etc.
    """

    def __init__(self, parent, efeitos_existentes=None, on_save=None):
        """
        Args:
            parent: widget pai (janela principal ou popup)
            efeitos_existentes (list): lista de efeitos já definidos (opcional)
            on_save (callable): função chamada ao confirmar, recebendo a lista final de efeitos
        """
        self.parent = parent
        self.efeitos = list(efeitos_existentes) if efeitos_existentes else []
        self.on_save = on_save
        self.window = None
        self.lista_frame = None

    def abrir(self):
        """Cria e exibe a janela modal."""
        self.window = ctk.CTkToplevel(self.parent)
        self.window.title("Gerenciar Efeitos")
        self.window.geometry("600x500")
        self.window.minsize(500, 400)
        self.window.resizable(False, False)
        self.window.after(100, self.window.grab_set)

        self._construir_interface()
        self._atualizar_lista()

    def _construir_interface(self):
        """Monta a estrutura básica da janela."""
        # Frame principal
        main = ctk.CTkFrame(self.window, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=20)

        # Título
        ctk.CTkLabel(main, text="Efeitos Passivos",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 10))

        # Área da lista (scrollable)
        self.lista_frame = ctk.CTkScrollableFrame(main, fg_color="transparent")
        self.lista_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Botões de ação
        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.pack(fill="x")

        ctk.CTkButton(btn_frame, text="➕ Adicionar Efeito",
                      command=self._abrir_editor_efeito).pack(side="left", padx=(0, 5))
        ctk.CTkButton(btn_frame, text="Salvar", fg_color="#1a6b1a", hover_color="#145214",
                      command=self._salvar).pack(side="right", padx=(5, 0))
        ctk.CTkButton(btn_frame, text="Cancelar", fg_color="transparent", border_width=1,
                      command=self.window.destroy).pack(side="right")

    def _atualizar_lista(self):
        """Recria a exibição da lista de efeitos."""
        for w in self.lista_frame.winfo_children():
            w.destroy()

        if not self.efeitos:
            ctk.CTkLabel(self.lista_frame, text="Nenhum efeito adicionado.",
                         font=ctk.CTkFont(size=12), text_color="gray").pack(pady=20)
            return

        for i, efeito in enumerate(self.efeitos):
            self._criar_card_efeito(efeito, i)

    def _criar_card_efeito(self, efeito: dict, index: int):
        """Cria um card representando um efeito na lista."""
        alvo_nome = ALVOS_DISPONIVEIS.get(efeito["alvo"], {}).get("nome", efeito["alvo"])
        operacao = efeito["operacao"]
        formula_str = self._formula_para_string(efeito["formula"])

        card = ctk.CTkFrame(self.lista_frame, fg_color="#2a2a2a", corner_radius=6)
        card.pack(fill="x", pady=2)

        info = f"{alvo_nome} {operacao} {formula_str}"
        ctk.CTkLabel(card, text=info, font=ctk.CTkFont(size=12),
                     anchor="w").pack(side="left", padx=10, pady=8, fill="x", expand=True)

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(side="right", padx=5)

        ctk.CTkButton(btn_frame, text="✎", width=30, height=30,
                      font=ctk.CTkFont(size=14), fg_color="transparent",
                      hover_color="#3a3a3a",
                      command=lambda idx=index: self._abrir_editor_efeito(idx)).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="✕", width=30, height=30,
                      font=ctk.CTkFont(size=14), fg_color="transparent",
                      hover_color="#3a3a3a",
                      command=lambda idx=index: self._remover_efeito(idx)).pack(side="left", padx=2)

    def _formula_para_string(self, formula: list) -> str:
        """Converte uma fórmula (lista de tokens) em uma string legível (simplificada)."""
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

    def _abrir_editor_efeito(self, index=None):
        editando = index is not None
        efeito_atual = self.efeitos[index] if editando else {}

        popup = ctk.CTkToplevel(self.window)
        popup.title("Editar Efeito" if editando else "Novo Efeito")
        popup.geometry("500x400")
        popup.resizable(False, False)
        popup.after(100, popup.grab_set)

        main = ctk.CTkFrame(popup, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=20)

        # ══════════════════════════════════════════════════════════════════════
        # Categorias e alvos
        # ══════════════════════════════════════════════════════════════════════
        categorias = sorted(set(v['categoria'] for v in ALVOS_DISPONIVEIS.values()))
        alvos_por_categoria = {}
        for k, v in ALVOS_DISPONIVEIS.items():
            cat = v['categoria']
            alvos_por_categoria.setdefault(cat, []).append((k, v['nome']))

        # Categoria
        ctk.CTkLabel(main, text="Categoria:", anchor="w").pack(fill="x")
        cat_var = ctk.StringVar()
        cat_menu = ctk.CTkOptionMenu(main, values=categorias, variable=cat_var,
                                     command=lambda _: atualizar_alvos())
        cat_menu.pack(fill="x", pady=(2, 12))

        # Alvo
        ctk.CTkLabel(main, text="Alvo:", anchor="w").pack(fill="x")
        alvo_var = ctk.StringVar()
        alvo_menu = ctk.CTkOptionMenu(main, values=[], variable=alvo_var)
        alvo_menu.pack(fill="x", pady=(2, 12))

        def atualizar_alvos():
            cat = cat_var.get()
            alvos = alvos_por_categoria.get(cat, [])
            opcoes = [f"{nome} ({k})" for k, nome in alvos]
            alvo_menu.configure(values=opcoes)
            if opcoes:
                alvo_var.set(opcoes[0])

        # Se estiver editando, pré-seleciona categoria e alvo
        if editando:
            alvo_key = efeito_atual.get("alvo", "")
            if alvo_key in ALVOS_DISPONIVEIS:
                cat_alvo = ALVOS_DISPONIVEIS[alvo_key]['categoria']
                cat_var.set(cat_alvo)
                atualizar_alvos()
                # Seleciona o item correto no dropdown de alvos
                nome_alvo = ALVOS_DISPONIVEIS[alvo_key]['nome']
                alvo_var.set(f"{nome_alvo} ({alvo_key})")
            else:
                cat_var.set(categorias[0])
                atualizar_alvos()
        else:
            cat_var.set(categorias[0])
            atualizar_alvos()

        # ══════════════════════════════════════════════════════════════════════
        # Operação
        # ══════════════════════════════════════════════════════════════════════
        ctk.CTkLabel(main, text="Operação:", anchor="w").pack(fill="x")
        op_var = ctk.StringVar(value=efeito_atual.get("operacao", "+") if editando else "+")
        op_menu = ctk.CTkOptionMenu(main, values=OPERACOES_PERMITIDAS, variable=op_var)
        op_menu.pack(fill="x", pady=(2, 12))

        # ══════════════════════════════════════════════════════════════════════
        # Fórmula
        # ══════════════════════════════════════════════════════════════════════
        ctk.CTkLabel(main, text="Fórmula (expressão):", anchor="w").pack(fill="x")
        formula_entry = ctk.CTkEntry(main, placeholder_text="ex: LP*2+10, AB/2")
        if editando:
            formula_entry.insert(0, self._formula_para_string(efeito_atual.get("formula", [])))
        formula_entry.pack(fill="x", pady=(2, 12))

        ctk.CTkLabel(main, text="Use variáveis: " + ", ".join(VARIAVEIS_BASE),
                     font=ctk.CTkFont(size=11), text_color="#888888").pack(anchor="w")

        # ══════════════════════════════════════════════════════════════════════
        # Botões
        # ══════════════════════════════════════════════════════════════════════
        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 0))

        def salvar_efeito():
            # Extrai a chave do alvo a partir da string selecionada
            sel = alvo_var.get()
            if not sel:
                messagebox.showerror("Erro", "Selecione um alvo.")
                return
            # O formato é "Nome (CHAVE)"
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

            if editando:
                self.efeitos[index] = novo_efeito
            else:
                self.efeitos.append(novo_efeito)

            popup.destroy()
            self._atualizar_lista()

        ctk.CTkButton(btn_frame, text="Salvar", fg_color="#1a6b1a", hover_color="#145214",
                      command=salvar_efeito).pack(side="right", padx=(5, 0))
        ctk.CTkButton(btn_frame, text="Cancelar", fg_color="transparent", border_width=1,
                      command=popup.destroy).pack(side="right")

    def _remover_efeito(self, index: int):
        """Remove um efeito da lista após confirmação."""
        if not messagebox.askyesno("Confirmar", "Remover este efeito?"):
            return
        del self.efeitos[index]
        self._atualizar_lista()

    def _salvar(self):
        """Fecha a janela e chama o callback on_save com a lista final de efeitos."""
        if self.on_save:
            self.on_save(self.efeitos)
        self.window.destroy()