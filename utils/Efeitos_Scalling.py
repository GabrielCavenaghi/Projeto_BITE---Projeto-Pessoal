import re

# utils/Efeitos_Scaling.py
"""
Módulo para gerenciamento de efeitos passivos (buffs/debuffs) reutilizáveis.
Fornece constantes, validação e avaliação de efeitos baseados em fórmulas.
"""

# ══════════════════════════════════════════════════════════════════════════════
# Constantes e Definições
# ══════════════════════════════════════════════════════════════════════════════

# Alvos disponíveis para efeitos passivos.
# Mapeia identificador interno -> nome amigável e categoria (opcional).
ALVOS_DISPONIVEIS = {
    # Defesas e Resistências
    "DEF": {"nome": "Defesa", "categoria": "Defesas"},
    "TR": {"nome": "Testes de Resistência", "categoria": "Defesas"},
    "RD_GERAL": {"nome": "RD Geral", "categoria": "Resistências"},
    "RD_PARANORMAL": {"nome": "RD Paranormal", "categoria": "Resistências"},
    "RD_MENTAL": {"nome": "RD Mental", "categoria": "Resistências"},
    "RD_FISICO": {"nome": "RD Físico", "categoria": "Resistências"},

    # Status Máximos
    "PV_MAX": {"nome": "PV Máximo", "categoria": "Status"},
    "SAN_MAX": {"nome": "Sanidade Máxima", "categoria": "Status"},
    "PE_MAX": {"nome": "PE Máximo", "categoria": "Status"},

    # Passos de Dano
    "PASSO_DANO_TECNICA": {"nome": "Passo de Dano (Técnica)", "categoria": "Dano"},
    "PASSO_DANO_CORPO": {"nome": "Passo de Dano (Corpo a Corpo)", "categoria": "Dano"},
    "PASSO_DANO_DESARMADO": {"nome": "Passo de Dano (Desarmado)", "categoria": "Dano"},
    "PASSO_DANO_INVOCACAO": {"nome": "Passo de Dano (Invocação)", "categoria": "Dano"},
    "PASSO_ENERGIA_AMALDICOADA": {"nome": "Passo (Energia Amaldiçoada)", "categoria": "Dano"},
    "PASSO_MALDICAO": {"nome": "Passo (Maldição)", "categoria": "Dano"},
    "PASSO_SHINOBI": {"nome": "Passo (Shinobi)", "categoria": "Dano"},
    "PASSO_ESTILO_LUTA": {"nome": "Passo de Dano (Estilo de Luta)", "categoria": "Dano"},

    # Atributos de Combate
    "MARGEM_AMEAÇA": {"nome": "Margem de Ameaça", "categoria": "Combate"},
    "MULTIPLICADOR_CRITICO": {"nome": "Multiplicador de Crítico", "categoria": "Combate"},
    "ALCANCE": {"nome": "Alcance", "categoria": "Combate"},
    "DESLOCAMENTO": {"nome": "Deslocamento", "categoria": "Combate"},

    # Perícias Específicas
    "PERICIA_LUTA": {"nome": "Perícia Luta", "categoria": "Perícias"},
    "PERICIA_PONTARIA": {"nome": "Perícia Pontaria", "categoria": "Perícias"},
    "PERICIA_FORTITUDE": {"nome": "Perícia Fortitude", "categoria": "Perícias"},
    "PERICIA_REFLEXOS": {"nome": "Perícia Reflexos", "categoria": "Perícias"},
    "PERICIA_VONTADE": {"nome": "Perícia Vontade", "categoria": "Perícias"},

    # DT (Dificuldade de Testes)
    "DT": {"nome": "DT (Dificuldade de Testes)", "categoria": "Geral"},
    "DT_HABILIDADES_TECNICA": {"nome": "DT (Habilidades de Técnica)", "categoria": "Geral"},

    # Outros
    "CARACTERISTICA_INVOCACAO": {"nome": "Característica de Invocação", "categoria": "Invocação"},
    "DADO_CORPO": {"nome": "Dados de Dano Corpo a Corpo", "categoria": "Dano"},
    "DADO_DESARMADO": {"nome": "Dados de Dano Desarmado", "categoria": "Dano"},
}

# Operações permitidas para efeitos passivos.
# Nota: "*" e "/" podem ser usados em fórmulas, mas como operação principal
# geralmente apenas "+", "-" e "=" fazem sentido para acumular bônus.
OPERACOES_PERMITIDAS = ["+", "-", "="]

# Variáveis que podem ser utilizadas nas fórmulas.
# Estas devem corresponder às chaves retornadas por construir_contexto_base().
# Variáveis que podem ser utilizadas nas fórmulas.
# Estas devem corresponder às chaves retornadas por construir_contexto_base().
VARIAVEIS_BASE = [
    "LP",           # LP total (base + bônus)
    "LP_NATURAL",   # LP base (apenas do NEX)
    "AB",           # Atributo Base
    "GRAU",         # Valor numérico do Grau (1-7)
    "NEX",          # Valor percentual do NEX (ex.: 99.3)
    "AGI", "FOR", "INT", "VIG", "PRE",  # Atributos
    "EA",           # Energia Amaldiçoada (treino + bônus)
    "PODERES_PARANORMAIS"  # Quantidade de poderes paranormais
]

# ══════════════════════════════════════════════════════════════════════════════
# Funções de Validação e Avaliação
# ══════════════════════════════════════════════════════════════════════════════

def validar_efeito(alvo: str, operacao: str, formula: list) -> tuple[bool, str]:
    """
    Verifica se um efeito é válido.
    Retorna (True, "") se válido, ou (False, mensagem_de_erro) se inválido.
    """
    if alvo not in ALVOS_DISPONIVEIS:
        return False, f"Alvo '{alvo}' não é suportado."

    if operacao not in OPERACOES_PERMITIDAS:
        return False, f"Operação '{operacao}' não é permitida para efeitos passivos."

    if not isinstance(formula, list):
        return False, "A fórmula deve ser uma lista de tokens."

    # Validação básica da fórmula (pode ser expandida)
    for token in formula:
        tipo = token.get("tipo")
        if tipo not in ("constante", "variavel", "operador", "expressao"):
            return False, f"Tipo de token inválido na fórmula: {tipo}"
        if tipo == "variavel":
            if token.get("valor") not in VARIAVEIS_BASE:
                return False, f"Variável '{token.get('valor')}' não é permitida."

    return True, ""


def avaliar_efeitos(lista_efeitos: list, contexto: dict) -> dict:
    """
    Avalia uma lista de efeitos e retorna um dicionário com os bônus acumulados.
    Cada efeito deve ser um dicionário com: alvo, operacao, formula.
    """
    # Importação local para evitar dependência circular
    from ficha import avaliar_formula

    bonificacoes = {}

    for efeito in lista_efeitos:
        alvo = efeito["alvo"]
        operacao = efeito["operacao"]
        formula = efeito["formula"]

        # Validação (opcional, mas recomendada)
        valido, msg = validar_efeito(alvo, operacao, formula)
        if not valido:
            print(f"Aviso: Efeito inválido ignorado - {msg}")
            continue

        try:
            valor = avaliar_formula(formula, contexto)
        except Exception as e:
            print(f"Erro ao avaliar fórmula do efeito {alvo}: {e}")
            continue

        if alvo not in bonificacoes:
            bonificacoes[alvo] = 0

        if operacao == "+":
            bonificacoes[alvo] += valor
        elif operacao == "-":
            bonificacoes[alvo] -= valor
        elif operacao == "=":
            bonificacoes[alvo] = valor

    return bonificacoes


def mesclar_bonus(bonus_atual: dict, novos_bonus: dict) -> dict:
    """
    Soma dois dicionários de bônus, retornando um novo dicionário.
    """
    resultado = bonus_atual.copy()
    for alvo, valor in novos_bonus.items():
        resultado[alvo] = resultado.get(alvo, 0) + valor
    return resultado

def string_para_tokens(expr: str) -> list:
    """
    Converte uma string de fórmula matemática em uma lista de tokens
    no formato esperado por avaliar_formula().
    Exemplo: "LP*2+10" -> [
        {"tipo": "variavel", "valor": "LP"},
        {"tipo": "operador", "valor": "*"},
        {"tipo": "constante", "valor": 2},
        {"tipo": "operador", "valor": "+"},
        {"tipo": "constante", "valor": 10}
    ]
    Suporta parênteses e expressões aninhadas.
    """
    expr = expr.replace(" ", "")  # Remove espaços
    if not expr:
        raise ValueError("Fórmula vazia")

    tokens = []
    i = 0
    n = len(expr)

    def parse_expressao(inicio):
        """Parseia uma expressão até encontrar um ')' ou fim da string."""
        nonlocal i
        sub_tokens = []
        while i < n:
            char = expr[i]
            if char == ')':
                i += 1  # consome ')'
                break
            elif char == '(':
                i += 1  # consome '('
                sub_expr = parse_expressao(i)
                sub_tokens.append({"tipo": "expressao", "valor": sub_expr})
            elif char.isalpha() or char == '_':
                # Variável
                j = i
                while j < n and (expr[j].isalnum() or expr[j] == '_'):
                    j += 1
                var = expr[i:j]
                if var not in VARIAVEIS_BASE:
                    raise ValueError(f"Variável desconhecida: '{var}'")
                sub_tokens.append({"tipo": "variavel", "valor": var})
                i = j
                continue
            elif char.isdigit() or char == '.':
                # Número (constante)
                j = i
                dots = 0
                while j < n and (expr[j].isdigit() or expr[j] == '.'):
                    if expr[j] == '.':
                        dots += 1
                        if dots > 1:
                            raise ValueError(f"Número inválido: múltiplos pontos")
                    j += 1
                num_str = expr[i:j]
                try:
                    if '.' in num_str:
                        valor = float(num_str)
                    else:
                        valor = int(num_str)
                except ValueError:
                    raise ValueError(f"Número inválido: '{num_str}'")
                sub_tokens.append({"tipo": "constante", "valor": valor})
                i = j
                continue
            elif char in '+-*/':
                # Operador
                # Verifica se é '//'
                if char == '/' and i + 1 < n and expr[i + 1] == '/':
                    op = '//'
                    i += 2
                else:
                    op = char
                    i += 1
                sub_tokens.append({"tipo": "operador", "valor": op})
                continue
            else:
                raise ValueError(f"Caractere inválido: '{char}'")
        return sub_tokens

    i = 0
    result = parse_expressao(0)
    if i < n:
        # Se sobrou algo que não foi processado (ex.: parêntese extra)
        raise ValueError(f"Caractere inesperado na posição {i}: '{expr[i]}'")
    return result