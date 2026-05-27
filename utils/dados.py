# utils/dados.py
import random
import re
from ficha import avaliar_formula, construir_contexto_base
from utils.Efeitos_Scalling import string_para_tokens

PASSO_MAP = {
    2:  (1, 3),      # d2 → d3
    3:  (1, 4),      # d3 → d4
    4:  (1, 6),      # d4 → d6
    6:  (1, 8),      # d6 → d8
    8:  (1, 10),     # d8 → d10
    10: (1, 12),     # d10 → d12
    12: (2, 8),      # d12 → 2d8
    20: (4, 12),     # d20 → 4d8
    100:(15, 12),    # d100 → 15d8
}

def _aplicar_um_passo(count: int, faces: int) -> tuple[int, int]:
    if faces in PASSO_MAP:
        mult, new_faces = PASSO_MAP[faces]
        return int(count * mult), new_faces
    return count, faces

def _aplicar_passo(count: int, faces: int, passos: int) -> tuple[int, int]:
    for _ in range(passos):
        count, faces = _aplicar_um_passo(count, faces)
    return count, faces


def avaliar_dado_str(
    formula_str: str,
    ficha: dict = None,
    contexto: dict = None,
    aplicar_passo: bool = False,
    tipo_efeito: str | list = "tecnica", # <-- Agora suporta Listas de Efeitos
    params: dict = None
) -> int:
    """
    Avalia uma string contendo notação de dados (ex.: "50d12+AB*2", "(AB+LP)*(2*(EAd20))").
    """
    if params is None:
        params = {}

    if not formula_str or formula_str.strip() == "0":
        return 0

    formula_str = formula_str.replace(' ', '')

    if contexto is None and ficha is not None:
        contexto = construir_contexto_base(ficha)
    elif contexto is None:
        contexto = {}

    MAP_BONUS = {
        "tecnica": {
            "passo_dano": "PASSO_DANO_TECNICA",
            "passo_extra": "PASSO_TECNICA",
            "dado_extra": "DADO_TECNICA",
            "por_dado": "DADO_POR_DADO_TECNICA",
            "percentual": "DANO_PERCENTUAL_TECNICA",
        },
        "corpo": {
            "passo_dano": "PASSO_DANO_CORPO",
            "passo_extra": None,
            "dado_extra": "DADO_CORPO",
            "por_dado": "DADO_POR_DADO_CORPO",
            "percentual": "DANO_PERCENTUAL_CORPO",
        },
        "desarmado": {
            "passo_dano": "PASSO_DANO_DESARMADO",
            "passo_extra": None,
            "dado_extra": "DADO_DESARMADO",
            "por_dado": "DADO_POR_DADO_DESARMADO",
            "percentual": "DANO_PERCENTUAL_DESARMADO",
        },
        "invocacao": {
            "passo_dano": "PASSO_DANO_INVOCACAO",
            "passo_extra": None,
            "dado_extra": "DADO_INVOCACAO",
            "por_dado": "DADO_POR_DADO_INVOCACAO",
            "percentual": "PERCENTUAL_INVOCACAO",
        },
        "maldicao": {
            "passo_dano": "PASSO_MALDICAO",
            "passo_extra": None,
            "dado_extra": "DADO_MALDICAO",
            "por_dado": "DADO_POR_DADO_MALDICAO",
            "percentual": "PERCENTUAL_MALDICAO",
        },
        "shinobi": {
            "passo_dano": "PASSO_SHINOBI",
            "passo_extra": None,
            "dado_extra": "DADO_SHINOBI",
            "por_dado": "DADO_POR_DADO_SHINOBI",
            "percentual": "PERCENTUAL_SHINOBI",
        },
        "estilo_luta": {
            "passo_dano": "PASSO_ESTILO_LUTA",
            "passo_extra": None,
            "dado_extra": "DADO_ESTILO_LUTA",
            "por_dado": "DADO_POR_DADO_ESTILO_LUTA",
            "percentual": "DANO_PERCENTUAL_ESTILO_LUTA",
        },
        "energia_amaldicoada": {
            "passo_dano": "PASSO_ENERGIA_AMALDICOADA",
            "passo_extra": None,
            "dado_extra": "DADO_ENERGIA_AMALDICOADA",
            "por_dado": "DADO_POR_DADO_ENERGIA_AMALDICOADA",
            "percentual": "PERCENTUAL_ENERGIA_AMALDICOADA",
        },
        "geral": {
            "passo_dano": "PASSO_DANO_GERAL",
            "passo_extra": None,
            "dado_extra": "DADO_GERAL",
            "por_dado": "DADO_POR_DADO_GERAL",
            "percentual": "DANO_PERCENTUAL_GERAL",
        },
    }

    # Transforma em lista caso alguém chame mandando só uma string antiga
    lista_tipos = [tipo_efeito] if isinstance(tipo_efeito, str) else tipo_efeito

    bonus_passo = 0
    bonus_dados_extra = 0
    bonus_por_dado = 0
    fator_percentual_especifico = 0.0

    if aplicar_passo:
        def _get(key, default=0):
            return contexto.get(key, default)

        # Usamos sets para garantir que chaves repetidas não sejam somadas múltiplas vezes
        chaves_soma = {
            "passo_dano": set(),
            "passo_extra": set(),
            "dado_extra": set(),
            "por_dado": set(),
            "percentual": set()
        }

        for t in lista_tipos:
            chaves = MAP_BONUS.get(t, MAP_BONUS["tecnica"])
            if chaves["passo_dano"]: chaves_soma["passo_dano"].add(chaves["passo_dano"])
            if chaves["passo_extra"]: chaves_soma["passo_extra"].add(chaves["passo_extra"])
            if chaves["dado_extra"]: chaves_soma["dado_extra"].add(chaves["dado_extra"])
            if chaves["por_dado"]: chaves_soma["por_dado"].add(chaves["por_dado"])
            if chaves["percentual"]: chaves_soma["percentual"].add(chaves["percentual"])

        # Tratamento especial: desarmado também herda bônus de corpo a corpo
        if "desarmado" in lista_tipos:
            chaves_corpo = MAP_BONUS["corpo"]
            if chaves_corpo["passo_dano"]: chaves_soma["passo_dano"].add(chaves_corpo["passo_dano"])
            if chaves_corpo["dado_extra"]: chaves_soma["dado_extra"].add(chaves_corpo["dado_extra"])
            if chaves_corpo["por_dado"]: chaves_soma["por_dado"].add(chaves_corpo["por_dado"])
            if chaves_corpo["percentual"]: chaves_soma["percentual"].add(chaves_corpo["percentual"])

        # Verdadeiro Jujutsu
        if any(t in ["tecnica", "maldicao", "invocacao"] for t in lista_tipos):
            chaves_soma["passo_extra"].add("VERDADEIRO_JUJUTSU")

        # Bônus Gerais
        chaves_geral = MAP_BONUS["geral"]
        if chaves_geral["passo_dano"]: chaves_soma["passo_dano"].add(chaves_geral["passo_dano"])
        if chaves_geral["dado_extra"]: chaves_soma["dado_extra"].add(chaves_geral["dado_extra"])
        if chaves_geral["por_dado"]: chaves_soma["por_dado"].add(chaves_geral["por_dado"])


        # Aplica a soma real extraindo as chaves únicas
        for k in chaves_soma["passo_dano"]: bonus_passo += int(_get(k))
        for k in chaves_soma["passo_extra"]: bonus_passo += int(_get(k))
        for k in chaves_soma["dado_extra"]: bonus_dados_extra += int(_get(k))
        for k in chaves_soma["por_dado"]: bonus_por_dado += int(_get(k))
        for k in chaves_soma["percentual"]: fator_percentual_especifico += float(_get(k))


    def rolar_dado(quant_str: str, faces_str: str) -> int:
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

        fator = 1
        while count > 1000:
            count //= 2
            fator *= 2

        resultados = [random.randint(1, faces) for _ in range(count)]
        soma_dados = sum(resultados)
        valor_dados = soma_dados * fator
        valor_total = valor_dados + (count * bonus_por_dado * fator)
        return valor_total

    partes = []
    i = 0
    n = len(formula_str)
    while i < n:
        if formula_str[i] == 'd':
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

            k = i + 1
            while k < n and formula_str[k].isdigit():
                k += 1
            faces_str = formula_str[i+1:k]

            del partes[-(i - quant_start):]
            valor_dado = rolar_dado(quant_str, faces_str)
            partes.append(str(valor_dado))
            i = k
        else:
            partes.append(formula_str[i])
            i += 1

    formula_sem_dados = ''.join(partes)

    try:
        tokens = string_para_tokens(formula_sem_dados)
        valor_final = avaliar_formula(tokens, contexto)
    except Exception as e:
        print(f"Erro ao avaliar expressão final '{formula_sem_dados}': {e}")
        valor_final = 0

    if aplicar_passo:
        mult_formula = params.get("multiplicador_dano", "1")
        if mult_formula and mult_formula != "1":
            multiplicador = avaliar_dado_str(
                mult_formula,
                contexto=contexto,
                aplicar_passo=False,
                tipo_efeito=tipo_efeito,
                params={}
            )
            valor_final = int(valor_final * multiplicador)

    if aplicar_passo:
        percentual_geral = float(contexto.get("DANO_PERCENTUAL_GERAL", 0))
        fator_total = 1.0 + percentual_geral + fator_percentual_especifico
        valor_final = int(valor_final * fator_total)

    return int(valor_final)