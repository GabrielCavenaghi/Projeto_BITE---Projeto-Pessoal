# utils/combate.py
from ficha import construir_contexto_base, rolar_atributo
from utils.dados import avaliar_dado_str

def executar_ataque_personalizado(ficha: dict, ataque: dict) -> dict:
    """
    Executa um ataque personalizado definido pelo usuário.
    Retorna um dicionário com o resultado formatado para exibição.
    """
    ctx = construir_contexto_base(ficha)
    pericia = ataque.get("pericia", "Luta")
    bonus_pericia = ctx.get(pericia, 0)

    # Obtém o atributo associado à perícia (respeitando override)
    pericias_info = ficha.get("pericias", {})
    info_pericia = pericias_info.get(pericia, {})
    atributo = info_pericia.get("atributo_override") or info_pericia.get("atributo_base", "FOR")
    valor_atributo = ctx.get(atributo, 1)

    # Rolagem do d20
    resultado_ataque = rolar_atributo(valor_atributo, treinamento=bonus_pericia, bonus=0)
    d20_result = resultado_ataque["escolhido"]
    total_ataque = resultado_ataque["total"]

    margem = ataque.get("margem_ameaca", 20)
    multiplicador = ataque.get("multiplicador_critico", 2)

    critico = (d20_result >= margem)
    falha_critica = (d20_result == 1)

    # Cálculo do dano
    aplicar_passo = ataque.get("aplicar_passo", False)
    tipo_efeito = ataque.get("tipo_efeito", "corpo")
    dano_formula = ataque.get("dano", "1d6")
    dano_total = avaliar_dado_str(
        formula_str=dano_formula,
        contexto=ctx,
        aplicar_passo=aplicar_passo,
        tipo_efeito=tipo_efeito,
        params={}
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