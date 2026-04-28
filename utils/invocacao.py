# utils/invocacao.py
from ficha import construir_contexto_base, rolar_atributo
from utils.dados import avaliar_dado_str

def executar_ataque_invocacao(inv: dict, ataque: dict, ficha: dict) -> dict:
    """
    Executa um ataque de invocação (principal ou secundário).
    
    Parâmetros:
        inv     : dicionário completo da invocação (contém 'pericia_base', 'nome', etc.)
        ataque  : dicionário do ataque específico com:
                    - dano: fórmula de dano
                    - aplicar_passo: bool
                    - tipo_mecanica: "Ataque" (padrão), "Teste de Resistência"
                    - margem_ameaca: int (padrão 20)
                    - multiplicador_critico: int (padrão 2)
        ficha   : dicionário da ficha do personagem invocador
    
    Retorna:
        dict com "sucesso", "mensagem" e "detalhes" (incluindo dano calculado).
    """
    tipo_mec = ataque.get("tipo_mecanica", "Ataque")
    pericia_base = inv.get("pericia_base", "Luta")
    dano_formula = ataque.get("dano", "1d6")
    aplicar_passo = ataque.get("aplicar_passo", False)

    # Constrói o contexto (com PB = perícia base do invocador)
    contexto = construir_contexto_base(ficha)
    contexto["PB"] = contexto.get(pericia_base, 0)  # valor da perícia escolhida

    # Avalia o dano base (já com passos, dados extras, percentuais de invocação)
    dano_total = avaliar_dado_str(
        formula_str=dano_formula,
        contexto=contexto,
        aplicar_passo=aplicar_passo,
        tipo_efeito="invocacao",
        params={}
    )

    if tipo_mec == "Teste de Resistência":
        dt = int(contexto.get("DT_TECNICA", 10))
        mensagem = f"{inv.get('nome', 'Invocação')} causa {dano_total} de dano.\nTeste de Resistência (DT {dt}) para reduzir à metade."
        return {
            "sucesso": True,
            "mensagem": mensagem,
            "detalhes": {"dano": dano_total, "dt": dt}
        }

    elif tipo_mec == "Ataque":
        margem = ataque.get("margem_ameaca", 20)
        multiplicador = ataque.get("multiplicador_critico", 2)
        if margem < 1:
            margem = 1
        valor_critico_min = 21 - margem

        # Bônus da perícia (já deve estar no contexto, por exemplo "Luta")
        bonus_pericia = contexto.get(pericia_base, 0)

        # Determina atributo para vantagem baseado na perícia (simplificado como em combate)
        atributo_map = {"Luta": "FOR", "Pontaria": "AGI"}
        atributo = atributo_map.get(pericia_base, "FOR")
        valor_atributo = contexto.get(atributo, 1)

        resultado_ataque = rolar_atributo(valor_atributo, treinamento=bonus_pericia, bonus=0)
        d20_result = resultado_ataque["escolhido"]
        total_ataque = resultado_ataque["total"]

        critico = (d20_result >= valor_critico_min)
        falha_critica = (d20_result == 1)

        dano_final = dano_total
        if critico:
            dano_final = int(dano_final * multiplicador)

        msg = f"Ataque com {pericia_base}: {d20_result} + {bonus_pericia} = {total_ataque}"
        if critico:
            msg += " (CRÍTICO!)"
        elif falha_critica:
            msg += " (FALHA CRÍTICA!)"

        mensagem = f"{msg}\nDados: {resultado_ataque['dados']}\nDano: {dano_final}"

        return {
            "sucesso": True,
            "mensagem": mensagem,
            "detalhes": {
                "d20": d20_result,
                "bonus": bonus_pericia,
                "total": total_ataque,
                "critico": critico,
                "falha_critica": falha_critica,
                "dano": dano_final
            }
        }

    else:
        # Fallback para tipos não implementados
        return {
            "sucesso": False,
            "mensagem": f"Tipo de mecânica '{tipo_mec}' não suportado para invocações.",
            "detalhes": {}
        }