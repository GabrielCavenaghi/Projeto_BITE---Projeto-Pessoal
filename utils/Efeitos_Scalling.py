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
    # Resistências
    "DEF": {"nome": "Defesa", "categoria": "Resistências"},
    "TR": {"nome": "Testes de Resistência", "categoria": "Resistências"},
    "RD_GERAL": {"nome": "RD Geral", "categoria": "Resistências"},
    "RD_PARANORMAL": {"nome": "RD Paranormal", "categoria": "Resistências"},
    "RD_MENTAL": {"nome": "RD Mental", "categoria": "Resistências"},
    "RD_FISICO": {"nome": "RD Físico", "categoria": "Resistências"},
    "CURA_ACELERADA": {"nome": "Cura Acelerada", "categoria": "Resistências"},

    # Status Máximos
    "PV_MAX": {"nome": "PV Máximo", "categoria": "Status"},
    "SAN_MAX": {"nome": "Sanidade Máxima", "categoria": "Status"},
    "PE_MAX": {"nome": "PE Máximo", "categoria": "Status"},

    #Tecnica:    
    "PASSO_DANO_TECNICA": {"nome": "Passo de Dano (Técnica)", "categoria": "Técnica"},
    "DADO_TECNICA": {"nome": "Dados de Dano Técnica", "categoria": "Técnica"},
    "DADO_POR_DADO_TECNICA": {"nome": "Dados de Dano Por Dado (Técnica)", "categoria": "Técnica"},
    "DANO_PERCENTUAL_TECNICA": {"nome": "Bônus de Dano Percentual (Técnica)", "categoria": "Técnica"},

    #Corpo a Corpo:
    "PASSO_DANO_CORPO": {"nome": "Passo de Dano (Corpo a Corpo)", "categoria": "Corpo a Corpo"},
    "DADO_CORPO": {"nome": "Dados de Dano Corpo a Corpo", "categoria": "Corpo a Corpo"},
    "DADO_POR_DADO_CORPO": {"nome": "Dados de Dano Por Dado (Corpo a Corpo)", "categoria": "Corpo a Corpo"},
    "DANO_PERCENTUAL_CORPO": {"nome": "Bônus de Dano Percentual (Corpo a Corpo)", "categoria": "Corpo a Corpo"},

    #Desarmado:    
    "PASSO_DANO_DESARMADO": {"nome": "Passo de Dano (Desarmado)", "categoria": "Desarmado"},
    "DADO_DESARMADO": {"nome": "Dados de Dano Desarmado", "categoria": "Desarmado"},
    "DADO_POR_DADO_DESARMADO": {"nome": "Dados de Dano Por Dado (Desarmado)", "categoria": "Desarmado"},
    "DANO_PERCENTUAL_DESARMADO": {"nome": "Bônus de Dano Percentual (Desarmado)", "categoria": "Desarmado"},

    #Estilo de Luta:
    "PASSO_DANO_ESTILO_LUTA": {"nome": "Passo de Dano (Estilo de Luta)", "categoria": "Estilo de Luta"},
    "DADO_ESTILO_LUTA": {"nome": "Dados de Dano Estilo de Luta", "categoria": "Estilo de Luta"},
    "DADO_POR_DADO_ESTILO_LUTA": {"nome": "Dados de Dano Por Dado (Estilo de Luta)", "categoria": "Estilo de Luta"},
    "DANO_PERCENTUAL_ESTILO_LUTA": {"nome": "Bônus de Dano Percentual (Estilo de Luta)", "categoria": "Estilo de Luta"},

    #Invocação:
    "PASSO_DANO_INVOCACAO": {"nome": "Passo de Dano (Invocação)", "categoria": "Invocação"},
    "DADO_INVOCACAO": {"nome": "Dados de Dano Invocação", "categoria": "Invocação"},
    "DADO_POR_DADO_INVOCACAO": {"nome": "Dados de Dano Por Dado (Invocação)", "categoria": "Invocação"},
    "PERCENTUAL_INVOCACAO": {"nome": "Bônus de Dano Percentual (Invocação)", "categoria": "Invocação"},
    
    #Maldição:
    "PASSO_MALDICAO": {"nome": "Passo de Dano (Maldição)", "categoria": "Maldição"},
    "DADO_MALDICAO": {"nome": "Dados de Dano Maldição", "categoria": "Maldição"},
    "DADO_POR_DADO_MALDICAO": {"nome": "Dados de Dano Por Dado (Maldição)", "categoria": "Maldição"},
    "PERCENTUAL_MALDICAO": {"nome": "Bônus de Dano Percentual (Maldição)", "categoria": "Maldição"},

    #Shinobi:
    "PASSO_SHINOBI": {"nome": "Passo de Dano (Shinobi)", "categoria": "Shinobi"},
    "DADO_SHINOBI": {"nome": "Dados de Dano Shinobi", "categoria": "Shinobi"},
    "DADO_POR_DADO_SHINOBI": {"nome": "Dados de Dano Por Dado (Shinobi)", "categoria": "Shinobi"},
    "PERCENTUAL_SHINOBI": {"nome": "Bônus de Dano Percentual (Shinobi)", "categoria": "Shinobi"},

    #Energia Amaldiçoada:
    "PASSO_ENERGIA_AMALDICOADA": {"nome": "Passo (Energia Amaldiçoada)", "categoria": "Energia Amaldiçoada"},
    "DADO_ENERGIA_AMALDICOADA": {"nome": "Dados de Dano Energia Amaldiçoada", "categoria": "Energia Amaldiçoada"},
    "DADO_POR_DADO_ENERGIA_AMALDICOADA": {"nome": "Dados de Dano Por Dado (Energia Amaldiçoada)", "categoria": "Energia Amaldiçoada"},
    "PERCENTUAL_ENERGIA_AMALDICOADA": {"nome": "Bônus de Dano Percentual (Energia Amaldiçoada)", "categoria": "Energia Amaldiçoada"},
    
    #Geral:
    "PASSO_DANO_GERAL": {"nome": "Passo de Dano Geral", "categoria": "Geral"},
    "DADO_GERAL": {"nome": "Dados de Dano Geral", "categoria": "Geral"},
    "DADO_POR_DADO_GERAL": {"nome": "Dados de Dano Por Dado (Geral)", "categoria": "Geral"},
    "DANO_PERCENTUAL_GERAL": {"nome": "Bônus de Dano Percentual Geral", "categoria": "Geral"},


    # Atributos de Combate
    "MARGEM_AMEAÇA": {"nome": "Margem de Ameaça", "categoria": "Combate"},
    "MULTIPLICADOR_CRITICO": {"nome": "Multiplicador de Crítico", "categoria": "Combate"},
    "ALCANCE": {"nome": "Alcance", "categoria": "Combate"},
    "DESLOCAMENTO": {"nome": "Deslocamento", "categoria": "Combate"},

    # Perícias Específicas
    "PERICIA_ACROBACIA": {"nome": "Acrobacia", "categoria": "Perícias"},
    "PERICIA_ADESTRAMENTO": {"nome": "Adestramento", "categoria": "Perícias"},
    "PERICIA_ARTES": {"nome": "Artes", "categoria": "Perícias"},
    "PERICIA_ATLETISMO": {"nome": "Atletismo", "categoria": "Perícias"},
    "PERICIA_ATUALIDADES": {"nome": "Atualidades", "categoria": "Perícias"},
    "PERICIA_CIENCIAS": {"nome": "Ciências", "categoria": "Perícias"},
    "PERICIA_CRIME": {"nome": "Crime", "categoria": "Perícias"},
    "PERICIA_DIPLOMACIA": {"nome": "Diplomacia", "categoria": "Perícias"},
    "PERICIA_ENGANACAO": {"nome": "Enganação", "categoria": "Perícias"},
    "PERICIA_FORTITUDE": {"nome": "Fortitude", "categoria": "Perícias"},
    "PERICIA_FURTIVIDADE": {"nome": "Furtividade", "categoria": "Perícias"},
    "PERICIA_INICIATIVA": {"nome": "Iniciativa", "categoria": "Perícias"},
    "PERICIA_INTIMIDACAO": {"nome": "Intimidação", "categoria": "Perícias"},
    "PERICIA_INTUICAO": {"nome": "Intuição", "categoria": "Perícias"},
    "PERICIA_INVESTIGACAO": {"nome": "Investigação", "categoria": "Perícias"},
    "PERICIA_LUTA": {"nome": "Luta", "categoria": "Perícias"},
    "PERICIA_MEDICINA": {"nome": "Medicina", "categoria": "Perícias"},
    "PERICIA_OCULTISMO": {"nome": "Ocultismo", "categoria": "Perícias"},
    "PERICIA_PERCEPCAO": {"nome": "Percepção", "categoria": "Perícias"},
    "PERICIA_PILOTAGEM": {"nome": "Pilotagem", "categoria": "Perícias"},
    "PERICIA_PONTARIA": {"nome": "Pontaria", "categoria": "Perícias"},
    "PERICIA_PROFISSAO": {"nome": "Profissão", "categoria": "Perícias"},
    "PERICIA_ENERGIA_AMALDICOADA": {"nome": "Energia Amaldiçoada", "categoria": "Perícias"},
    "PERICIA_REFLEXOS": {"nome": "Reflexos", "categoria": "Perícias"},
    "PERICIA_RELIGIAO": {"nome": "Religião", "categoria": "Perícias"},
    "PERICIA_SOBREVIVENCIA": {"nome": "Sobrevivência", "categoria": "Perícias"},
    "PERICIA_TATICA": {"nome": "Tática", "categoria": "Perícias"},
    "PERICIA_TECNOLOGIA": {"nome": "Tecnologia", "categoria": "Perícias"},
    "PERICIA_VONTADE": {"nome": "Vontade", "categoria": "Perícias"},

    # DT (Dificuldade de Testes)
    "DT": {"nome": "DT (Dificuldade de Testes)", "categoria": "Geral"},
    "DT_HABILIDADES_TECNICA": {"nome": "DT (Habilidades de Técnica)", "categoria": "Geral"},

    # Atributos
    "AGI": {"nome": "Agilidade", "categoria": "Atributos"},
    "FOR": {"nome": "Força", "categoria": "Atributos"},
    "INT": {"nome": "Inteligência", "categoria": "Atributos"},
    "VIG": {"nome": "Vigor", "categoria": "Atributos"},
    "PRE": {"nome": "Presença", "categoria": "Atributos"},

    # Outros
    "CARACTERISTICA_INVOCACAO": {"nome": "Característica de Invocação", "categoria": "Invocação"},
    "LP": {"nome": "LP", "categoria": "Outros"},
}

OPERACOES_PERMITIDAS = ["+", "-"]

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
    "DT",           # DT base (sem modificadores de habilidades ou efeitos)
    "DT_TECNICA",   # DT específico para habilidades de técnica
    "PB",           # Perícia Base
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