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

    aplicar_passo = ataque.get("aplicar_passo", False)
    tipos = ataque.get("tipos_efeito", [ataque.get("tipo_efeito", "corpo")])  # ← aqui
    dano_formula = ataque.get("dano", "1d6")

    # Cálculo do dano
    MAP_PASSO = {
    "tecnica": "PASSO_DANO_TECNICA",
    "corpo": "PASSO_DANO_CORPO",
    "desarmado": "PASSO_DANO_DESARMADO",
    "invocacao": "PASSO_DANO_INVOCACAO",
    "maldicao": "PASSO_MALDICAO",
    "shinobi": "PASSO_SHINOBI",
    "estilo_luta": "PASSO_ESTILO_LUTA",
    "energia_amaldicoada": "PASSO_ENERGIA_AMALDICOADA",
    }

    MAP_DADO = {
        "tecnica": "DADO_TECNICA",
        "corpo": "DADO_CORPO",
        "desarmado": "DADO_DESARMADO",
        "invocacao": "DADO_INVOCACAO",
        "maldicao": "DADO_MALDICAO",
        "shinobi": "DADO_SHINOBI",
        "estilo_luta": "DADO_ESTILO_LUTA",
        "energia_amaldicoada": "DADO_ENERGIA_AMALDICOADA",
    }

    bonus_passo_total = 0
    bonus_dados_total = 0

    for tipo in tipos:
        bonus_passo_total += int(ctx.get(MAP_PASSO.get(tipo, ""), 0))
        bonus_dados_total += int(ctx.get(MAP_DADO.get(tipo, ""), 0))

    # Bônus gerais (uma vez só)
    bonus_passo_total += int(ctx.get("PASSO_DANO_GERAL", 0))
    bonus_dados_total += int(ctx.get("DADO_GERAL", 0))

    # Verdadeiro Jujutsu (uma vez só)
    tipos_vj = {"tecnica", "maldicao", "invocacao"}
    if tipos_vj.intersection(set(tipos)):
        bonus_passo_total += int(ctx.get("VERDADEIRO_JUJUTSU", 0))

    # Contexto combinado sem duplicatas
    ctx_combinado = dict(ctx)
    ctx_combinado["PASSO_DANO_GERAL"] = bonus_passo_total
    ctx_combinado["DADO_GERAL"] = bonus_dados_total
    for chave in list(MAP_PASSO.values()) + list(MAP_DADO.values()):
        ctx_combinado[chave] = 0
    ctx_combinado["VERDADEIRO_JUJUTSU"] = 0

    dano_total = avaliar_dado_str(
        formula_str=dano_formula,
        contexto=ctx_combinado,
        aplicar_passo=aplicar_passo,
        tipo_efeito="geral",
        params={}
    )
    detalhes_tipos = [f"{t}" for t in tipos]

    dados_rolados = resultado_ataque["dados"]
    msg_ataque = f"Ataque com {pericia}: {d20_result} + {bonus_pericia} = {total_ataque}"
    if critico:
        msg_ataque += " (CRÍTICO!)"
    elif falha_critica:
        msg_ataque += " (FALHA CRÍTICA!)"

    mensagem = f"{msg_ataque}\nDados: {dados_rolados}\nDano total: {dano_total}"

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