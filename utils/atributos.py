ATRIBUTOS_BASE = {
    "AGI": {"nome": "AGILIDADE", "valor": 1},
    "FOR": {"nome": "FORÇA",     "valor": 1},
    "INT": {"nome": "INTELECTO", "valor": 1},
    "VIG": {"nome": "VIGOR",     "valor": 1},
    "PRE": {"nome": "PRESENÇA",  "valor": 1},
}

LIMITE_NORMAL = 13
LIMITE_ABSOLUTO = 14  # só alcançável via habilidade especial

def calcular_pontos_disponiveis(totais_nex: dict) -> int:
    """4 pontos base + o que o NEX concede."""
    return 4 + totais_nex.get("pontos_atributo", 0)

def atributos_iniciais() -> dict:
    """Retorna uma cópia limpa dos atributos base — sempre começa em 1."""
    return {sigla: dict(dados) for sigla, dados in ATRIBUTOS_BASE.items()}

def pode_aumentar(pontos_disponiveis: int, valor_atual: int) -> bool:
    return pontos_disponiveis > 0 and valor_atual < LIMITE_NORMAL

def pode_diminuir(valor_atual: int) -> bool:
    return valor_atual > 0

def adicionar_pontos_extras(pontos_disponiveis: int, quantidade: int) -> int:
    """Adiciona pontos extras ao pool disponível — mínimo de 0."""
    resultado = pontos_disponiveis + quantidade
    return max(0, resultado)

def ajustar_atributo(atributos: dict, sigla: str, delta: int, pontos_disponiveis: int):
    """
    Tenta aplicar o delta (+1 ou -1) no atributo.
    Retorna (atributos, pontos_disponiveis) atualizados, ou None se inválido.
    """
    valor_atual = atributos[sigla]["valor"]

    if delta > 0 and not pode_aumentar(pontos_disponiveis, valor_atual):
        return None
    if delta < 0 and not pode_diminuir(valor_atual):
        return None

    atributos[sigla]["valor"] += delta
    pontos_disponiveis -= delta  # se delta=-1, pontos_disponiveis aumenta em 1
    return atributos, pontos_disponiveis

def atributos_validos(pontos_disponiveis: int) -> bool:
    """Verifica se o jogador distribuiu todos os pontos antes de avançar."""
    return pontos_disponiveis == 0