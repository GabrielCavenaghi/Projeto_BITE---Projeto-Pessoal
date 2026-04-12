# utils/tecnicas.py
import random
import re
from ficha import avaliar_formula, construir_contexto_base, rolar_atributo
from utils.Efeitos_Scalling import string_para_tokens

# ══════════════════════════════════════════════════════════════════════════════
# Tabela de progressão de passos
# ══════════════════════════════════════════════════════════════════════════════
PASSO_MAP = {
    6:  (1, 8),      # d6 → d8 (quantidade mantida)
    8:  (1, 10),     # d8 → d10
    10: (1, 12),     # d10 → d12
    12: (2, 8),      # d12 → 2d8
    20: (4, 8),      # d20 → 4d8
    100:(15, 8),     # d100 → 15d8
}

def _aplicar_um_passo(count: int, faces: int) -> tuple[int, int]:
    """Aplica um único passo ao dado, retornando (novo_count, novas_faces)."""
    if faces in PASSO_MAP:
        mult, new_faces = PASSO_MAP[faces]
        return int(count * mult), new_faces
    return count, faces

def _aplicar_passo(count: int, faces: int, passos: int) -> tuple[int, int]:
    """Aplica uma quantidade de passos (positivos) ao dado."""
    for _ in range(passos):
        count, faces = _aplicar_um_passo(count, faces)
    return count, faces

# ══════════════════════════════════════════════════════════════════════════════
# Função auxiliar que avalia strings de dano com todos os bônus
# ══════════════════════════════════════════════════════════════════════════════
def _avaliar_dado_str(formula_str: str, contexto: dict, aplicar_passo: bool, params: dict) -> int:
    """
    Interpreta uma string com notação de dados (ex.: "50d12+AB*2", "(AB+LP)*(2*(EAd20))").
    Se aplicar_passo=True, aplica bônus de passos, dados extras e bônus por dado.
    """
    if not formula_str or formula_str.strip() == "0":
        return 0

    formula_str = formula_str.replace(' ', '')
    
    # Obtém bônus do contexto (apenas se aplicar_passo)
    bonus_passo = 0
    bonus_dados_extra = 0
    bonus_por_dado = 0
    if aplicar_passo:
        bonus_passo = int(contexto.get("PASSO_DANO_TECNICA", 0)) + int(contexto.get("PASSO_TECNICA", 0))
        bonus_dados_extra = int(contexto.get("DADO_TECNICA", 0))
        bonus_por_dado = int(contexto.get("DADO_POR_DADO_TECNICA", 0))

    def rolar_dado(quant_str: str, faces_str: str) -> int:
        """Avalia a quantidade, aplica bônus, rola os dados e retorna o valor total."""
        # Avalia a quantidade (pode ser expressão como "EA", "AB+2")
        if quant_str.isdigit():
            count = int(quant_str)
        else:
            try:
                tokens_quant = string_para_tokens(quant_str)
                count = int(avaliar_formula(tokens_quant, contexto))
            except Exception as e:
                print(f"Erro ao avaliar quantidade '{quant_str}': {e}")
                count = 1
        faces = int(faces_str)

        if aplicar_passo:
            count += bonus_dados_extra
            if bonus_passo > 0:
                count, faces = _aplicar_passo(count, faces, bonus_passo)

        # Compressão para evitar rolagens massivas (> 1000 dados)
        fator = 1
        while count > 1000:
            count //= 2
            fator *= 2

        resultados = [random.randint(1, faces) for _ in range(count)]
        soma_dados = sum(resultados)
        valor_dados = soma_dados * fator
        valor_total = valor_dados + (count * bonus_por_dado * fator)
        return valor_total

    # --- Reconstrução da string com substituição dos dados ---
    partes = []
    i = 0
    n = len(formula_str)
    while i < n:
        if formula_str[i] == 'd':
            # Encontra o início da quantidade (respeitando parênteses)
            j = i - 1
            paren_count = 0
            while j >= 0:
                if formula_str[j] == ')':
                    paren_count += 1
                elif formula_str[j] == '(':
                    paren_count -= 1
                if paren_count == 0 and formula_str[j] in '+-*/(':
                    break
                j -= 1
            quant_start = j + 1 if j >= 0 else 0
            quant_str = formula_str[quant_start:i]

            # Encontra o fim das faces (dígitos)
            k = i + 1
            while k < n and formula_str[k].isdigit():
                k += 1
            faces_str = formula_str[i+1:k]

            # Remove a quantidade que já foi adicionada às partes (está no final da lista)
            del partes[-(i - quant_start):]

            # Calcula o valor do dado e adiciona como string
            valor_dado = rolar_dado(quant_str, faces_str)
            partes.append(str(valor_dado))

            # Avança o índice para depois do dado
            i = k
        else:
            partes.append(formula_str[i])
            i += 1

    formula_sem_dados = ''.join(partes)

    # --- Avaliação da expressão matemática final ---
    try:
        tokens = string_para_tokens(formula_sem_dados)
        valor_final = avaliar_formula(tokens, contexto)
    except Exception as e:
        print(f"Erro ao avaliar expressão final '{formula_sem_dados}': {e}")
        valor_final = 0

    # --- Aplica multiplicador exclusivo da técnica (se houver) ---
    if aplicar_passo:
        mult_formula = params.get("multiplicador_dano", "1")
        if mult_formula and mult_formula != "1":
            try:
                tokens_mult = string_para_tokens(mult_formula)
                multiplicador = avaliar_formula(tokens_mult, contexto)
                valor_final = int(valor_final * multiplicador)
            except Exception as e:
                print(f"Erro ao avaliar multiplicador '{mult_formula}': {e}")

    # --- Aplica percentuais globais de dano ---
    if aplicar_passo:
        fator_percentual = 1.0 + contexto.get("DANO_PERCENTUAL_GERAL", 0) + contexto.get("DANO_PERCENTUAL_TECNICA", 0)
        valor_final = int(valor_final * fator_percentual)

    return int(valor_final)

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
    dano_total = _avaliar_dado_str(dano_formula_str, ctx, aplicar_passo, params)

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
    dano_total = _avaliar_dado_str(dano_formula_str, ctx, aplicar_passo, params)

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
    cura_total = _avaliar_dado_str(cura_formula_str, ctx, aplicar_passo, params)

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