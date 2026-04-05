import json
import os

CAMINHO_GRAUS = os.path.join(os.path.dirname(__file__), "..", "data", "graus.json")

def carregar_graus() -> dict:
    with open(CAMINHO_GRAUS, "r", encoding="utf-8") as f:
        return json.load(f)

def listar_graus(graus: dict) -> list:
    return list(graus["graus"].keys())

def listar_classes(graus: dict) -> list:
    return graus["classes_disponiveis"]

def tem_classes(nome_grau: str, graus: dict) -> bool:
    """Verifica se o grau exige escolha de classe (Especial e Ultra Especial)."""
    return "classes" in graus["graus"][nome_grau]

def calcular_pv_pe_san(nex_str: str, nome_grau: str, nome_classe: str,
                        vigor: int, presenca: int, graus: dict) -> dict:
    nex = float(nex_str.replace("%", "").replace(",", "."))
    dados = graus["graus"][nome_grau]

    if tem_classes(nome_grau, graus):
        dados_classe = dados["classes"][nome_classe]
        pv_nex  = dados_classe["pv_por_nex"]
        san_nex = dados_classe["san_por_nex"]
        pe_nex  = dados_classe["pe_por_nex"]
    else:
        pv_nex  = dados.get("pv_por_nex", 0)
        san_nex = dados.get("san_por_nex", 0)
        pe_nex  = dados.get("pe_por_nex", 0)

    pv  = pv_nex  * nex
    san = san_nex * nex
    pe  = pe_nex  * nex

    if bonus := dados.get("bonus_vigor"):
        pv += vigor * bonus["pv_por_vigor"]
    if bonus := dados.get("bonus_presenca"):
        pe += presenca * bonus["pe_por_presenca"]

    return {"pv": int(pv), "san": int(san), "pe": int(pe)}

def extras_do_grau(nome_grau: str, graus: dict) -> dict:
    dados = graus["graus"][nome_grau]
    return {
        "graus_treinamento": dados.get("graus_treinamento", 0),
        "encantamentos":     dados.get("encantamentos", 0),
        "encantamentos_ab":  dados.get("encantamentos_ab"),
        "maldicoes":         dados.get("maldicoes", 0),
        "pontos_atributo":   dados.get("pontos_atributo", 0),
    }