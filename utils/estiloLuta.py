# utils/estiloLuta.py
import random
from ficha import construir_contexto_base, rolar_atributo
from utils.dados import avaliar_dado_str

def executar_estilo_luta(hab: dict, ficha: dict) -> dict:
    """
    Executa uma habilidade de estilo de luta conforme seu tipo_mecanica.
    Retorna um dicionário com o resultado formatado para exibição.
    """
    tipo = hab.get("tipo_mecanica")
    if tipo == "Ataque":
        return _executar_ataque_estilo(hab, ficha)
    elif tipo == "Teste de Resistência":
        return _executar_tr_estilo(hab, ficha)
    elif tipo == "Passiva":
        return _executar_passiva_estilo(hab, ficha)
    else:
        return {"sucesso": False, "mensagem": "Tipo de habilidade não implementado."}

def _executar_ataque_estilo(hab: dict, ficha: dict) -> dict:
    params = hab.get("parametros", {})
    ctx = construir_contexto_base(ficha)

    # Perícia de ataque (padrão Luta)
    pericia = params.get("pericia_ataque", "Luta")
    bonus_pericia = ctx.get(pericia, 0)

    # Margem de ameaça (padrão 20)
    margem = params.get("margem_ameaca", 20)
    if margem < 1:
        margem = 1
    valor_critico_min = 21 - margem

    # Multiplicador de crítico (padrão 2)
    multiplicador = params.get("multiplicador_critico", 2)

    # Atributo para vantagem/desvantagem (mapeamento básico)
    atributo_map = {"Luta": "FOR", "Pontaria": "AGI"}
    atributo = atributo_map.get(pericia, "FOR")
    valor_atributo = ctx.get(atributo, 1)

    # Rolagem do d20
    resultado_ataque = rolar_atributo(valor_atributo, treinamento=bonus_pericia, bonus=0)
    d20_result = resultado_ataque["escolhido"]
    total_ataque = resultado_ataque["total"]

    critico = (d20_result >= valor_critico_min)
    falha_critica = (d20_result == 1)

    # Dano
    aplicar_passo = params.get("aplicar_passo", False)
    dano_formula = params.get("dano", "0")
    dano_total = avaliar_dado_str(
        formula_str=dano_formula,
        contexto=ctx,
        aplicar_passo=aplicar_passo,
        tipo_efeito="estilo_luta",    # importante para aplicar bônus de estilo de luta
        params=params
    )
    if critico:
        dano_total = int(dano_total * multiplicador)

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

def _executar_tr_estilo(hab: dict, ficha: dict) -> dict:
    params = hab.get("parametros", {})
    ctx = construir_contexto_base(ficha)

    aplicar_passo = params.get("aplicar_passo", False)
    dano_formula = params.get("dano", "0")
    dano_total = avaliar_dado_str(
        formula_str=dano_formula,
        contexto=ctx,
        aplicar_passo=aplicar_passo,
        tipo_efeito="estilo_luta",
        params=params
    )

    # DT padrão (a mesma usada para técnicas)
    dt = int(ctx.get("DT_TECNICA", 10))

    mensagem = (
        f"{hab['nome']} causa {dano_total} de dano.\n"
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

def _executar_passiva_estilo(hab: dict, ficha: dict) -> dict:
    # Passivas de estilo são gerenciadas pelo sistema de efeitos (Efeitos_Scalling)
    # e ativadas/desativadas via checkbox no painel.
    return {
        "sucesso": True,
        "mensagem": f"Passiva '{hab['nome']}' está ativa. Seus efeitos são aplicados automaticamente.",
        "detalhes": {}
    }