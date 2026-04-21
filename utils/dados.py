# utils/dados.py
import random
import re
from ficha import avaliar_formula, construir_contexto_base
from utils.Efeitos_Scalling import string_para_tokens

# Tabela de progressão de passos (pode ser importada se já definida em outro lugar)
PASSO_MAP = {
    6:  (1, 8),      # d6 → d8
    8:  (1, 10),     # d8 → d10
    10: (1, 12),     # d10 → d12
    12: (2, 8),      # d12 → 2d8
    20: (4, 8),      # d20 → 4d8
    100:(15, 8),     # d100 → 15d8
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
    tipo_efeito: str = "tecnica",
    params: dict = None
) -> int:
    """
    Avalia uma string contendo notação de dados (ex.: "50d12+AB*2", "(AB+LP)*(2*(EAd20))").

    Parâmetros:
        formula_str   : string com a fórmula (dados, operadores, variáveis)
        ficha         : dicionário completo da ficha (usado se contexto for None)
        contexto      : dicionário de contexto pré-construído (opcional, evita reconstruir)
        aplicar_passo : se True, aplica bônus de passos, dados extras, bônus por dado e percentuais
        tipo_efeito   : categoria do efeito para selecionar os bônus corretos:
                        "tecnica", "corpo", "desarmado", "invocacao", "maldicao", "shinobi", "estilo_luta"
        params        : dicionário de parâmetros adicionais (ex.: multiplicador_dano)
    """
    if params is None:
        params = {}

    if not formula_str or formula_str.strip() == "0":
        return 0

    formula_str = formula_str.replace(' ', '')

    # Constrói contexto se não fornecido
    if contexto is None and ficha is not None:
        contexto = construir_contexto_base(ficha)
    elif contexto is None:
        contexto = {}

    # Mapeamento de tipo_efeito para as chaves de bônus no contexto
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

    # Obtém as chaves para o tipo de efeito (fallback para tecnica)
    chaves = MAP_BONUS.get(tipo_efeito, MAP_BONUS["tecnica"])

    bonus_passo = 0
    bonus_dados_extra = 0
    bonus_por_dado = 0
    fator_percentual_especifico = 0.0

    if aplicar_passo:
        # Função auxiliar para obter valor do contexto (inteiro ou float)
        def _get(key, default=0):
            return contexto.get(key, default)

        # Passo de dano principal
        if chaves["passo_dano"]:
            bonus_passo += int(_get(chaves["passo_dano"]))
        # Passo extra (apenas para técnica)
        if chaves["passo_extra"]:
            bonus_passo += int(_get(chaves["passo_extra"]))
        # Verdadeiro Jujutsu (apenas para técnica)
        if tipo_efeito == "tecnica":
            bonus_passo += int(_get("VERDADEIRO_JUJUTSU"))

        # Dados extras
        if chaves["dado_extra"]:
            bonus_dados_extra = int(_get(chaves["dado_extra"]))

        # Bônus por dado
        if chaves["por_dado"]:
            bonus_por_dado = int(_get(chaves["por_dado"]))

        # Percentual específico
        if chaves["percentual"]:
            fator_percentual_especifico = float(_get(chaves["percentual"]))

        # ══════════════════════════════════════════════════════════════════════
        # Tratamento especial: desarmado também herda bônus de corpo a corpo
        # ══════════════════════════════════════════════════════════════════════
        if tipo_efeito == "desarmado":
            chaves_corpo = MAP_BONUS["corpo"]
            if chaves_corpo["passo_dano"]:
                bonus_passo += int(_get(chaves_corpo["passo_dano"]))
            if chaves_corpo["dado_extra"]:
                bonus_dados_extra += int(_get(chaves_corpo["dado_extra"]))
            if chaves_corpo["por_dado"]:
                bonus_por_dado += int(_get(chaves_corpo["por_dado"]))
            if chaves_corpo["percentual"]:
                fator_percentual_especifico += float(_get(chaves_corpo["percentual"]))

        # ══════════════════════════════════════════════════════════════════════
        # ADIÇÃO DOS BÔNUS GERAIS (aplicam-se a todos os tipos)
        # ══════════════════════════════════════════════════════════════════════
        chaves_geral = MAP_BONUS["geral"]
        if chaves_geral["passo_dano"]:
            bonus_passo += int(_get(chaves_geral["passo_dano"]))
        if chaves_geral["dado_extra"]:
            bonus_dados_extra += int(_get(chaves_geral["dado_extra"]))
        if chaves_geral["por_dado"]:
            bonus_por_dado += int(_get(chaves_geral["por_dado"]))

    def rolar_dado(quant_str: str, faces_str: str) -> int:
        # Avalia a quantidade
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

        # Compressão para evitar rolagens massivas
        fator = 1
        while count > 1000:
            count //= 2
            fator *= 2

        resultados = [random.randint(1, faces) for _ in range(count)]
        soma_dados = sum(resultados)
        valor_dados = soma_dados * fator
        valor_total = valor_dados + (count * bonus_por_dado * fator)
        return valor_total

    # Reconstrução da string com substituição dos dados
    partes = []
    i = 0
    n = len(formula_str)
    while i < n:
        if formula_str[i] == 'd':
            # Encontra o início da quantidade
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

            # Encontra o fim das faces
            k = i + 1
            while k < n and formula_str[k].isdigit():
                k += 1
            faces_str = formula_str[i+1:k]

            # Remove a quantidade já adicionada
            del partes[-(i - quant_start):]

            valor_dado = rolar_dado(quant_str, faces_str)
            partes.append(str(valor_dado))
            i = k
        else:
            partes.append(formula_str[i])
            i += 1

    formula_sem_dados = ''.join(partes)

    # Avaliação da expressão matemática final
    try:
        tokens = string_para_tokens(formula_sem_dados)
        valor_final = avaliar_formula(tokens, contexto)
    except Exception as e:
        print(f"Erro ao avaliar expressão final '{formula_sem_dados}': {e}")
        valor_final = 0

    # Multiplicador exclusivo (dos params)
    if aplicar_passo:
        mult_formula = params.get("multiplicador_dano", "1")
        if mult_formula and mult_formula != "1":
            # Chama recursivamente sem aplicar bônus de novo
            multiplicador = avaliar_dado_str(
                mult_formula,
                contexto=contexto,
                aplicar_passo=False,
                tipo_efeito=tipo_efeito,
                params={}
            )
            valor_final = int(valor_final * multiplicador)

    # Percentuais globais + específico
    if aplicar_passo:
        percentual_geral = float(contexto.get("DANO_PERCENTUAL_GERAL", 0))
        fator_total = 1.0 + percentual_geral + fator_percentual_especifico
        valor_final = int(valor_final * fator_total)

    return int(valor_final)