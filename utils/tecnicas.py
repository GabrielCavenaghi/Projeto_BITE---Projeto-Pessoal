# utils/tecnicas.py
from ficha import avaliar_formula, construir_contexto_base, rolar_atributo
import random

def executar_tecnica(tecnica: dict, ficha: dict) -> dict:
    """Roteia para a função específica conforme o tipo_mecanica."""
    tipo = tecnica.get("tipo_mecanica")
    if tipo == "Ataque":
        return _executar_ataque(tecnica, ficha)
    elif tipo == "Teste de Resistencia":
        return _executar_tr(tecnica, ficha)
    elif tipo == "Cura":
        return _executar_cura(tecnica, ficha)
    elif tipo == "Passiva":
        return _executar_passiva(tecnica, ficha)
    elif tipo == "Extra":
        return _executar_extra(tecnica, ficha)
    else:
        return {"sucesso": False, "mensagem": "Tipo de técnica não implementado."}
    
def _executar_tr(tecnica: dict, ficha: dict) -> dict:
    params = tecnica.get("parametros", {})
    contexto = construir_contexto_base(ficha)

    # Calcula dano
    dano_formula = params.get("dano", "0")
    dano_total = avaliar_formula(dano_formula, contexto)

    # Simula rolagem de resistência do alvo (apenas sugestão visual)
    # Aqui você pode optar por apenas retornar o dano e deixar o mestre rolar
    return {
        "sucesso": True,
        "mensagem": f"{tecnica['nome']} causa {dano_total} de dano. Teste de {params.get('atributo_teste')} ({params.get('atributo_resistencia')}) para reduzir.",
        "detalhes": {
            "dano": dano_total,
            "atributo_teste": params.get("atributo_teste"),
            "atributo_resistencia": params.get("atributo_resistencia"),
            "efeito_sucesso": params.get("efeito_sucesso", "metade_dano"),
            "condicao_falha": params.get("condicao_falha")
        }
    }

#def _executar_ataque(tecnica: dict, ficha: dict) -> dict:

#def _executar_cura(tecnica: dict, ficha: dict) -> dict:

#def _executar_passiva(tecnica: dict, ficha: dict) -> dict:

#def _executar_extra(tecnica: dict, ficha: dict) -> dict:
