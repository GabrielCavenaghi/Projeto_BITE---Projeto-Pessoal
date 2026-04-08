import customtkinter as ctk
import json
import os
import datetime
import random

# ══════════════════════════════════════════════════════════════════════════════
# Funções auxiliares para manipulação de atributos (edição na ficha)
# ══════════════════════════════════════════════════════════════════════════════

LIMITE_NORMAL = 13
LIMITE_ABSOLUTO = 14

def rolar_atributo(valor_atributo: int, treinamento: int = 0, bonus: int = 0) -> dict:
    """
    Rola dados conforme o valor do atributo:
    - Se atributo == 0: rola 2d20 e pega o menor (desvantagem).
    - Se atributo > 0: rola (valor) d20 e pega o maior (vantagem).
    Retorna um dicionário com:
        'dados': lista dos valores rolados,
        'escolhido': valor selecionado (maior/menor),
        'total': valor escolhido + treinamento + bonus
    """
    if valor_atributo == 0:
        dados = [random.randint(1, 20) for _ in range(2)]
        escolhido = min(dados)
    else:
        dados = [random.randint(1, 20) for _ in range(valor_atributo)]
        escolhido = max(dados)

    total = escolhido + treinamento + bonus
    return {
        "dados": dados,
        "escolhido": escolhido,
        "treinamento": treinamento,
        "bonus": bonus,
        "total": total
    }

def calcular_pontos_disponiveis_ficha(ficha: dict) -> int:
    # Total de pontos que o personagem tem direito
    totais = ficha.get("totais_nex", {})
    total_disponivel = 4 + totais.get("pontos_atributo", 0) + ficha.get("pontos_extras_temp", 0)

    # Calcula quantos pontos já foram efetivamente gastos (baseado nos valores atuais)
    atributos = ficha.get("atributos", {})
    soma_atributos = sum(atributos.values())
    gastos_reais = max(0, soma_atributos - 5)   # cada atributo começa com 1

    pontos_restantes = total_disponivel - gastos_reais
    return max(0, pontos_restantes)

# ══════════════════════════════════════════════════════════════════════════════
# Definição padrão das perícias
# ══════════════════════════════════════════════════════════════════════════════
PERICIAS_PADRAO = {
    "Acrobacia": {"atributo_base": "AGI"},
    "Adestramento": {"atributo_base": "PRE"},
    "Artes": {"atributo_base": "PRE"},
    "Atletismo": {"atributo_base": "FOR"},
    "Atualidades": {"atributo_base": "INT"},
    "Ciencias": {"atributo_base": "INT"},
    "Crime": {"atributo_base": "AGI"},
    "Diplomacia": {"atributo_base": "PRE"},
    "Enganação": {"atributo_base": "PRE"},
    "Fortitude": {"atributo_base": "VIG"},
    "Furtividade": {"atributo_base": "AGI"},
    "Iniciativa": {"atributo_base": "AGI"},
    "Intimidação": {"atributo_base": "PRE"},
    "Intuição": {"atributo_base": "PRE"},
    "Investigação": {"atributo_base": "INT"},
    "Luta": {"atributo_base": "FOR"},
    "Medicina": {"atributo_base": "INT"},
    "Ocultismo": {"atributo_base": "INT"},
    "Percepção": {"atributo_base": "PRE"},
    "Pilotagem": {"atributo_base": "AGI"},
    "Pontaria": {"atributo_base": "AGI"},
    "Profissão": {"atributo_base": "INT"},
    "Energia Amaldiçoada": {"atributo_base": "PRE"},
    "Reflexos": {"atributo_base": "AGI"},
    "Religião": {"atributo_base": "PRE"},
    "Sobrevivência": {"atributo_base": "INT"},
    "Tática": {"atributo_base": "INT"},
    "Tecnologia": {"atributo_base": "INT"},
    "Vontade": {"atributo_base": "PRE"}
}

# ══════════════════════════════════════════════════════════════════════════════
# Normalização — garante retrocompatibilidade com fichas antigas
# ══════════════════════════════════════════════════════════════════════════════

def normalizar_ficha(ficha: dict) -> dict:
    """
    Preenche campos ausentes com defaults seguros.
    Fichas criadas antes da v2 continuam funcionando normalmente.
    """
    lp = ficha.get("lp", 0) or 0

    ficha.setdefault("atualizado_em", ficha.get("criado_em", ""))
    ficha.setdefault("pontos_atributo_gastos", 0)
    ficha.setdefault("pontos_atributo_gastos", 0)
    ficha.setdefault("pontos_extras_temp", 0)

    # Garante que 'atributos' exista com os valores base
    if "atributos" not in ficha:
        ficha["atributos"] = {
            "AGI": 1, "FOR": 1, "INT": 1, "VIG": 1, "PRE": 1
        }

    # Estado de sessão (PV, Sanidade, PE)
    if "estado" not in ficha:
        ficha["estado"] = {
            "pv_atual":   lp,
            "pv_maximo":  lp,
            "san_atual":  lp,
            "san_maximo": lp,
            "pe_atual":   ficha.get("totais_nex", {}).get("feiticos", 0),
            "pe_maximo":  ficha.get("totais_nex", {}).get("feiticos", 0),
        }
    else:
        ficha["estado"].setdefault("pv_atual",   lp)
        ficha["estado"].setdefault("pv_maximo",  lp)
        ficha["estado"].setdefault("san_atual",  lp)
        ficha["estado"].setdefault("san_maximo", lp)
        ficha["estado"].setdefault("pe_atual",   0)
        ficha["estado"].setdefault("pe_maximo",  0)

    # Combate
    ficha.setdefault("estilo_luta", {
        "id": None, "nome": None, "descricao": None,
        "origem": "padrao", "efeito": None,
    })
    ficha.setdefault("tecnica", {
        "id": None, "nome": None, "descricao": None,
        "origem": "padrao", "efeito": None,
    })
    ficha.setdefault("feiticos_custom", [])

    # Inventário
    ficha.setdefault("inventario", {"dinheiro": 0, "itens": []})

    # Anotações
    ficha.setdefault("anotacoes", "")
    ficha.setdefault("historico_sessoes", [])

    ficha.setdefault("passivas_ativas", {})   # ex: {"fei_004": "ESPECIAL", "fei_016": "GRAU 1"}
    ficha.setdefault("bonus_passivos", {})    # será preenchido dinamicamente

    # ══════════════════════════════════════════════════════════════════════════
    # Perícias
    # ══════════════════════════════════════════════════════════════════════════
    if "pericias" not in ficha:
        ficha["pericias"] = {}
        for nome, info in PERICIAS_PADRAO.items():
            ficha["pericias"][nome] = {
                "atributo_base": info["atributo_base"],
                "atributo_override": None,
                "treinamento": 0,
                "bonus": 0
            }
    else:
        # Garante que todas as perícias existam (caso alguma tenha sido removida)
        for nome, info in PERICIAS_PADRAO.items():
            if nome not in ficha["pericias"]:
                ficha["pericias"][nome] = {
                    "atributo_base": info["atributo_base"],
                    "atributo_override": None,
                    "treinamento": 0,
                    "bonus": 0
                }
            else:
                # Garante campos obrigatórios
                ficha["pericias"][nome].setdefault("atributo_base", info["atributo_base"])
                ficha["pericias"][nome].setdefault("atributo_override", None)
                ficha["pericias"][nome].setdefault("treinamento", 0)
                ficha["pericias"][nome].setdefault("bonus", 0)

    return ficha


def salvar_ficha(ficha: dict):
    """Sobrescreve o .json da ficha no disco e atualiza atualizado_em."""
    caminho = ficha.get("_arquivo")
    if not caminho:
        return
    ficha["atualizado_em"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    dados = {k: v for k, v in ficha.items() if k != "_arquivo"}
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def avaliar_formula(formula: list, contexto: dict) -> float:
    """
    Avalia uma fórmula em notação infixa (lista de tokens).
    Suporta operadores +, -, *, /, // e parênteses via token "expressao".
    """
    # Precedência dos operadores
    precedencia = {'+': 1, '-': 1, '*': 2, '/': 2, '//': 2}

    # Pilhas para o algoritmo Shunting-yard
    saida = []
    operadores = []

    def aplicar_operador(op, a, b):
        if op == '+': return a + b
        if op == '-': return a - b
        if op == '*': return a * b
        if op == '/': return a / b if b != 0 else 0
        if op == '//': return a // b if b != 0 else 0
        raise ValueError(f"Operador desconhecido: {op}")

    i = 0
    while i < len(formula):
        token = formula[i]
        tipo = token["tipo"]

        if tipo == "constante":
            saida.append(token["valor"])
        elif tipo == "variavel":
            nome = token["valor"]
            if nome not in contexto:
                raise KeyError(f"Variável '{nome}' não encontrada.")
            saida.append(contexto[nome])
        elif tipo == "operador":
            op = token["valor"]
            while (operadores and operadores[-1] != '(' and
                   precedencia.get(operadores[-1], 0) >= precedencia.get(op, 0)):
                saida.append(operadores.pop())
            operadores.append(op)
        elif tipo == "expressao":
            # Avalia a subexpressão recursivamente e empilha como valor
            sub_valor = avaliar_formula(token["valor"], contexto)
            saida.append(sub_valor)
        else:
            raise ValueError(f"Tipo de token desconhecido: {tipo}")
        i += 1

    # Despeja operadores restantes
    while operadores:
        saida.append(operadores.pop())

    # Avalia a notação RPN gerada
    pilha = []
    for item in saida:
        if isinstance(item, (int, float)):
            pilha.append(item)
        elif item in precedencia:
            if len(pilha) < 2:
                raise ValueError("Operador sem operandos suficientes.")
            b = pilha.pop()
            a = pilha.pop()
            pilha.append(aplicar_operador(item, a, b))
        else:
            raise ValueError(f"Elemento inesperado na saída RPN: {item}")

    return pilha[0] if pilha else 0

def construir_contexto_base(ficha: dict) -> dict:
    atributos = ficha.get("atributos", {})
    estado = ficha.get("estado", {})
    totais_nex = ficha.get("totais_nex", {})
    grau_str = ficha.get("grau", "Grau 4")
    grau_num = 0
    if "Grau" in grau_str and "Semi" not in grau_str and "Especial" not in grau_str:
        try:
            grau_num = int(grau_str.split()[1])
        except:
            pass
    elif "Semi" in grau_str:
        grau_num = 5
    elif "Ultra" in grau_str:
        grau_num = 7
    elif "Especial" in grau_str:
        grau_num = 6

    nex_str = ficha.get("nex", "5%").replace("%", "")
    try:
        nex_valor = float(nex_str)
    except:
        nex_valor = 5.0

    contexto = {
        "LP": ficha.get("lp", 1),
        "AB": atributos.get("INT", 1),   # ou atributo relevante?
        "GRAU": grau_num,
        "NEX": nex_valor,
        "AGI": atributos.get("AGI", 1),
        "FOR": atributos.get("FOR", 1),
        "INT": atributos.get("INT", 1),
        "VIG": atributos.get("VIG", 1),
        "PRE": atributos.get("PRE", 1),
        # Outras variáveis podem ser adicionadas conforme necessidade
    }
    return contexto

# ══════════════════════════════════════════════════════════════════════════════
# Widget: BarraRecurso (PV / Sanidade / PE)
# ══════════════════════════════════════════════════════════════════════════════

class BarraRecurso(ctk.CTkFrame):
    """
    Barra de recurso reutilizável.
    Layout: label + fração  |  barra de progresso  |  [−] [entrada] [+]  [máx]
    on_change(novo_atual) é chamado após cada alteração.
    """

    def __init__(self, parent, label: str, atual: int, maximo: int,
                 cor_barra: str, on_change=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self._atual     = atual
        self._maximo    = maximo
        self._on_change = on_change

        # Linha superior: nome + fracção
        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.pack(fill="x")

        ctk.CTkLabel(topo, text=label,
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#cccccc").pack(side="left")

        self._lbl_fracao = ctk.CTkLabel(topo, text=self._texto_fracao(),
                                        font=ctk.CTkFont(size=12),
                                        text_color="#888888")
        self._lbl_fracao.pack(side="right")

        # Barra visual
        self._barra = ctk.CTkProgressBar(self, height=8, corner_radius=4,
                                         progress_color=cor_barra,
                                         fg_color="#2a2a2a")
        self._barra.pack(fill="x", pady=(4, 6))
        self._atualizar_barra()

        # Controles: − | entrada | + | máx
        controles = ctk.CTkFrame(self, fg_color="transparent")
        controles.pack(fill="x")

        ctk.CTkButton(controles, text="−", width=36, height=30,
                      font=ctk.CTkFont(size=18),
                      fg_color="#2a2a2a", hover_color="#3a3a3a",
                      command=self._decrementar).pack(side="left")

        self._entrada = ctk.CTkEntry(controles, width=70, height=30,
                                     justify="center",
                                     font=ctk.CTkFont(size=14, weight="bold"))
        self._entrada.insert(0, str(self._atual))
        self._entrada.pack(side="left", padx=6)
        self._entrada.bind("<Return>",   self._ao_confirmar_entrada)
        self._entrada.bind("<FocusOut>", self._ao_confirmar_entrada)

        ctk.CTkButton(controles, text="+", width=36, height=30,
                      font=ctk.CTkFont(size=18),
                      fg_color="#2a2a2a", hover_color="#3a3a3a",
                      command=self._incrementar).pack(side="left")

        ctk.CTkButton(controles, text="máx", width=46, height=30,
                      font=ctk.CTkFont(size=11),
                      fg_color="transparent", border_width=1,
                      border_color="#444444", text_color="#888888",
                      command=self._editar_maximo).pack(side="right")

    # ── Helpers internos ──────────────────────────────────────────────────────

    def _texto_fracao(self) -> str:
        return f"{self._atual} / {self._maximo}"

    def _atualizar_barra(self):
        prog = max(0.0, min(1.0, self._atual / self._maximo)) if self._maximo > 0 else 0.0
        self._barra.set(prog)

    def _atualizar_ui(self):
        self._lbl_fracao.configure(text=self._texto_fracao())
        self._atualizar_barra()
        self._entrada.delete(0, "end")
        self._entrada.insert(0, str(self._atual))
        if self._on_change:
            self._on_change(self._atual)

    # ── Ações ─────────────────────────────────────────────────────────────────

    def _decrementar(self):
        self._atual = max(0, self._atual - 1)
        self._atualizar_ui()

    def _incrementar(self):
        self._atual = min(self._maximo, self._atual + 1)
        self._atualizar_ui()

    def _ao_confirmar_entrada(self, _event=None):
        try:
            valor = int(self._entrada.get())
            self._atual = max(0, min(self._maximo, valor))
        except ValueError:
            pass
        self._atualizar_ui()

    def _editar_maximo(self):
        popup = ctk.CTkToplevel(self.winfo_toplevel())
        popup.title("Editar máximo")
        popup.geometry("280x150")
        popup.resizable(False, False)
        popup.after(100, popup.grab_set)

        ctk.CTkLabel(popup, text="Novo valor máximo:",
                     font=ctk.CTkFont(size=13)).pack(pady=(20, 6))

        entrada = ctk.CTkEntry(popup, width=100, justify="center",
                               font=ctk.CTkFont(size=14))
        entrada.insert(0, str(self._maximo))
        entrada.pack()
        entrada.focus()

        def confirmar():
            try:
                novo = int(entrada.get())
                if novo >= 0:
                    self._maximo = novo
                    self._atual  = min(self._atual, self._maximo)
                    self._atualizar_ui()
            except ValueError:
                pass
            popup.destroy()

        entrada.bind("<Return>", lambda _: confirmar())
        ctk.CTkButton(popup, text="Confirmar", command=confirmar).pack(pady=12)

    # ── API pública ───────────────────────────────────────────────────────────

    def get_atual(self) -> int:
        return self._atual

    def get_maximo(self) -> int:
        return self._maximo

    def set_valores(self, atual: int, maximo: int):
        self._atual  = atual
        self._maximo = maximo
        self._atualizar_ui()


# ══════════════════════════════════════════════════════════════════════════════
# Painéis das abas
# ══════════════════════════════════════════════════════════════════════════════

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

class PainelSkilltree(ctk.CTkFrame):
    """Aba: nós de skill tree comprados, agrupados por atributo, com detalhes ao clicar."""

    CAMINHO_SKILLTREE = "data/skilltrees.json"

    CORES = {
        "AGI": "#e67e22", "FOR": "#e74c3c", "INT": "#3498db",
        "VIG": "#2ecc71", "PRE": "#9b59b6", "GERAL": "#95a5a6",
    }

    def __init__(self, parent, ficha: dict, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._ficha = ficha
        self._db = self._carregar_db()
        self._construir()

    def _carregar_db(self) -> dict:
        db = {}
        # Caminho absoluto baseado no diretório deste arquivo (ficha.py)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        caminho_json = os.path.join(base_dir, self.CAMINHO_SKILLTREE)

        if os.path.exists(caminho_json):
            try:
                with open(caminho_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for atributo, conteudo in data.items():
                        for no in conteudo.get("nos", []):
                            db[no["id"]] = no
            except Exception as e:
                print(f"Erro ao carregar skilltree: {e}")
        else:
            print(f"Arquivo não encontrado: {caminho_json}")
        return db

    def _construir(self):
        for w in self.winfo_children():
            w.destroy()

        nos_comprados = self._ficha.get("nos_comprados", {})

        if not any(nos_comprados.values()):
            ctk.CTkLabel(self, text="Nenhuma perícia comprada ainda.",
                         font=ctk.CTkFont(size=13), text_color="gray").pack(pady=40)
            return

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Ordem de exibição dos atributos
        ordem_atributos = ["AGI", "FOR", "INT", "VIG", "PRE", "GERAL"]

        for aba in ordem_atributos:
            nos = nos_comprados.get(aba, [])
            if not nos:
                continue
            cor = self.CORES.get(aba, "#888888")

            # Cabeçalho da seção
            header = ctk.CTkFrame(scroll, fg_color="transparent")
            header.pack(fill="x", pady=(12, 4))

            ctk.CTkFrame(header, width=4, height=16,
                         fg_color=cor, corner_radius=2).pack(side="left", padx=(0, 8))
            ctk.CTkLabel(header, text=aba,
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=cor).pack(side="left")
            ctk.CTkLabel(header, text=f"{len(nos)} nós",
                         font=ctk.CTkFont(size=11),
                         text_color="#555555").pack(side="right")

            # Cards dos nós
            for no_id in nos:
                dados_no = self._db.get(no_id, {"id": no_id, "nome": no_id, "descricao": ""})
                self._criar_card(scroll, dados_no, aba)

        # ══════════════════════════════════════════════════════════════════════
        # Habilita scroll com roda do mouse (compatível Windows/Linux)
        # ══════════════════════════════════════════════════════════════════════
        def _scroll(delta):
            """Movimenta a rolagem verticalmente."""
            scroll._parent_canvas.yview_scroll(delta, "units")

        def _bind_scroll_recursivo(widget):
            """Aplica os binds de scroll ao widget e a todos os seus filhos."""
            # Windows/Mac
            widget.bind("<MouseWheel>", lambda e: _scroll(-1 if e.delta > 0 else 1))
            # Linux
            widget.bind("<Button-4>", lambda e: _scroll(-1))
            widget.bind("<Button-5>", lambda e: _scroll(1))
            for child in widget.winfo_children():
                _bind_scroll_recursivo(child)

        # Aplica binds recursivamente a partir do scroll
        _bind_scroll_recursivo(scroll)

        # Garante também no canvas interno (redundante, mas seguro)
        scroll._parent_canvas.bind("<MouseWheel>", lambda e: _scroll(-1 if e.delta > 0 else 1))
        scroll._parent_canvas.bind("<Button-4>", lambda e: _scroll(-1))
        scroll._parent_canvas.bind("<Button-5>", lambda e: _scroll(1))

        # Força foco (útil no Linux)
        scroll.focus_set()


    def _tornar_clicavel(self, widget, callback):
        """Torna o widget e seus filhos clicáveis."""
        widget.bind("<Button-1>", lambda e: callback())
        for child in widget.winfo_children():
            self._tornar_clicavel(child, callback)

    def _criar_card(self, parent, dados_no: dict, atributo: str):
        """Cria um card clicável para um nó da skill tree."""
        card = ctk.CTkFrame(parent, fg_color="#1e1e1e",
                            corner_radius=6, border_width=1,
                            border_color="#333333")
        card.pack(fill="x", pady=2, padx=2)

        self._tornar_clicavel(card, lambda: self._mostrar_detalhes(dados_no, atributo))

        # Linha superior: nome do nó
        topo = ctk.CTkFrame(card, fg_color="transparent")
        topo.pack(fill="x", padx=10, pady=(8, 2))

        ctk.CTkLabel(topo, text=dados_no.get("nome", dados_no.get("id", "?")),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")

        # ID pequeno à direita (opcional)
        ctk.CTkLabel(topo, text=dados_no.get("id", ""),
                     font=ctk.CTkFont(size=10),
                     text_color="#555555").pack(side="right")

        # Prévia da descrição (se houver)
        desc = dados_no.get("descricao", "")
        if desc:
            previa = (desc[:50] + "…") if len(desc) > 50 else desc
            ctk.CTkLabel(card, text=previa, wraplength=480, justify="left",
                         font=ctk.CTkFont(size=11),
                         text_color="#888888").pack(anchor="w", padx=10, pady=(0, 8))
            


    def _mostrar_detalhes(self, dados_no: dict, atributo: str):
        """Exibe popup com detalhes completos da perícia."""
        popup = ctk.CTkToplevel(self.winfo_toplevel())
        popup.title(dados_no.get("nome", dados_no.get("id", "Perícia")))
        popup.geometry("500x400")
        popup.minsize(400, 300)
        popup.after(100, popup.grab_set)

        scroll = ctk.CTkScrollableFrame(popup, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=12)

        # Título
        nome = dados_no.get("nome", dados_no.get("id", "???"))
        ctk.CTkLabel(scroll, text=nome,
                     font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", pady=(0, 4))

        # Atributo
        cor_attr = self.CORES.get(atributo, "#888888")
        ctk.CTkLabel(scroll, text=f"Atributo: {atributo}",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=cor_attr).pack(anchor="w", pady=(0, 12))

        # Descrição completa
        desc = dados_no.get("descricao", "Sem descrição disponível.")
        frame_desc = ctk.CTkFrame(scroll, fg_color="#1e1e1e", corner_radius=8)
        frame_desc.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(frame_desc, text="📜 Descrição",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#cccccc").pack(anchor="w", padx=12, pady=(10, 4))
        ctk.CTkLabel(frame_desc, text=desc, wraplength=440, justify="left",
                     font=ctk.CTkFont(size=12),
                     text_color="#bbbbbb").pack(anchor="w", padx=12, pady=(0, 12))

        # Requisitos (se houver)
        requisitos = dados_no.get("requisitos", [])
        if requisitos:
            req_text = ", ".join(requisitos)
            ctk.CTkLabel(scroll, text=f"🔗 Requisitos: {req_text}",
                         font=ctk.CTkFont(size=12),
                         text_color="#aaaaaa").pack(anchor="w", pady=(4, 8))

        # Custo (se houver)
        custo = dados_no.get("custo")
        if custo is not None:
            ctk.CTkLabel(scroll, text=f"💰 Custo: {custo} ponto(s)",
                         font=ctk.CTkFont(size=12),
                         text_color="#aaaaaa").pack(anchor="w", pady=(0, 8))

        # Botão fechar
        ctk.CTkButton(popup, text="Fechar", width=100,
                      command=popup.destroy).pack(pady=(0, 8))

    
    def atualizar(self):
        self._db = self._carregar_db()
        self._construir()

class PainelFeiticos(ctk.CTkFrame):
    """Aba: feitiços escolhidos (padrão + custom)."""

    CAMINHO_FEITICOS = "data/feiticos.json"
    CAMINHO_CUSTOM   = "data/feiticos_custom.json"

    def __init__(self, parent, ficha: dict, on_passiva_change=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._ficha = ficha
        self._on_passiva_change = on_passiva_change
        self._db = self._carregar_db()
        self._construir()

    def _carregar_db(self) -> dict:
        db = {}
        for caminho in [self.CAMINHO_FEITICOS, self.CAMINHO_CUSTOM]:
            if os.path.exists(caminho):
                try:
                    with open(caminho, "r", encoding="utf-8") as f:
                        for item in json.load(f):
                            db[item["id"]] = item
                except Exception:
                    pass
        return db

    def _construir(self):
        for w in self.winfo_children():
            w.destroy()

        ids = self._ficha.get("feiticos", []) + self._ficha.get("feiticos_custom", [])

        if not ids:
            ctk.CTkLabel(self, text="Nenhum feitiço escolhido.",
                         font=ctk.CTkFont(size=13), text_color="gray").pack(pady=40)
            return

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        for fid in ids:
            f = self._db.get(fid)
            if f:
                self._card_completo(scroll, f)
            else:
                self._card_simples(scroll, fid)
            
        # ══════════════════════════════════════════════════════════════════════
        # Habilita scroll com roda do mouse (compatível Windows/Linux)
        # ══════════════════════════════════════════════════════════════════════
        def _scroll(delta):
            """Movimenta a rolagem verticalmente."""
            scroll._parent_canvas.yview_scroll(delta, "units")

        def _bind_scroll_recursivo(widget):
            """Aplica os binds de scroll ao widget e a todos os seus filhos."""
            # Windows/Mac
            widget.bind("<MouseWheel>", lambda e: _scroll(-1 if e.delta > 0 else 1))
            # Linux
            widget.bind("<Button-4>", lambda e: _scroll(-1))
            widget.bind("<Button-5>", lambda e: _scroll(1))
            for child in widget.winfo_children():
                _bind_scroll_recursivo(child)

        # Aplica binds recursivamente a partir do scroll
        _bind_scroll_recursivo(scroll)

        # Garante também no canvas interno (redundante, mas seguro)
        scroll._parent_canvas.bind("<MouseWheel>", lambda e: _scroll(-1 if e.delta > 0 else 1))
        scroll._parent_canvas.bind("<Button-4>", lambda e: _scroll(-1))
        scroll._parent_canvas.bind("<Button-5>", lambda e: _scroll(1))

        # Força foco (útil no Linux)
        scroll.focus_set()

    def _tornar_clicavel(self, widget, callback):
        """Faz com que o widget e todos os seus filhos chamem o callback ao serem clicados."""
        widget.bind("<Button-1>", lambda e: callback())
        for child in widget.winfo_children():
            self._tornar_clicavel(child, callback)

    def _card_completo(self, parent, f: dict):
        # Card como frame normal
        card = ctk.CTkFrame(
            parent,
            fg_color="#1e1e1e",
            corner_radius=8,
            border_width=1,
            border_color="#333333"
        )
        card.pack(fill="x", pady=4)

        # Torna o card e todo seu conteúdo clicável
        self._tornar_clicavel(card, lambda: self._mostrar_detalhes(f))

        # Conteúdo do card (idêntico ao original)
        topo = ctk.CTkFrame(card, fg_color="transparent")
        topo.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(topo, text=f.get("nome", f.get("id", "?")),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")

        classe = f.get("classe", "")
        if classe:
            ctk.CTkLabel(topo, text=classe,
                         font=ctk.CTkFont(size=11),
                         text_color="#666666").pack(side="right")

        desc = f.get("descricao_base") or f.get("descricao", "")
        if desc:
            # Prévia curta da descrição
            previa = (desc[:60] + "…") if len(desc) > 60 else desc
            ctk.CTkLabel(card, text=previa, wraplength=500, justify="left",
                         font=ctk.CTkFont(size=12),
                         text_color="#aaaaaa").pack(anchor="w", padx=12, pady=(0, 10))
            
        if f.get("tipo") == "Passiva" and "efeitos_por_versao" in f:
            versoes = list(f["efeitos_por_versao"].keys())
            self._criar_controles_passiva(card, f["id"], versoes)

    def _card_simples(self, parent, fid: str):
        card = ctk.CTkFrame(
            parent,
            fg_color="#1a1a1a",
            corner_radius=6,
            border_width=1,
            border_color="#2a2a2a"
        )
        card.pack(fill="x", pady=2)
        self._tornar_clicavel(card, lambda: self._mostrar_detalhes({"id": fid, "nome": fid}))

        ctk.CTkLabel(card, text=fid, font=ctk.CTkFont(size=12),
                     text_color="#666666").pack(anchor="w", padx=12, pady=6)
        
    def _mostrar_detalhes(self, feitico: dict):
        popup = ctk.CTkToplevel(self.winfo_toplevel())
        popup.title(feitico.get("nome", feitico.get("id", "Feitiço")))
        popup.geometry("550x500")
        popup.minsize(450, 400)
        popup.after(100, popup.grab_set)

        # Scroll para caso o conteúdo seja grande
        scroll = ctk.CTkScrollableFrame(popup, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # Título e tipo
        header = ctk.CTkFrame(scroll, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))

        nome = feitico.get("nome", feitico.get("id", "???"))
        ctk.CTkLabel(header, text=nome,
                     font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w")

        tipo = feitico.get("tipo", "—")
        cor_tipo = "#2ecc71" if tipo.lower() == "passiva" else "#e67e22"
        ctk.CTkLabel(header, text=f"Tipo: {tipo}",
                     font=ctk.CTkFont(size=13),
                     text_color=cor_tipo).pack(anchor="w", pady=(4, 0))

        # Classe (se houver)
        classe = feitico.get("classe", "")
        if classe:
            ctk.CTkLabel(scroll, text=f"Classe: {classe}",
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="#888888").pack(anchor="w", pady=(0, 8))

        # Descrição base
        desc_base = feitico.get("descricao_base") or feitico.get("descricao", "")
        if desc_base:
            frame_desc = ctk.CTkFrame(scroll, fg_color="#1e1e1e", corner_radius=8)
            frame_desc.pack(fill="x", pady=(0, 12))
            ctk.CTkLabel(frame_desc, text="📜 Descrição",
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color="#cccccc").pack(anchor="w", padx=12, pady=(10, 4))
            ctk.CTkLabel(frame_desc, text=desc_base, wraplength=480, justify="left",
                         font=ctk.CTkFont(size=12),
                         text_color="#bbbbbb").pack(anchor="w", padx=12, pady=(0, 10))

        # Versões (upgrades)
        versoes = feitico.get("versoes", {})
        if versoes:
            ctk.CTkLabel(scroll, text="⬆️ Versões melhoradas",
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color="#aaaaaa").pack(anchor="w", pady=(0, 6))

            for grau, texto in versoes.items():
                frame_ver = ctk.CTkFrame(scroll, fg_color="#1a1a1a", corner_radius=6)
                frame_ver.pack(fill="x", pady=2)
                ctk.CTkLabel(frame_ver, text=f"{grau}:", width=80,
                             font=ctk.CTkFont(size=12, weight="bold"),
                             text_color="#f1c40f").pack(side="left", padx=10, pady=8)
                ctk.CTkLabel(frame_ver, text=texto, wraplength=380, justify="left",
                             font=ctk.CTkFont(size=12),
                             text_color="#cccccc").pack(side="left", padx=(0, 10), pady=8)

        # Espaço reservado para efeitos futuros (não implementado ainda)
        if "efeitos_por_versao" in feitico:
            ctk.CTkLabel(scroll, text="⚙️ Efeitos mecânicos (em breve)",
                         font=ctk.CTkFont(size=12, slant="italic"),
                         text_color="#555555").pack(anchor="w", pady=(12, 0))

        # Botão fechar
        ctk.CTkButton(popup, text="Fechar", width=100,
                      command=popup.destroy).pack(pady=(0, 10))
        
    def _criar_controles_passiva(self, parent, feitico_id: str, versoes_disponiveis: list):
        """Cria checkbox e dropdown para ativar/versionar uma passiva."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=12, pady=(0, 8))

        # Estado atual
        passivas_ativas = self._ficha.get("passivas_ativas", {})
        ativa = feitico_id in passivas_ativas
        versao_atual = passivas_ativas.get(feitico_id, "BASE")

        var_ativa = ctk.BooleanVar(value=ativa)
        var_versao = ctk.StringVar(value=versao_atual)

        cb = ctk.CTkCheckBox(frame, text="Ativar", variable=var_ativa,
                             font=ctk.CTkFont(size=12),
                             command=lambda: self._toggle_passiva(feitico_id, var_ativa, var_versao, dropdown))
        cb.pack(side="left", padx=(0, 10))

        dropdown = ctk.CTkOptionMenu(frame, values=versoes_disponiveis, variable=var_versao,
                                    width=100, height=28, font=ctk.CTkFont(size=12),
                                    command=lambda val: self._mudar_versao_passiva(feitico_id, val))
        dropdown.pack(side="left")
        if not ativa:
            dropdown.configure(state="disabled")

        return cb, dropdown

    def _toggle_passiva(self, fid, var_ativa, var_versao, dropdown):
        ativa = var_ativa.get()
        passivas = self._ficha.setdefault("passivas_ativas", {})
        if ativa:
            passivas[fid] = var_versao.get()
            dropdown.configure(state="normal")
        else:
            passivas.pop(fid, None)
            dropdown.configure(state="disabled")
        self._aplicar_passivas()

    def _mudar_versao_passiva(self, fid, nova_versao):
        if fid in self._ficha.get("passivas_ativas", {}):
            self._ficha["passivas_ativas"][fid] = nova_versao
            self._aplicar_passivas()

    def _aplicar_passivas(self):
        """Dispara o recálculo na janela principal."""
        if self._on_passiva_change:
            self._on_passiva_change()

    def atualizar(self):
        self._db = self._carregar_db()
        self._construir()


class PainelEstiloLuta(ctk.CTkFrame):
    """Aba dedicada ao Estilo de Luta."""

    def __init__(self, parent, ficha: dict, on_save=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._ficha = ficha
        self._on_save = on_save
        self._construir()

    def _construir(self):
        for w in self.winfo_children():
            w.destroy()

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        self._secao(scroll, "Estilo de Luta", "estilo_luta")

         # ══════════════════════════════════════════════════════════════════════
        # Habilita scroll com roda do mouse (compatível Windows/Linux)
        # ══════════════════════════════════════════════════════════════════════
        def _scroll(delta):
            """Movimenta a rolagem verticalmente."""
            scroll._parent_canvas.yview_scroll(delta, "units")

        def _bind_scroll_recursivo(widget):
            """Aplica os binds de scroll ao widget e a todos os seus filhos."""
            # Windows/Mac
            widget.bind("<MouseWheel>", lambda e: _scroll(-1 if e.delta > 0 else 1))
            # Linux
            widget.bind("<Button-4>", lambda e: _scroll(-1))
            widget.bind("<Button-5>", lambda e: _scroll(1))
            for child in widget.winfo_children():
                _bind_scroll_recursivo(child)

        # Aplica binds recursivamente a partir do scroll
        _bind_scroll_recursivo(scroll)

        # Garante também no canvas interno (redundante, mas seguro)
        scroll._parent_canvas.bind("<MouseWheel>", lambda e: _scroll(-1 if e.delta > 0 else 1))
        scroll._parent_canvas.bind("<Button-4>", lambda e: _scroll(-1))
        scroll._parent_canvas.bind("<Button-5>", lambda e: _scroll(1))

        # Força foco (útil no Linux)
        scroll.focus_set()

    def _secao(self, parent, titulo: str, chave: str):
        # Código idêntico ao método _secao da classe PainelEstiloTecnica
        dados = self._ficha.get(chave, {}) or {}

        ctk.CTkLabel(parent, text=titulo,
                     font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", pady=(0, 8))

        card = ctk.CTkFrame(parent, fg_color="#1e1e1e",
                            corner_radius=8, border_width=1,
                            border_color="#333333")
        card.pack(fill="x", pady=(0, 8))

        linha = ctk.CTkFrame(card, fg_color="transparent")
        linha.pack(fill="x", padx=12, pady=(10, 4))

        nome_exib = dados.get("nome") or "Não definido"
        ctk.CTkLabel(linha, text=nome_exib,
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")

        if dados.get("origem") == "custom":
            ctk.CTkLabel(linha, text="personalizado",
                         font=ctk.CTkFont(size=11),
                         text_color="#9b59b6").pack(side="right")

        efeito = dados.get("efeito") or dados.get("descricao") or ""
        if efeito:
            ctk.CTkLabel(card, text=efeito, wraplength=500, justify="left",
                         font=ctk.CTkFont(size=12),
                         text_color="#aaaaaa").pack(anchor="w", padx=12, pady=(0, 10))

        ctk.CTkButton(parent, text=f"Editar {titulo}", width=160,
                      fg_color="transparent", border_width=1,
                      border_color="#444444",
                      command=lambda: self._popup_editar(chave, titulo)
                      ).pack(anchor="w")

    def _popup_editar(self, chave: str, titulo: str):
        # Exatamente igual ao popup original
        dados = self._ficha.get(chave, {}) or {}

        popup = ctk.CTkToplevel(self.winfo_toplevel())
        popup.title(f"Editar {titulo}")
        popup.geometry("480x400")
        popup.after(100, popup.grab_set)

        ctk.CTkLabel(popup, text=titulo,
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 12))

        ctk.CTkLabel(popup, text="Nome:", anchor="w").pack(fill="x", padx=20)
        e_nome = ctk.CTkEntry(popup, width=440)
        e_nome.insert(0, dados.get("nome") or "")
        e_nome.pack(padx=20, pady=(4, 12))

        ctk.CTkLabel(popup, text="Efeito / Descrição:", anchor="w").pack(fill="x", padx=20)
        e_efeito = ctk.CTkTextbox(popup, height=140, width=440)
        e_efeito.insert("1.0", dados.get("efeito") or dados.get("descricao") or "")
        e_efeito.pack(padx=20, pady=(4, 16))

        def salvar():
            self._ficha[chave] = {
                "id":       dados.get("id"),
                "nome":     e_nome.get().strip() or None,
                "descricao": None,
                "origem":   "custom",
                "efeito":   e_efeito.get("1.0", "end-1c").strip() or None,
            }
            if self._on_save:
                self._on_save()
            popup.destroy()
            self._construir()

        ctk.CTkButton(popup, text="Salvar", command=salvar).pack()

    def atualizar(self):
        self._construir()


class PainelTecnica(PainelEstiloLuta):
    """Aba dedicada à Técnica. Herda de PainelEstiloLuta e só muda o título/chave."""

    def __init__(self, parent, ficha: dict, on_save=None, **kwargs):
        # Inicializa normalmente, mas forçamos a chave e título específicos
        super().__init__(parent, ficha, on_save, **kwargs)

    def _construir(self):
        for w in self.winfo_children():
            w.destroy()

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        self._secao(scroll, "Técnica", "tecnica")

        # ══════════════════════════════════════════════════════════════════════
        # Habilita scroll com roda do mouse (compatível Windows/Linux)
        # ══════════════════════════════════════════════════════════════════════
        def _scroll(delta):
            """Movimenta a rolagem verticalmente."""
            scroll._parent_canvas.yview_scroll(delta, "units")

        def _bind_scroll_recursivo(widget):
            """Aplica os binds de scroll ao widget e a todos os seus filhos."""
            # Windows/Mac
            widget.bind("<MouseWheel>", lambda e: _scroll(-1 if e.delta > 0 else 1))
            # Linux
            widget.bind("<Button-4>", lambda e: _scroll(-1))
            widget.bind("<Button-5>", lambda e: _scroll(1))
            for child in widget.winfo_children():
                _bind_scroll_recursivo(child)

        # Aplica binds recursivamente a partir do scroll
        _bind_scroll_recursivo(scroll)

        # Garante também no canvas interno (redundante, mas seguro)
        scroll._parent_canvas.bind("<MouseWheel>", lambda e: _scroll(-1 if e.delta > 0 else 1))
        scroll._parent_canvas.bind("<Button-4>", lambda e: _scroll(-1))
        scroll._parent_canvas.bind("<Button-5>", lambda e: _scroll(1))

        # Força foco (útil no Linux)
        scroll.focus_set()


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


class PainelAnotacoes(ctk.CTkFrame):
    """Aba: texto livre para anotações de sessão com autosave por debounce."""

    def __init__(self, parent, ficha: dict, on_save=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._ficha          = ficha
        self._on_save        = on_save
        self._timer_autosave = None
        self._construir()

    def _construir(self):
        ctk.CTkLabel(self, text="Anotações de sessão",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 8))

        self._texto = ctk.CTkTextbox(self, font=ctk.CTkFont(size=13),
                                     fg_color="#1e1e1e", corner_radius=8,
                                     border_width=1, border_color="#333333")
        self._texto.pack(fill="both", expand=True)
        self._texto.insert("1.0", self._ficha.get("anotacoes", ""))
        self._texto.bind("<KeyRelease>", self._ao_digitar)

    def _ao_digitar(self, _event=None):
        if self._timer_autosave:
            self.after_cancel(self._timer_autosave)
        self._timer_autosave = self.after(1500, self._salvar)

    def _salvar(self):
        self._ficha["anotacoes"] = self._texto.get("1.0", "end-1c")
        if self._on_save:
            self._on_save()

    def atualizar(self):
        self._texto.delete("1.0", "end")
        self._texto.insert("1.0", self._ficha.get("anotacoes", ""))


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
        


# ══════════════════════════════════════════════════════════════════════════════
# Tela principal: FichaPersonagem
# ══════════════════════════════════════════════════════════════════════════════

class FichaPersonagem:
    """
    Tela de gerenciamento de ficha — substitui a janela do gerenciador.

    Parâmetros
    ----------
    app       : janela ctk.CTk existente (reutilizada)
    ficha     : dict normalizado com _arquivo preenchido
    on_voltar : callback chamado ao clicar Voltar
    """

    ABA_NOMES = [
        "Perícias",
        "Skill Tree",
        "Feitiços",
        "Estilo de Luta",
        "Técnica",
        "Inventário",
        "Resumo",
        "Anotações",
    ]

    CORES_RECURSO = {
        "pv":  "#e74c3c",
        "san": "#3498db",
        "pe":  "#f39c12",
    }

    CORES_ATRIBUTO = {
        "AGI": "#e67e22", "FOR": "#e74c3c",
        "INT": "#3498db", "VIG": "#2ecc71",
        "PRE": "#9b59b6",
    }

    def __init__(self, app: ctk.CTk, ficha: dict, on_voltar=None):
        self.app       = app
        self.ficha     = normalizar_ficha(ficha)
        self.on_voltar = on_voltar

        self._aba_ativa   = 0
        self._paineis_aba: dict[int, ctk.CTkFrame] = {}
        self._barras:      dict[str, BarraRecurso]  = {}

        # ══════════════════════════════════════════════════════════════════════
        # NOVO: Controle de atributos editáveis
        # ══════════════════════════════════════════════════════════════════════
        self._attr_widgets = {}        # guarda referências aos labels de valor
        self._lbl_pontos_disponiveis = None  # será criado depois
        # ══════════════════════════════════════════════════════════════════════

        self._fontes()
        self._construir()

    # ── Fontes ────────────────────────────────────────────────────────────────

    def _fontes(self):
        self.f_titulo    = ctk.CTkFont(size=22, weight="bold")
        self.f_subtitulo = ctk.CTkFont(size=13)
        self.f_secao     = ctk.CTkFont(size=12, weight="bold")
        self.f_valor     = ctk.CTkFont(size=20, weight="bold")
        self.f_label     = ctk.CTkFont(size=11)
        self.f_botao     = ctk.CTkFont(size=13)

    # ── Layout geral ──────────────────────────────────────────────────────────

    def _construir(self):
        for w in self.app.winfo_children():
            w.destroy()

        self.app.geometry("1100x700")
        self.app.minsize(900, 560)
        self.app.title(f"Projeto BITE — {self.ficha.get('nome', 'Ficha')}")

        raiz = ctk.CTkFrame(self.app, fg_color="transparent")
        raiz.pack(fill="both", expand=True, padx=16, pady=16)
        raiz.columnconfigure(1, weight=1)
        raiz.rowconfigure(0, weight=1)

        # Painel lateral fixo
        self._lateral = ctk.CTkFrame(raiz, width=280, corner_radius=12,
                                     fg_color="#161616", border_width=1,
                                     border_color="#2a2a2a")
        self._lateral.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self._lateral.grid_propagate(False)

        # Área principal
        self._area = ctk.CTkFrame(raiz, corner_radius=12,
                                  fg_color="#161616", border_width=1,
                                  border_color="#2a2a2a")
        self._area.grid(row=0, column=1, sticky="nsew")
        self._area.rowconfigure(1, weight=1)
        self._area.columnconfigure(0, weight=1)

        self._construir_lateral()
        self._construir_abas()
        self._mostrar_aba(0)
        # Atalho de teclado para debug (Ctrl+D)
        self.app.bind("<Control-d>", self._debug_popup)
                
        self._recalcular_tudo()

    # ── Painel lateral ────────────────────────────────────────────────────────

    def _construir_lateral(self):
        lat = self._lateral

        # Botão voltar
        ctk.CTkButton(lat, text="← Voltar", font=self.f_botao, width=90,
                      fg_color="transparent", border_width=1,
                      border_color="#333333",
                      command=self._voltar).pack(anchor="nw", padx=12, pady=(12, 0))

        # Identidade
        ctk.CTkLabel(lat, text=self.ficha.get("nome", "—"),
                     font=self.f_titulo,
                     wraplength=240).pack(pady=(10, 2), padx=16)

        ctk.CTkLabel(lat,
                     text=f"{self.ficha.get('classe','—')}  ·  {self.ficha.get('trilha','—')}",
                     font=self.f_subtitulo, text_color="#888888",
                     wraplength=240).pack(pady=(0, 2), padx=16)

                # Frame para NEX e Grau editáveis
        frame_nex_grau = ctk.CTkFrame(lat, fg_color="transparent")
        frame_nex_grau.pack(fill="x", padx=16, pady=(0, 10))

        # NEX
        ctk.CTkLabel(frame_nex_grau, text="NEX:", font=ctk.CTkFont(size=11),
                     text_color="#888888").pack(side="left")

        opcoes_nex = self._listar_opcoes_nex()
        # Ordena para exibição mais lógica (opcional)
        opcoes_nex.sort(key=lambda x: float(x.replace('%', '')) if x != "99.99%" else 99.99)

        self._nex_var = ctk.StringVar(value=self.ficha.get("nex", "5%"))
        nex_menu = ctk.CTkOptionMenu(
            frame_nex_grau,
            values=opcoes_nex,
            variable=self._nex_var,
            width=75,
            height=28,
            font=ctk.CTkFont(size=12),
            command=self._ao_mudar_nex
        )
        nex_menu.pack(side="left", padx=(4, 12))

        # Grau
        ctk.CTkLabel(frame_nex_grau, text="Grau:", font=ctk.CTkFont(size=11),
                     text_color="#888888").pack(side="left")

        opcoes_grau = self._listar_opcoes_grau()
        self._grau_var = ctk.StringVar(value=self.ficha.get("grau", "Grau 4"))
        grau_menu = ctk.CTkOptionMenu(
            frame_nex_grau,
            values=opcoes_grau,
            variable=self._grau_var,
            width=120,
            height=28,
            font=ctk.CTkFont(size=12),
            command=self._ao_mudar_grau
        )
        grau_menu.pack(side="left", padx=(4, 0))

        ctk.CTkFrame(lat, height=1, fg_color="#2a2a2a").pack(fill="x", padx=12)

                # Barras de recursos – agora fixas, sem scroll
        rec_frame = ctk.CTkFrame(lat, fg_color="transparent")
        rec_frame.pack(fill="x", padx=16, pady=12)

        estado = self.ficha["estado"]
        specs = [
            ("PV",       "pv",  "pv_atual",  "pv_maximo"),
            ("Sanidade", "san", "san_atual",  "san_maximo"),
            ("PE",       "pe",  "pe_atual",   "pe_maximo"),
        ]

        for nome_exib, chave, k_atual, k_max in specs:
            barra = BarraRecurso(
                rec_frame,   # <--- aqui muda de rec_scroll para rec_frame
                label    = nome_exib,
                atual    = estado.get(k_atual, 0),
                maximo   = estado.get(k_max,   0),
                cor_barra= self.CORES_RECURSO[chave],
                on_change= self._make_callback(chave, k_atual, k_max),
            )
            barra.pack(fill="x", pady=(0, 14))
            self._barras[chave] = barra

        ctk.CTkFrame(lat, height=1, fg_color="#2a2a2a").pack(fill="x", padx=12)

        # ══════════════════════════════════════════════════════════════════════
        # Atributos (EDITÁVEIS)
        # ══════════════════════════════════════════════════════════════════════
        ctk.CTkFrame(lat, height=1, fg_color="#2a2a2a").pack(fill="x", padx=12, pady=(6, 6))

        # Cabeçalho com pontos disponíveis
        header_attr = ctk.CTkFrame(lat, fg_color="transparent")
        header_attr.pack(fill="x", padx=16, pady=(4, 6))

        ctk.CTkLabel(header_attr, text="ATRIBUTOS",
                     font=self.f_secao, text_color="#555555").pack(side="left")

        pontos_disp = calcular_pontos_disponiveis_ficha(self.ficha)
        self._lbl_pontos_disponiveis = ctk.CTkLabel(
            header_attr,
            text=f"{pontos_disp} pts",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#f1c40f" if pontos_disp > 0 else "#888888"
        )
        self._lbl_pontos_disponiveis.pack(side="right")

        # Scroll frame para os atributos (caso haja muitos)
        attr_scroll = ctk.CTkScrollableFrame(lat, fg_color="transparent", height=200)
        attr_scroll.pack(fill="x", padx=8, pady=(0, 8))

        # Container interno (para alinhamento)
        attr_container = ctk.CTkFrame(attr_scroll, fg_color="transparent")
        attr_container.pack(fill="x")

        # Para cada atributo, criar uma linha com: sigla | valor | [+] [-]
        for sigla, valor in self.ficha.get("atributos", {}).items():
            cor = self.CORES_ATRIBUTO.get(sigla, "#888888")

            linha = ctk.CTkFrame(attr_container, fg_color="transparent")
            linha.pack(fill="x", pady=2)

            # Sigla do atributo
            ctk.CTkLabel(linha, text=sigla,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=cor, width=40).pack(side="left", padx=(8, 4))

            # Valor atual
            lbl_valor = ctk.CTkLabel(linha, text=str(valor),
                                     font=ctk.CTkFont(size=16, weight="bold"),
                                     text_color="#ffffff", width=30)
            lbl_valor.pack(side="left", padx=4)
            self._attr_widgets[sigla] = lbl_valor

            # Botão diminuir (-)
            btn_menos = ctk.CTkButton(
                linha, text="−", width=28, height=28,
                font=ctk.CTkFont(size=14),
                fg_color="#2a2a2a", hover_color="#3a3a3a",
                command=lambda s=sigla: self._ajustar_atributo(s, -1)
            )
            btn_menos.pack(side="right", padx=2)

            # Botão aumentar (+)
            btn_mais = ctk.CTkButton(
                linha, text="+", width=28, height=28,
                font=ctk.CTkFont(size=14),
                fg_color="#2a2a2a", hover_color="#3a3a3a",
                command=lambda s=sigla: self._ajustar_atributo(s, +1)
            )
            btn_mais.pack(side="right", padx=2)

        # ══════════════════════════════════════════════════════════════════════
        # Pontos extras (buffs temporários)
        # ══════════════════════════════════════════════════════════════════════
        extras_frame = ctk.CTkFrame(lat, fg_color="transparent")
        extras_frame.pack(fill="x", padx=16, pady=(4, 8))

        ctk.CTkLabel(extras_frame, text="Pontos extras:",
                     font=ctk.CTkFont(size=11), text_color="#666666").pack(side="left")

        self._entrada_extras = ctk.CTkEntry(extras_frame, width=50, height=26,
                                            font=ctk.CTkFont(size=12),
                                            placeholder_text="0")
        self._entrada_extras.pack(side="left", padx=(4, 4))

        ctk.CTkButton(extras_frame, text="Adicionar", width=70, height=26,
                      font=ctk.CTkFont(size=11),
                      fg_color="#2a2a2a", hover_color="#3a3a3a",
                      command=self._adicionar_pontos_extras).pack(side="left")

        # Indicador de salvamento
        self._lbl_salvo = ctk.CTkLabel(lat, text="",
                                       font=ctk.CTkFont(size=10),
                                       text_color="#444444")
        self._lbl_salvo.pack(pady=(8, 4), padx=16)

        # ══════════════════════════════════════════════════════════════════════
        # Botão Recalcular (PV / PE / SAN)
        # ══════════════════════════════════════════════════════════════════════
        btn_recalcular = ctk.CTkButton(
            lat,
            text="⟲ Recalcular PV/PE/SAN",
            font=ctk.CTkFont(size=11),
            fg_color="#2a2a2a",
            hover_color="#3a3a3a",
            border_width=1,
            border_color="#444444",
            command=self._recalcular_tudo
        )
        btn_recalcular.pack(fill="x", padx=16, pady=(4, 4))

    def _make_callback(self, chave: str, k_atual: str, k_max: str):
        """Fábrica de callbacks para as barras de recurso."""
        def callback(_valor_ignorado: int):
            barra = self._barras[chave]
            self.ficha["estado"][k_atual] = barra.get_atual()
            self.ficha["estado"][k_max]   = barra.get_maximo()
            self._salvar()
        return callback

    # ── Abas ──────────────────────────────────────────────────────────────────

    def _construir_abas(self):
        area = self._area

        # Barra de navegação das abas
        nav = ctk.CTkFrame(area, fg_color="#0f0f0f", height=42, corner_radius=0)
        nav.grid(row=0, column=0, sticky="ew")
        nav.pack_propagate(False)

        self._botoes_aba: list[ctk.CTkButton] = []
        for i, nome in enumerate(self.ABA_NOMES):
            btn = ctk.CTkButton(
                nav, text=nome, height=42, font=self.f_botao,
                fg_color="transparent", text_color="#666666",
                hover_color="#1a1a1a", corner_radius=0,
                command=lambda idx=i: self._mostrar_aba(idx),
            )
            btn.pack(side="left", padx=2)
            self._botoes_aba.append(btn)

        # Frame de conteúdo das abas
        self._frame_conteudo = ctk.CTkFrame(area, fg_color="transparent")
        self._frame_conteudo.grid(row=1, column=0, sticky="nsew", padx=16, pady=16)
        self._frame_conteudo.rowconfigure(0, weight=1)
        self._frame_conteudo.columnconfigure(0, weight=1)

    def _mostrar_aba(self, idx: int):
        self._aba_ativa = idx

        # Destaca aba ativa
        for i, btn in enumerate(self._botoes_aba):
            if i == idx:
                btn.configure(text_color="#ffffff", fg_color="#1e1e1e")
            else:
                btn.configure(text_color="#666666", fg_color="transparent")

        # Oculta todos os painéis
        for painel in self._paineis_aba.values():
            painel.grid_forget()

        # Cria painel sob demanda (lazy)
        if idx not in self._paineis_aba:
            self._paineis_aba[idx] = self._criar_painel(idx)

        self._paineis_aba[idx].grid(row=0, column=0, sticky="nsew")

    def _criar_painel(self, idx: int) -> ctk.CTkFrame:
        """Instancia o painel correto para cada índice de aba."""
        nome = self.ABA_NOMES[idx]
        pai  = self._frame_conteudo

        fabricas = {
            "Perícias":        lambda: PainelPericias(pai, self.ficha),
            "Skill Tree":      lambda: PainelSkilltree(pai, self.ficha), 
            "Feitiços":        lambda: PainelFeiticos(pai, self.ficha, on_passiva_change=self._recalcular_tudo),
            "Estilo de Luta":  lambda: PainelEstiloLuta(pai, self.ficha, on_save=self._salvar),
            "Técnica":         lambda: PainelTecnica(pai, self.ficha, on_save=self._salvar),
            "Inventário":      lambda: PainelInventario(pai, self.ficha, on_save=self._salvar),
            "Resumo":          lambda: PainelResumo(pai, self.ficha),
            "Anotações":       lambda: PainelAnotacoes(pai, self.ficha, on_save=self._salvar),
        }

        fabrica = fabricas.get(nome)
        if fabrica:
            return fabrica()

        # Fallback genérico para abas ainda não implementadas
        frame = ctk.CTkFrame(pai, fg_color="transparent")
        ctk.CTkLabel(frame, text=f"'{nome}' em construção.",
                     text_color="gray").pack(pady=40)
        return frame

    # ── Persistência ──────────────────────────────────────────────────────────

    def _salvar(self):
        salvar_ficha(self.ficha)
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self._lbl_salvo.configure(text=f"salvo às {ts}")

    # ── Navegação ─────────────────────────────────────────────────────────────

    # ══════════════════════════════════════════════════════════════════════════
    # Manipulação de atributos (edição na lateral)
    # ══════════════════════════════════════════════════════════════════════════

    def _atualizar_ui_atributos(self):
        """Atualiza labels de valor e pontos disponíveis após alteração."""
        # Atualiza labels de valor
        for sigla, lbl in self._attr_widgets.items():
            valor = self.ficha["atributos"][sigla]
            lbl.configure(text=str(valor))

        # Recalcula e atualiza pontos disponíveis
        pontos = calcular_pontos_disponiveis_ficha(self.ficha)
        if self._lbl_pontos_disponiveis:
            self._lbl_pontos_disponiveis.configure(
                text=f"{pontos} pts",
                text_color="#f1c40f" if pontos > 0 else "#888888"
            )

        # Salva automaticamente
        self._salvar()

    def _ajustar_atributo(self, sigla: str, delta: int):
        """Aumenta ou diminui o valor do atributo, respeitando limites e pontos disponíveis."""
        valor_atual = self.ficha["atributos"][sigla]
        pontos_disp = calcular_pontos_disponiveis_ficha(self.ficha)

        if delta > 0:
            # Aumentar: precisa de pontos e não pode ultrapassar LIMITE_NORMAL
            if pontos_disp <= 0:
                return  # Poderia tocar um aviso sonoro, mas por ora silencioso
            if valor_atual >= LIMITE_NORMAL:
                return
            self.ficha["atributos"][sigla] += 1
            self.ficha["pontos_atributo_gastos"] = self.ficha.get("pontos_atributo_gastos", 0) + 1
        else:  # delta < 0
            # Diminuir: não pode ficar abaixo de 0
            if valor_atual <= 0:
                return
            self.ficha["atributos"][sigla] -= 1
            self.ficha["pontos_atributo_gastos"] = max(0, self.ficha.get("pontos_atributo_gastos", 0) - 1)

        self._atualizar_ui_atributos()


    def _calcular_bonus_passivas(self) -> dict:
        """Retorna apenas os bônus das passivas ativas."""
        db_feiticos = {}
        caminhos = ["data/feiticos.json", "data/feiticos_custom.json"]
        for caminho in caminhos:
            if os.path.exists(caminho):
                with open(caminho, "r", encoding="utf-8") as f:
                    for item in json.load(f):
                        db_feiticos[item["id"]] = item

        contexto = construir_contexto_base(self.ficha)
        bonificacoes = {}

        for feat_id, versao in self.ficha.get("passivas_ativas", {}).items():
            feitico = db_feiticos.get(feat_id)
            if not feitico or feitico.get("tipo") != "Passiva":
                continue
            efeitos_versao = feitico.get("efeitos_por_versao", {}).get(versao, [])
            if not efeitos_versao and versao != "BASE":
                efeitos_versao = feitico.get("efeitos_por_versao", {}).get("BASE", [])

            for efeito in efeitos_versao:
                alvo = efeito["alvo"]
                operacao = efeito["operacao"]
                formula = efeito["formula"]
                valor = avaliar_formula(formula, contexto)

                if alvo not in bonificacoes:
                    bonificacoes[alvo] = 0

                if operacao == "+":
                    bonificacoes[alvo] += valor
                elif operacao == "-":
                    bonificacoes[alvo] -= valor
                elif operacao == "=":
                    bonificacoes[alvo] = valor

        return bonificacoes

    def recalcular_bonus_skilltree(self) -> dict:
        """Retorna um dicionário com os bônus acumulados da Skill Tree."""
        bonificacoes = {}
        nos_comprados = self.ficha.get("nos_comprados", {})
        if not nos_comprados:
            return bonificacoes

        # Carrega o banco da skill tree
        db_skilltree = {}
        caminho = os.path.join(os.path.dirname(__file__), "data", "skilltrees.json")
        if os.path.exists(caminho):
            with open(caminho, "r", encoding="utf-8") as f:
                data = json.load(f)
                for atributo, conteudo in data.items():
                    for no in conteudo.get("nos", []):
                        db_skilltree[no["id"]] = no

        contexto = construir_contexto_base(self.ficha)

        for atributo, ids in nos_comprados.items():
            for no_id in ids:
                no = db_skilltree.get(no_id)
                if not no:
                    continue
                for efeito in no.get("efeitos", []):
                    alvo = efeito["alvo"]
                    operacao = efeito["operacao"]
                    formula = efeito["formula"]
                    valor = avaliar_formula(formula, contexto)

                    if alvo not in bonificacoes:
                        bonificacoes[alvo] = 0

                    if operacao == "+":
                        bonificacoes[alvo] += valor
                    elif operacao == "-":
                        bonificacoes[alvo] -= valor
                    elif operacao == "=":
                        bonificacoes[alvo] = valor

        return bonificacoes

    def _adicionar_pontos_extras(self):
        """Adiciona pontos temporários (buffs) ao pool disponível."""
        texto = self._entrada_extras.get().strip()
        if not texto:
            return
        try:
            qtd = int(texto)
        except ValueError:
            return
        if qtd <= 0:
            return

        # Armazena como campo separado (não interfere nos gastos fixos)
        self.ficha["pontos_extras_temp"] = self.ficha.get("pontos_extras_temp", 0) + qtd
        self._entrada_extras.delete(0, "end")
        self._atualizar_ui_atributos()

    def _voltar(self):
        if self.on_voltar:
            self.on_voltar()


    # ══════════════════════════════════════════════════════════════════════════
    # Progressão de NEX e Grau
    # ══════════════════════════════════════════════════════════════════════════

    def _carregar_progressao_nex(self) -> dict:
        """Carrega a tabela de progressão NEX do arquivo JSON."""
        caminho = os.path.join(os.path.dirname(__file__), "data", "progressao_nex.json")
        if os.path.exists(caminho):
            with open(caminho, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    
    def _carregar_classes(self) -> dict:
        """Carrega o dicionário de classes (nome -> dados)."""
        caminho = os.path.join(os.path.dirname(__file__), "data", "classes.json")
        if os.path.exists(caminho):
            with open(caminho, "r", encoding="utf-8") as f:
                lista = json.load(f)
                return {item["nome"]: item for item in lista}
        return {}

    def _carregar_graus(self) -> dict:
        caminho = os.path.join(os.path.dirname(__file__), "data", "graus.json")
        if os.path.exists(caminho):
            with open(caminho, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("graus", {})
        return {}
    
    def calcular_valor_pericia(ficha: dict, nome_pericia: str) -> int:
        """Retorna o valor total da perícia (atributo efetivo + treinamento + bônus)."""
        pericia = ficha.get("pericias", {}).get(nome_pericia)
        if not pericia:
            return 0

        atributos = ficha.get("atributos", {})
        attr_override = pericia.get("atributo_override")
        attr_base = pericia.get("atributo_base", "FOR")

        atributo_valor = atributos.get(attr_override if attr_override else attr_base, 0)

        treinamento = pericia.get("treinamento", 0)
        bonus = pericia.get("bonus", 0)

        return atributo_valor + treinamento + bonus

    def _listar_opcoes_nex(self) -> list:
        """Retorna lista de NEX disponíveis (ex.: ['5%', '10%', ...])."""
        progressao = self._carregar_progressao_nex()
        return list(progressao.keys())

    def _listar_opcoes_grau(self) -> list:
        graus = self._carregar_graus()
        # Ordem desejada (pode ajustar)
        ordem = ["Grau 4", "Grau 3", "Grau 2", "Grau 1",
                 "Grau Semi Especial", "Grau Especial", "Grau Ultra Especial"]
        return [g for g in ordem if g in graus]

    def _ao_mudar_nex(self, novo_nex: str):
        self.ficha["nex"] = novo_nex
        self.ficha["pontos_atributo_gastos"] = 0
        self.ficha["pontos_extras_temp"] = 0
        self._recalcular_tudo()
        self._atualizar_ui_atributos()
        self._salvar()

    def _ao_mudar_grau(self, novo_grau: str):
        self.ficha["grau"] = novo_grau
        self._recalcular_tudo()
        self._salvar()

    def _recalcular_totais_nex(self):
        progressao = self._carregar_progressao_nex()
        nex_atual = self.ficha.get("nex", "5%")

        campos_possiveis = [
            "pontos_atributo", "feiticos", "graus_treinamento",
            "habilidade_trilha", "afinidade", "expansao_modo",
            "melhorias_superiores", "habilidades_lendarias", "habilidade_tecnica_n6"
        ]
        totais = {campo: 0 for campo in campos_possiveis}

        for nivel, bonus in progressao.items():
            for campo in campos_possiveis:
                totais[campo] += bonus.get(campo, 0)
            if nivel == nex_atual:
                break

        # 🔁 Atualiza o LP natural antes de calcular recursos
        self._atualizar_lp_base()

        self.ficha["totais_nex"] = totais
        self._atualizar_recursos_por_grau_e_nex()

    def _atualizar_lp_base(self):
        """Define o LP baseado no NEX atual."""
        progressao = self._carregar_progressao_nex()
        nex_atual = self.ficha.get("nex", "5%")
        lp_base = progressao.get(nex_atual, {}).get("lp", 1)
        self.ficha["lp"] = lp_base
           

    def _atualizar_recursos_por_grau_e_nex(self):
        # Carrega dados
        graus = self._carregar_graus()
        classes = self._carregar_classes()
        grau_atual = self.ficha.get("grau", "Grau 4")
        info_grau = graus.get(grau_atual, {})
        classe_nome = self.ficha.get("classe", "")
        info_classe = classes.get(classe_nome, {})

        atributos = self.ficha.get("atributos", {})
        vig = atributos.get("VIG", 1)
        pre = atributos.get("PRE", 1)

        # -----------------------------------------------------------------
        # 1. Atualiza o LP baseado no NEX
        # -----------------------------------------------------------------
        self._atualizar_lp_base()   
        lp_base = self.ficha.get("lp", 1)

        # -----------------------------------------------------------------
        # 2. Determina os multiplicadores (agora por LP, não por NEX)
        # -----------------------------------------------------------------
        pv_por_lp = 0
        san_por_lp = 0
        pe_por_lp = 0

        if "classes" in info_grau and classe_nome in info_grau["classes"]:
            bonus_classe = info_grau["classes"][classe_nome]
            pv_por_lp = bonus_classe.get("pv_por_nex", 0)   # mantém nome original do JSON
            san_por_lp = bonus_classe.get("san_por_nex", 0)
            pe_por_lp = bonus_classe.get("pe_por_nex", 0)
        elif "pv_por_nex" in info_grau:
            pv_por_lp = info_grau.get("pv_por_nex", 0)
            san_por_lp = info_grau.get("san_por_nex", 0)
            pe_por_lp = info_grau.get("pe_por_nex", 0)
        else:
            pv_por_lp = info_classe.get("pv_por_nex", 0)
            san_por_lp = info_classe.get("san_por_nex", 0)
            pe_por_lp = info_classe.get("pe_por_nex", 0)

        # -----------------------------------------------------------------
        # 3. Valores iniciais da classe (base)
        # -----------------------------------------------------------------
        pv_inicial = info_classe.get("pv_inicial", 0)
        san_inicial = info_classe.get("san_inicial", 0)
        pe_inicial = info_classe.get("pe_inicial", 0)

        # -----------------------------------------------------------------
        # 4. Bônus por LP (multiplicação)
        # -----------------------------------------------------------------
        pv_por_lp_total = lp_base * pv_por_lp
        san_por_lp_total = lp_base * san_por_lp
        pe_por_lp_total = lp_base * pe_por_lp

        # -----------------------------------------------------------------
        # 5. Bônus especiais do Grau (Vigor e Presença)
        # -----------------------------------------------------------------
        bonus_vigor = info_grau.get("bonus_vigor", {})
        bonus_presenca = info_grau.get("bonus_presenca", {})

        pv_bonus_vigor = bonus_vigor.get("pv_por_vigor", 0) * vig
        pe_bonus_presenca = bonus_presenca.get("pe_por_presenca", 0) * pre

        # -----------------------------------------------------------------
        # 6. PE adicional por feitiços concedidos pelo NEX
        # -----------------------------------------------------------------
        pe_feiticos = self.ficha.get("totais_nex", {}).get("feiticos", 0)

        # -----------------------------------------------------------------
        # 7. Cálculo final
        # -----------------------------------------------------------------
        pv_max = pv_inicial + pv_por_lp_total + pv_bonus_vigor
        san_max = san_inicial + san_por_lp_total
        pe_max = pe_inicial + pe_por_lp_total + pe_bonus_presenca + pe_feiticos

        # Se o Grau não forneceu multiplicadores, mantém LP (fallback)
        if pv_por_lp == 0 and pv_bonus_vigor == 0:
            pv_max = lp_base
        if san_por_lp == 0:
            san_max = lp_base

        # -----------------------------------------------------------------
        # 8. Atualiza estado e barras
        # -----------------------------------------------------------------
        estado = self.ficha.setdefault("estado", {})
        estado["pv_maximo"] = pv_max
        estado["san_maximo"] = san_max
        estado["pe_maximo"] = pe_max

        estado["pv_atual"] = min(estado.get("pv_atual", pv_max), pv_max)
        estado["san_atual"] = min(estado.get("san_atual", san_max), san_max)
        estado["pe_atual"] = min(estado.get("pe_atual", pe_max), pe_max)

        for chave, barra in self._barras.items():
            if chave == "pv":
                barra.set_valores(estado["pv_atual"], pv_max)
            elif chave == "san":
                barra.set_valores(estado["san_atual"], san_max)
            elif chave == "pe":
                barra.set_valores(estado["pe_atual"], pe_max)
    
    def _recalcular_tudo(self):
        """Recalcula bônus, totais NEX e recursos máximos, resetando atuais."""
        # Recalcula totais NEX e LP base
        self._recalcular_totais_nex()

        # Recalcula bônus de passivas e skill tree
        bonus_passivas = self._calcular_bonus_passivas()
        bonus_skilltree = self.recalcular_bonus_skilltree()

        bonus_total = {}
        for fonte in (bonus_passivas, bonus_skilltree):
            for alvo, valor in fonte.items():
                bonus_total[alvo] = bonus_total.get(alvo, 0) + valor

        self.ficha["bonus_passivos"] = bonus_total
        self._salvar()

        # Atualiza recursos com o LP total (já incluso bônus)
        self._atualizar_recursos_por_grau_e_nex()

        # Reseta valores atuais para os máximos
        estado = self.ficha.get("estado", {})
        estado["pv_atual"] = estado.get("pv_maximo", 0)
        estado["san_atual"] = estado.get("san_maximo", 0)
        estado["pe_atual"] = estado.get("pe_maximo", 0)

        for chave, barra in self._barras.items():
            if chave == "pv":
                barra.set_valores(estado["pv_atual"], estado["pv_maximo"])
            elif chave == "san":
                barra.set_valores(estado["san_atual"], estado["san_maximo"])
            elif chave == "pe":
                barra.set_valores(estado["pe_atual"], estado["pe_maximo"])

        # Atualiza painéis de resumo
        for painel in self._paineis_aba.values():
            if isinstance(painel, PainelResumo):
                painel._construir()

    def _debug_popup(self, event=None):
        """Exibe um popup com o conteúdo completo da ficha (JSON formatado) + testes de fórmula."""
        popup = ctk.CTkToplevel(self.app)
        popup.title("Debug - Ficha Completa")
        popup.geometry("700x600")
        popup.minsize(500, 400)
        popup.after(100, popup.grab_set)

        # Frame principal
        main = ctk.CTkFrame(popup, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(main, text="📋 Conteúdo da ficha (JSON)",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 8))

        # Caixa de texto somente leitura com scroll
        textbox = ctk.CTkTextbox(main, font=ctk.CTkFont(size=12, family="Courier"),
                                 fg_color="#1a1a1a", corner_radius=8,
                                 border_width=1, border_color="#333333",
                                 height=300)
        textbox.pack(fill="x", expand=False, pady=(0, 10))

        # Converte a ficha para JSON formatado
        dados_exibicao = {k: v for k, v in self.ficha.items() if k != "_arquivo"}
        json_str = json.dumps(dados_exibicao, indent=4, ensure_ascii=False)
        textbox.insert("1.0", json_str)
        textbox.configure(state="disabled")

        # Botão para testar fórmulas
        def testar_formulas():
            contexto = construir_contexto_base(self.ficha)
            resultados = []
            # Testes básicos
            formula1 = [{"tipo": "variavel", "valor": "LP"}, {"tipo": "operador", "valor": "*"}, {"tipo": "constante", "valor": 2}]
            r1 = avaliar_formula(formula1, contexto)
            resultados.append(f"LP * 2 = {r1}")

            formula2 = [{"tipo": "variavel", "valor": "LP"}, {"tipo": "operador", "valor": "*"},
                        {"tipo": "expressao", "valor": [{"tipo": "variavel", "valor": "AB"}, {"tipo": "operador", "valor": "/"}, {"tipo": "constante", "valor": 2}]}]
            r2 = avaliar_formula(formula2, contexto)
            resultados.append(f"LP * (AB/2) = {r2}")

            resultados.append(f"GRAU = {contexto['GRAU']}")
            resultados.append(f"NEX = {contexto['NEX']}")
            resultados.append(f"LP = {contexto['LP']}")
            resultados.append(f"AB (INT) = {contexto['AB']}")

            msg = "\n".join(resultados)
            ctk.CTkLabel(main, text=msg, font=ctk.CTkFont(size=12), justify="left").pack(pady=5)

        ctk.CTkButton(main, text="🧪 Testar Fórmulas (avaliar_formula)",
                      command=testar_formulas).pack(pady=5)

        # Botão fechar
        ctk.CTkButton(main, text="Fechar", width=100,
                      command=popup.destroy).pack(pady=(10, 0))
