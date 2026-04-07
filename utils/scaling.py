"""
Motor de cálculo de scaling do Projeto BITE.

Responsabilidades:
  - Extrair variáveis da ficha em tempo real
  - Avaliar fórmulas estruturadas (lista de tokens)
  - Determinar a versão ativa de um feitiço pelo grau
  - Calcular todos os efeitos ativos de uma habilidade
"""

# ══════════════════════════════════════════════════════════════════════════════
# Constantes do sistema
# ══════════════════════════════════════════════════════════════════════════════

# Ordem crescente de poder — usado para determinar versões desbloqueadas
ORDEM_GRAUS = [
    "Grau 4",
    "Grau 3",
    "Grau 2",
    "Grau 1",
    "Grau Semi Especial",
    "Grau Especial",
    "Grau Ultra Especial",
]

# Mapa de grau → valor numérico (1 = mais fraco, 7 = mais forte)
GRAU_PARA_NUMERO = {g: i + 1 for i, g in enumerate(ORDEM_GRAUS)}

# Chaves de versão nos JSONs de feitiços → índice numérico equivalente
VERSAO_PARA_NUMERO = {
    "GRAU 3":        2,
    "GRAU 2":        3,
    "GRAU 1":        4,
    "SEMI ESPECIAL": 5,
    "ESPECIAL":      6,
    "ULTRA ESPECIAL":7,
}

# Todas as variáveis reconhecidas pelo motor
VARIAVEIS_VALIDAS = {
    # Atributos base
    "FOR", "AGI", "INT", "VIG", "PRE",
    # Progressão
    "NEX", "LP", "LP_NATURAL", "AB", "GRAU",
    # Combate
    "DEF", "TR", "DT_HABILIDADES_TECNICA",
    "DADO_CORPO", "MULTIPLICADOR_CRITICO",
    # Passos de dano
    "PASSO_DANO_ARMADO_DESARMADO", "PASSO_DANO_CORPO",
    "PASSO_DANO_INVOCACAO", "PASSO_DANO_ESTILO_LUTA",
    "PASSO_TECNICA", "PASSO_ENERGIA_AMALDICOADA",
    "PASSO_SHINOBI",
    # Movimento e mobilidade
    "DESLOCAMENTO", "CURA_ACELERADA",
    # Resistências
    "RD_FISICO", "RD_PARANORMAL", "RD_MENTAL", "RD_GERAL",
    # Perícias
    "PERICIA_ATLETISMO", "PERICIA_INICIATIVA",
    "PERICIA_FURTIVIDADE", "PERICIA_INTIMIDACAO",
    # Invocação
    "CARACTERISTICA_INVOCACAO",
}

# Alvos que um efeito pode modificar — extensível
ALVOS_VALIDOS = [
    "DEF", "TR", "PV", "PE", "SAN",
    "DANO", "RD_FISICO", "RD_PARANORMAL", "RD_MENTAL", "RD_GERAL",
    "LP", "LP_NATURAL",
    "INICIATIVA", "ALCANCE", "DESLOCAMENTO",
    "MARGEM_AMEACA", "MULT_CRITICO",
    "PASSO_DANO_ARMADO_DESARMADO", "PASSO_DANO_CORPO",
    "PASSO_DANO_INVOCACAO", "PASSO_DANO_ESTILO_LUTA",
    "PASSO_TECNICA", "PASSO_ENERGIA_AMALDICOADA",
    "PASSO_SHINOBI", "CURA_ACELERADA",
    "PERICIA_ATLETISMO", "PERICIA_INICIATIVA",
    "PERICIA_FURTIVIDADE", "PERICIA_INTIMIDACAO",
    "CARACTERISTICA_INVOCACAO",
    "DT_HABILIDADES_TECNICA",
    "CUSTOM",   # alvo livre definido pelo usuário
]

# Operadores suportados
OPERADORES = ["+", "-", "*", "/", "^"]


# ══════════════════════════════════════════════════════════════════════════════
# Extração de variáveis da ficha
# ══════════════════════════════════════════════════════════════════════════════

def extrair_variaveis(ficha: dict) -> dict:
    """
    Lê uma ficha salva e retorna um dicionário com todas as variáveis
    disponíveis para cálculo de scaling.

    Todas as variáveis ausentes na ficha retornam 0 para não quebrar
    fórmulas que referenciam campos ainda não preenchidos.
    """
    variaveis = {v: 0 for v in VARIAVEIS_VALIDAS}

    # ── Atributos base ────────────────────────────────────────────────────────
    atributos = ficha.get("atributos", {})
    for sigla in ("FOR", "AGI", "INT", "VIG", "PRE"):
        variaveis[sigla] = int(atributos.get(sigla, 0))

    # AB = maior atributo base do personagem
    variaveis["AB"] = max(
        variaveis["FOR"], variaveis["AGI"], variaveis["INT"],
        variaveis["VIG"], variaveis["PRE"]
    )

    # ── Progressão ────────────────────────────────────────────────────────────
    # NEX como número puro (ex: "40%" → 40, "99.1%" → 99.1)
    nex_str = ficha.get("nex", "0%")
    try:
        variaveis["NEX"] = float(nex_str.replace("%", "").replace(",", "."))
    except ValueError:
        variaveis["NEX"] = 0

    variaveis["LP"]         = int(ficha.get("lp", 0))
    variaveis["LP_NATURAL"] = int(ficha.get("lp", 0))  # base sem modificadores
    variaveis["GRAU"]       = GRAU_PARA_NUMERO.get(ficha.get("grau", "Grau 4"), 1)

    # ── Valores derivados (preenchidos pelo gerenciador, 0 como fallback) ─────
    derivados = ficha.get("valores_derivados", {})
    campos_derivados = [
        "DEF", "TR", "DT_HABILIDADES_TECNICA", "DADO_CORPO",
        "MULTIPLICADOR_CRITICO", "DESLOCAMENTO", "CURA_ACELERADA",
        "PASSO_DANO_ARMADO_DESARMADO", "PASSO_DANO_CORPO",
        "PASSO_DANO_INVOCACAO", "PASSO_DANO_ESTILO_LUTA",
        "PASSO_TECNICA", "PASSO_ENERGIA_AMALDICOADA", "PASSO_SHINOBI",
        "RD_FISICO", "RD_PARANORMAL", "RD_MENTAL", "RD_GERAL",
        "PERICIA_ATLETISMO", "PERICIA_INICIATIVA",
        "PERICIA_FURTIVIDADE", "PERICIA_INTIMIDACAO",
        "CARACTERISTICA_INVOCACAO",
    ]
    for campo in campos_derivados:
        variaveis[campo] = float(derivados.get(campo, 0))

    return variaveis


# ══════════════════════════════════════════════════════════════════════════════
# Motor de avaliação de fórmulas
# ══════════════════════════════════════════════════════════════════════════════

def avaliar_formula(formula: list, variaveis: dict) -> float:
    """
    Avalia uma fórmula estruturada (lista de tokens) com as variáveis da ficha.

    Tokens possíveis:
      {"tipo": "constante",  "valor": 2}
      {"tipo": "variavel",   "valor": "LP"}
      {"tipo": "operador",   "valor": "*"}
      {"tipo": "expressao",  "valor": [...]}  ← sub-fórmula recursiva

    Retorna o valor numérico calculado.
    Levanta ScalingError em caso de token inválido ou divisão por zero.
    """
    if not formula:
        return 0.0

    # Resolve cada token para um valor ou operador
    tokens_resolvidos = []
    for token in formula:
        tipo  = token.get("tipo")
        valor = token.get("valor")

        if tipo == "constante":
            tokens_resolvidos.append(float(valor))

        elif tipo == "variavel":
            if valor not in variaveis:
                raise ScalingError(f"Variável desconhecida: '{valor}'")
            tokens_resolvidos.append(float(variaveis[valor]))

        elif tipo == "operador":
            if valor not in OPERADORES:
                raise ScalingError(f"Operador inválido: '{valor}'")
            tokens_resolvidos.append(valor)

        elif tipo == "expressao":
            # Sub-fórmula — avalia recursivamente
            tokens_resolvidos.append(avaliar_formula(valor, variaveis))

        else:
            raise ScalingError(f"Tipo de token desconhecido: '{tipo}'")

    return _calcular_tokens(tokens_resolvidos)


def _calcular_tokens(tokens: list) -> float:
    """
    Avalia uma lista de valores e operadores respeitando precedência:
      1ª passagem: ^ (potência)
      2ª passagem: * e /
      3ª passagem: + e -
    """
    # Copia para não modificar o original
    t = list(tokens)

    # Passagem 1 — potência
    t = _aplicar_operadores(t, {"^"})
    # Passagem 2 — multiplicação e divisão
    t = _aplicar_operadores(t, {"*", "/"})
    # Passagem 3 — adição e subtração
    t = _aplicar_operadores(t, {"+", "-"})

    if len(t) != 1:
        raise ScalingError(f"Fórmula malformada, tokens restantes: {t}")

    return float(t[0])


def _aplicar_operadores(tokens: list, operadores_alvo: set) -> list:
    """Aplica uma passagem de operadores sobre a lista de tokens."""
    resultado = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if isinstance(token, str) and token in operadores_alvo:
            esquerda  = resultado.pop()
            direita   = tokens[i + 1]
            resultado.append(_operar(esquerda, token, direita))
            i += 2
        else:
            resultado.append(token)
            i += 1
    return resultado


def _operar(a: float, op: str, b: float) -> float:
    """Aplica um operador entre dois valores."""
    a, b = float(a), float(b)
    if op == "+": return a + b
    if op == "-": return a - b
    if op == "*": return a * b
    if op == "/":
        if b == 0:
            raise ScalingError("Divisão por zero na fórmula.")
        return a / b
    if op == "^": return a ** b
    raise ScalingError(f"Operador não implementado: '{op}'")


# ══════════════════════════════════════════════════════════════════════════════
# Determinação de versão ativa
# ══════════════════════════════════════════════════════════════════════════════

def versao_ativa(feitico: dict, grau_personagem: str) -> str:
    """
    Retorna a chave da versão mais poderosa desbloqueada pelo grau do personagem.
    Se o personagem não desbloquear nenhuma versão além da base, retorna "BASE".

    Exemplo:
      feitiço tem versões GRAU 3, GRAU 2, GRAU 1
      personagem é Grau 2 → retorna "GRAU 2"
      personagem é Grau 4 → retorna "BASE"
    """
    grau_numero = GRAU_PARA_NUMERO.get(grau_personagem, 1)
    versoes     = feitico.get("efeitos_por_versao", {})

    melhor_chave  = "BASE"
    melhor_numero = 0  # BASE não tem número — é sempre o piso

    for chave, numero in VERSAO_PARA_NUMERO.items():
        if chave in versoes and numero <= grau_numero and numero > melhor_numero:
            melhor_chave  = chave
            melhor_numero = numero

    return melhor_chave


# ══════════════════════════════════════════════════════════════════════════════
# Cálculo de efeitos ativos
# ══════════════════════════════════════════════════════════════════════════════

def calcular_efeitos(feitico: dict, grau_personagem: str,
                     variaveis: dict) -> list:
    """
    Retorna a lista de efeitos calculados da versão ativa do feitiço.

    Cada item retornado é um dict:
      {
          "alvo":      "DEF",
          "operacao":  "+",
          "valor":     12.0,       ← já calculado
          "formula_str": "LP * 2"  ← representação legível para exibição
      }
    """
    chave_versao = versao_ativa(feitico, grau_personagem)
    versoes      = feitico.get("efeitos_por_versao", {})

    # BASE pode estar em "efeitos_por_versao" ou ser um campo separado
    if chave_versao == "BASE":
        efeitos_raw = versoes.get("BASE", feitico.get("efeitos_base", []))
    else:
        efeitos_raw = versoes.get(chave_versao, [])

    resultado = []
    for efeito in efeitos_raw:
        try:
            valor_calculado = avaliar_formula(efeito["formula"], variaveis)
        except ScalingError as e:
            valor_calculado = 0.0
            print(f"[Scaling] Erro ao calcular efeito de '{feitico.get('nome')}': {e}")

        resultado.append({
            "alvo":        efeito["alvo"],
            "operacao":    efeito.get("operacao", "+"),
            "valor":       round(valor_calculado, 2),
            "formula_str": formula_para_texto(efeito["formula"]),
        })

    return resultado


def formula_para_texto(formula: list) -> str:
    """
    Converte uma fórmula estruturada numa string legível.
    Ex: [LP, *, 2] → "LP * 2"
        [LP, *, (AB / 2)] → "LP * (AB / 2)"
    """
    partes = []
    for token in formula:
        tipo  = token.get("tipo")
        valor = token.get("valor")
        if tipo == "constante":
            partes.append(str(int(valor) if float(valor) == int(valor) else valor))
        elif tipo == "variavel":
            partes.append(str(valor))
        elif tipo == "operador":
            partes.append(str(valor))
        elif tipo == "expressao":
            partes.append(f"({formula_para_texto(valor)})")
    return " ".join(partes)


# ══════════════════════════════════════════════════════════════════════════════
# Aplicação de efeitos ao estado da ficha
# ══════════════════════════════════════════════════════════════════════════════

def aplicar_efeitos(efeitos: list, estado: dict) -> dict:
    """
    Aplica uma lista de efeitos calculados sobre um dicionário de estado.
    Usado pelo gerenciador para acumular bônus de múltiplas habilidades.

    Retorna um novo dicionário com os valores modificados.
    Não modifica o estado original.
    """
    resultado = dict(estado)
    for efeito in efeitos:
        alvo      = efeito["alvo"]
        op        = efeito["operacao"]
        valor     = efeito["valor"]

        if alvo not in resultado:
            resultado[alvo] = 0.0

        base = float(resultado[alvo])
        if op == "+": resultado[alvo] = base + valor
        elif op == "-": resultado[alvo] = base - valor
        elif op == "*": resultado[alvo] = base * valor
        elif op == "/":
            resultado[alvo] = base / valor if valor != 0 else base
        elif op == "^":
            resultado[alvo] = base ** valor

    return resultado


# ══════════════════════════════════════════════════════════════════════════════
# Utilitários públicos
# ══════════════════════════════════════════════════════════════════════════════

def resumo_efeitos(efeitos: list) -> str:
    """
    Gera uma string resumida de todos os efeitos para exibição na UI.
    Ex: "+12 em DEF  •  +6 em TR"
    """
    partes = []
    for e in efeitos:
        op    = e["operacao"] if e["operacao"] != "+" else "+"
        valor = int(e["valor"]) if e["valor"] == int(e["valor"]) else e["valor"]
        partes.append(f"{op}{valor} em {e['alvo']}")
    return "  •  ".join(partes) if partes else "Sem efeitos"


def listar_variaveis() -> list:
    """Retorna a lista ordenada de variáveis disponíveis para a UI."""
    return sorted(VARIAVEIS_VALIDAS)


def listar_alvos() -> list:
    """Retorna a lista de alvos disponíveis para a UI."""
    return list(ALVOS_VALIDOS)


def listar_operadores() -> list:
    return list(OPERADORES)


# ══════════════════════════════════════════════════════════════════════════════
# Exceção customizada
# ══════════════════════════════════════════════════════════════════════════════

class ScalingError(Exception):
    """Erro de avaliação de fórmula de scaling."""
    pass