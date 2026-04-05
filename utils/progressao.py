import json
import os

CAMINHO_PROGRESSAO = os.path.join(os.path.dirname(__file__), "..", "data", "progressao_nex.json")

def carregar_progressao() -> dict:
    with open(CAMINHO_PROGRESSAO, "r", encoding="utf-8") as f:
        return json.load(f)

def calcular_totais_ate_nex(nex_alvo: str, progressao: dict = None) -> dict:
    """
    Soma tudo que o personagem ganhou desde 5% até o NEX escolhido.
    Se progressao não for passado, carrega automaticamente do JSON.
    """
    if progressao is None:
        progressao = carregar_progressao()

    totais = {
        "pontos_atributo":       0,
        "feiticos":              0,
        "graus_treinamento":     0,
        "habilidade_trilha":     0,
        "afinidade":             0,
        "expansao_modo":         0,
        "melhorias_superiores":  0,
        "habilidades_lendarias": 0,
        "habilidade_tecnica_n6": 0,
    }

    for nex, ganhos in progressao.items():
        for chave, valor in ganhos.items():
            if chave in totais:
                totais[chave] += valor
        if nex == nex_alvo:
            break

    return totais

def calcular_ganhos_nex(nex: str, progressao: dict = None) -> dict:
    """
    Retorna só o que aquele NEX específico concede, sem acumular.
    Útil pra mostrar 'o que vou ganhar ao subir pra esse nível'.
    """
    if progressao is None:
        progressao = carregar_progressao()
    return progressao.get(nex, {})