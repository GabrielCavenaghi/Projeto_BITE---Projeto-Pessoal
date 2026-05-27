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
    
    # Mistura as tags da interface com a do estilo para o cálculo do dano base
    tipos_interface = hab.get("tipos_efeito", [])
    tipos_para_base = list(set(tipos_interface + ["estilo_luta"]))

    pericia = params.get("pericia_ataque", "Luta")
    bonus_pericia = ctx.get(pericia, 0)
    margem = max(params.get("margem_ameaca", 20), 1)
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

    # REFORMULADO: Resgatando os dois booleanos das duas checkboxes distintas
    passo_base_ativo = params.get("aplicar_passo_base", False)
    passo_estilo_ativo = params.get("aplicar_passo_estilo", False)

    dano_base_form = params.get("dano_base", "0") or "0"
    dano_estilo_form = params.get("dano_estilo", "0") or "0"

    # 1ª Caixa: Avalia usando a respectiva flag da checkbox 1
    dano_base_val = avaliar_dado_str(
        formula_str=dano_base_form,
        contexto=ctx,
        aplicar_passo=passo_base_ativo,
        tipo_efeito=tipos_para_base, 
        params=params
    )
    
    # 2ª Caixa: Avalia usando a respectiva flag da checkbox 2
    dano_estilo_val = avaliar_dado_str(
        formula_str=dano_estilo_form,
        contexto=ctx,
        aplicar_passo=passo_estilo_ativo,
        tipo_efeito=["estilo_luta"],
        params=params
    )

    dano_total = dano_base_val + dano_estilo_val
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
    
    tipos_interface = hab.get("tipos_efeito", [])
    tipos_para_base = list(set(tipos_interface + ["estilo_luta"]))

    # REFORMULADO: Mesma lógica de duas flags para habilidades de área / TR
    passo_base_ativo = params.get("aplicar_passo_base", False)
    passo_estilo_ativo = params.get("aplicar_passo_estilo", False)

    dano_base_form = params.get("dano_base", "0") or "0"
    dano_estilo_form = params.get("dano_estilo", "0") or "0"

    dano_base_val = avaliar_dado_str(
        formula_str=dano_base_form,
        contexto=ctx,
        aplicar_passo=passo_base_ativo,
        tipo_efeito=tipos_para_base,
        params=params
    )
    
    dano_estilo_val = avaliar_dado_str(
        formula_str=dano_estilo_form,
        contexto=ctx,
        aplicar_passo=passo_estilo_ativo,
        tipo_efeito=["estilo_luta"],
        params=params
    )

    dano_total = dano_base_val + dano_estilo_val
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
    return {
        "sucesso": True,
        "detalhes": {}
    }