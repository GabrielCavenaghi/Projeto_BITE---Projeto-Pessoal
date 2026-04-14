# utils/tecnicas.py
import random
import re
from ficha import avaliar_formula, construir_contexto_base, rolar_atributo
from utils.Efeitos_Scalling import string_para_tokens
from utils.dados import avaliar_dado_str
# ══════════════════════════════════════════════════════════════════════════════
# Funções de execução por tipo
# ══════════════════════════════════════════════════════════════════════════════

def executar_tecnica(tecnica: dict, ficha: dict) -> dict:
    tipo = tecnica.get("tipo_mecanica")
    if tipo == "Ataque":
        return _executar_ataque(tecnica, ficha)
    elif tipo == "Teste de Resistência":
        return _executar_tr(tecnica, ficha)
    elif tipo == "Cura":
        return _executar_cura(tecnica, ficha)
    elif tipo == "Passiva":
        return _executar_passiva(tecnica, ficha)
    elif tipo == "Extra":
        return _executar_extra(tecnica, ficha)
    else:
        return {"sucesso": False, "mensagem": "Tipo de técnica não implementado."}

def _executar_ataque(tecnica: dict, ficha: dict) -> dict:
    params = tecnica.get("parametros", {})
    ctx = construir_contexto_base(ficha)

    pericia = params.get("pericia_ataque", "Luta")
    bonus_pericia = ctx.get(pericia, 0)

    margem = params.get("margem_ameaca", 20)
    if margem < 1:
        margem = 1
    valor_critico_min = 21 - margem

    multiplicador = params.get("multiplicador_critico", 2)

    atributo_map = {"Luta": "FOR", "Pontaria": "AGI"}
    atributo = atributo_map.get(pericia, "FOR")
    valor_atributo = ctx.get(atributo, 1)

    resultado_ataque = rolar_atributo(valor_atributo, treinamento=bonus_pericia, bonus=0)
    d20_result = resultado_ataque["escolhido"]
    total_ataque = resultado_ataque["total"]

    critico = (d20_result >= valor_critico_min)
    falha_critica = (d20_result == 1)

    aplicar_passo = params.get("aplicar_passo", False)
    dano_formula_str = params.get("dano", "0")
    dano_total = avaliar_dado_str(dano_formula_str, ficha=ficha, contexto=ctx, aplicar_passo=aplicar_passo, tipo_efeito="tecnica", params=params)

    if critico:
        dano_total *= multiplicador

    dados_rolados = resultado_ataque["dados"]
    msg_ataque = f"Ataque com {pericia}: {d20_result} + {bonus_pericia} = {total_ataque}"
    if critico:
        msg_ataque += " (CRÍTICO!)"
    elif falha_critica:
        msg_ataque += " (FALHA CRÍTICA!)"

    mensagem = f"{msg_ataque}\nDados: {dados_rolados}\nDano: {dano_total}"

    return {
        "sucesso": True,
        "mensagem": mensagem,
        "detalhes": {
            "d20": d20_result,
            "bonus": bonus_pericia,
            "total": total_ataque,
            "critico": critico,
            "falha_critica": falha_critica,
            "dano": dano_total
        }
    }

def _executar_tr(tecnica: dict, ficha: dict) -> dict:
    params = tecnica.get("parametros", {})
    ctx = construir_contexto_base(ficha)
    aplicar_passo = params.get("aplicar_passo", False)
    dano_formula_str = params.get("dano", "0")
    dano_total = avaliar_dado_str(dano_formula_str, ficha=ficha, contexto=ctx, aplicar_passo=aplicar_passo, tipo_efeito="tecnica", params=params)

    dt = int(ctx.get("DT_TECNICA", 10))

    mensagem = (
        f"{tecnica['nome']} causa {dano_total} de dano.\n"
        f"Teste de Resistência (DT {dt}) para reduzir à metade."
    )

    return {
        "sucesso": True,
        "mensagem": mensagem,
        "detalhes": {
            "dano": dano_total,
            "dt": dt
        }
    }

def _executar_cura(tecnica: dict, ficha: dict) -> dict:
    params = tecnica.get("parametros", {})
    ctx = construir_contexto_base(ficha)
    aplicar_passo = params.get("aplicar_passo", False)
    cura_formula_str = params.get("cura", params.get("dano", "0"))
    cura_total = avaliar_dado_str(cura_formula_str, ficha=ficha, contexto=ctx, aplicar_passo=aplicar_passo, tipo_efeito="tecnica", params=params)

    return {
        "sucesso": True,
        "mensagem": f"{tecnica['nome']} cura {cura_total} pontos de vida.",
        "detalhes": {"cura": cura_total}
    }

def _executar_passiva(tecnica: dict, ficha: dict) -> dict:
    return {
        "sucesso": True,
        "mensagem": f"Passiva '{tecnica['nome']}' está ativa.",
        "detalhes": {}
    }

def _executar_extra(tecnica: dict, ficha: dict) -> dict:
    return {
        "sucesso": True,
        "mensagem": f"Efeito extra: {tecnica.get('descricao', '')}",
        "detalhes": {}
    }