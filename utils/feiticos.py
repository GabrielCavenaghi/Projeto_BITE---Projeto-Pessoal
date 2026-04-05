import json
import os

CAMINHO_FEITICOS = os.path.join(os.path.dirname(__file__), "..", "data", "feiticos.json")

# Ordem de grau do mais fraco ao mais forte
ORDEM_GRAUS = ["GRAU 4", "GRAU 3", "GRAU 2", "GRAU 1",
               "SEMI ESPECIAL", "ESPECIAL", "ULTRA ESPECIAL"]

GRAU_PARA_VERSOES = {
    "Grau 4":             [],
    "Grau 3":             ["GRAU 3"],
    "Grau 2":             ["GRAU 3", "GRAU 2"],
    "Grau 1":             ["GRAU 3", "GRAU 2", "GRAU 1"],
    "Grau Semi Especial": ["GRAU 3", "GRAU 2", "GRAU 1", "SEMI ESPECIAL"],
    "Grau Especial":      ["GRAU 3", "GRAU 2", "GRAU 1", "SEMI ESPECIAL", "ESPECIAL"],
    "Grau Ultra Especial":["GRAU 3", "GRAU 2", "GRAU 1", "SEMI ESPECIAL", "ESPECIAL", "ULTRA ESPECIAL"],
}

def carregar_feiticos() -> list:
    with open(CAMINHO_FEITICOS, "r", encoding="utf-8") as f:
        return json.load(f)

def feiticos_por_classe(feiticos: list) -> dict:
    """Agrupa feitiços por classe mantendo a ordem do JSON."""
    resultado = {}
    for f in feiticos:
        classe = f["classe"]
        resultado.setdefault(classe, []).append(f)
    return resultado

def versoes_disponiveis(feitico: dict, grau_personagem: str) -> list:
    """Retorna as chaves de versão desbloqueadas para o grau do personagem."""
    versoes_grau = GRAU_PARA_VERSOES.get(grau_personagem, [])
    return [v for v in versoes_grau if v in feitico.get("versoes", {})]

def abas_disponiveis(feiticos: list, classe_personagem: str) -> list:
    """
    Retorna as abas na ordem: classe do personagem primeiro, Geral por último,
    outras classes no meio.
    """
    classes = list(dict.fromkeys(f["classe"] for f in feiticos))
    ordenadas = []
    if classe_personagem in classes:
        ordenadas.append(classe_personagem)
    for c in classes:
        if c != classe_personagem and c != "Geral":
            ordenadas.append(c)
    if "Geral" in classes:
        ordenadas.append("Geral")
    return ordenadas