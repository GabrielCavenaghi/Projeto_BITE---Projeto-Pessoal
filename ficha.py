import customtkinter as ctk
import json
import os
import datetime
import random

# ══════════════════════════════════════════════════════════════════════════════
# Funções auxiliares para manipulação de atributos (edição na ficha)
# ══════════════════════════════════════════════════════════════════════════════

LIMITE_NORMAL = 13
LIMITE_ABSOLUTO = 14

def rolar_atributo(valor_atributo: int, treinamento: int = 0, bonus: int = 0) -> dict:
    """
    Rola dados conforme o valor do atributo:
    - Se atributo == 0: rola 2d20 e pega o menor (desvantagem).
    - Se atributo > 0: rola (valor) d20 e pega o maior (vantagem).
    Retorna um dicionário com:
        'dados': lista dos valores rolados,
        'escolhido': valor selecionado (maior/menor),
        'total': valor escolhido + treinamento + bonus
    """
    if valor_atributo == 0:
        dados = [random.randint(1, 20) for _ in range(2)]
        escolhido = min(dados)
    else:
        dados = [random.randint(1, 20) for _ in range(valor_atributo)]
        escolhido = max(dados)

    total = escolhido + treinamento + bonus
    return {
        "dados": dados,
        "escolhido": escolhido,
        "treinamento": treinamento,
        "bonus": bonus,
        "total": total
    }

def calcular_pontos_disponiveis_ficha(ficha: dict) -> int:
    # Total de pontos que o personagem tem direito
    totais = ficha.get("totais_nex", {})
    total_disponivel = 4 + totais.get("pontos_atributo", 0) + ficha.get("pontos_extras_temp", 0)

    # Calcula quantos pontos já foram efetivamente gastos (baseado nos valores atuais)
    atributos = ficha.get("atributos", {})
    soma_atributos = sum(atributos.values())
    gastos_reais = max(0, soma_atributos - 5)   # cada atributo começa com 1

    pontos_restantes = total_disponivel - gastos_reais
    return max(0, pontos_restantes)

# ══════════════════════════════════════════════════════════════════════════════
# Definição padrão das perícias
# ══════════════════════════════════════════════════════════════════════════════
PERICIAS_PADRAO = {
    "Acrobacia": {"atributo_base": "AGI"},
    "Adestramento": {"atributo_base": "PRE"},
    "Artes": {"atributo_base": "PRE"},
    "Atletismo": {"atributo_base": "FOR"},
    "Atualidades": {"atributo_base": "INT"},
    "Ciencias": {"atributo_base": "INT"},
    "Crime": {"atributo_base": "AGI"},
    "Diplomacia": {"atributo_base": "PRE"},
    "Enganação": {"atributo_base": "PRE"},
    "Fortitude": {"atributo_base": "VIG"},
    "Furtividade": {"atributo_base": "AGI"},
    "Iniciativa": {"atributo_base": "AGI"},
    "Intimidação": {"atributo_base": "PRE"},
    "Intuição": {"atributo_base": "PRE"},
    "Investigação": {"atributo_base": "INT"},
    "Luta": {"atributo_base": "FOR"},
    "Medicina": {"atributo_base": "INT"},
    "Ocultismo": {"atributo_base": "INT"},
    "Percepção": {"atributo_base": "PRE"},
    "Pilotagem": {"atributo_base": "AGI"},
    "Pontaria": {"atributo_base": "AGI"},
    "Profissão": {"atributo_base": "INT"},
    "Energia Amaldiçoada": {"atributo_base": "PRE"},
    "Reflexos": {"atributo_base": "AGI"},
    "Religião": {"atributo_base": "PRE"},
    "Sobrevivência": {"atributo_base": "INT"},
    "Tática": {"atributo_base": "INT"},
    "Tecnologia": {"atributo_base": "INT"},
    "Vontade": {"atributo_base": "PRE"}
}

# ══════════════════════════════════════════════════════════════════════════════
# Normalização — garante retrocompatibilidade com fichas antigas
# ══════════════════════════════════════════════════════════════════════════════

def normalizar_ficha(ficha: dict) -> dict:
    """
    Preenche campos ausentes com defaults seguros.
    Fichas criadas antes da v2 continuam funcionando normalmente.
    """
    lp = ficha.get("lp", 0) or 0

    ficha.setdefault("atualizado_em", ficha.get("criado_em", ""))
    ficha.setdefault("pontos_atributo_gastos", 0)
    ficha.setdefault("pontos_extras_temp", 0)
    ficha.setdefault("habilidades_gerais", [])
    ficha.setdefault("tecnicas_ativas", [])

    # Garante que 'atributos' exista com os valores base
    if "atributos" not in ficha:
        ficha["atributos"] = {
            "AGI": 1, "FOR": 1, "INT": 1, "VIG": 1, "PRE": 1
        }

    # Estado de sessão (PV, Sanidade, PE)
    if "estado" not in ficha:
        ficha["estado"] = {
            "pv_atual":   lp,
            "pv_maximo":  lp,
            "san_atual":  lp,
            "san_maximo": lp,
            "pe_atual":   ficha.get("totais_nex", {}).get("feiticos", 0),
            "pe_maximo":  ficha.get("totais_nex", {}).get("feiticos", 0),
        }
    else:
        ficha["estado"].setdefault("pv_atual",   lp)
        ficha["estado"].setdefault("pv_maximo",  lp)
        ficha["estado"].setdefault("san_atual",  lp)
        ficha["estado"].setdefault("san_maximo", lp)
        ficha["estado"].setdefault("pe_atual",   0)
        ficha["estado"].setdefault("pe_maximo",  0)

    # Combate
    ficha.setdefault("estilo_luta", {
        "id": None, "nome": None, "descricao": None,
        "origem": "padrao", "efeito": None,
    })
    ficha.setdefault("tecnica", {
        "id": None, "nome": None, "descricao": None,
        "origem": "padrao", "efeito": None,
    })
    ficha.setdefault("feiticos_custom", [])

    # Inventário
    ficha.setdefault("inventario", {"dinheiro": 0, "itens": []})

    # Anotações
    ficha.setdefault("anotacoes", "")
    ficha.setdefault("historico_sessoes", [])

    ficha.setdefault("passivas_ativas", {})   # ex: {"fei_004": "ESPECIAL", "fei_016": "GRAU 1"}
    ficha.setdefault("bonus_passivos", {})    # será preenchido dinamicamente

    # Perícias
    if "pericias" not in ficha:
        ficha["pericias"] = {}
        for nome, info in PERICIAS_PADRAO.items():
            ficha["pericias"][nome] = {
                "atributo_base": info["atributo_base"],
                "atributo_override": None,
                "treinamento": 0,
                "bonus": 0
            }
    else:
        for nome, info in PERICIAS_PADRAO.items():
            if nome not in ficha["pericias"]:
                ficha["pericias"][nome] = {
                    "atributo_base": info["atributo_base"],
                    "atributo_override": None,
                    "treinamento": 0,
                    "bonus": 0
                }
            else:
                ficha["pericias"][nome].setdefault("atributo_base", info["atributo_base"])
                ficha["pericias"][nome].setdefault("atributo_override", None)
                ficha["pericias"][nome].setdefault("treinamento", 0)
                ficha["pericias"][nome].setdefault("bonus", 0)

    return ficha

def salvar_ficha(ficha: dict):
    """Sobrescreve o .json da ficha no disco e atualiza atualizado_em."""
    caminho = ficha.get("_arquivo")
    if not caminho:
        return
    ficha["atualizado_em"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    dados = {k: v for k, v in ficha.items() if k != "_arquivo"}
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def avaliar_formula(formula: list, contexto: dict) -> float:
    """
    Avalia uma fórmula em notação infixa (lista de tokens).
    Suporta operadores +, -, *, /, // e parênteses via token "expressao".
    """
    precedencia = {'+': 1, '-': 1, '*': 2, '/': 2, '//': 2}
    saida = []
    operadores = []

    def aplicar_operador(op, a, b):
        if op == '+': return a + b
        if op == '-': return a - b
        if op == '*': return a * b
        if op == '/': return a / b if b != 0 else 0
        if op == '//': return a // b if b != 0 else 0
        raise ValueError(f"Operador desconhecido: {op}")

    i = 0
    while i < len(formula):
        token = formula[i]
        tipo = token["tipo"]

        if tipo == "constante":
            saida.append(token["valor"])
        elif tipo == "variavel":
            nome = token["valor"]
            if nome not in contexto:
                raise KeyError(f"Variável '{nome}' não encontrada.")
            saida.append(contexto[nome])
        elif tipo == "operador":
            op = token["valor"]
            while (operadores and operadores[-1] != '(' and
                   precedencia.get(operadores[-1], 0) >= precedencia.get(op, 0)):
                saida.append(operadores.pop())
            operadores.append(op)
        elif tipo == "expressao":
            sub_valor = avaliar_formula(token["valor"], contexto)
            saida.append(sub_valor)
        else:
            raise ValueError(f"Tipo de token desconhecido: {tipo}")
        i += 1

    while operadores:
        saida.append(operadores.pop())

    pilha = []
    for item in saida:
        if isinstance(item, (int, float)):
            pilha.append(item)
        elif item in precedencia:
            if len(pilha) < 2:
                raise ValueError("Operador sem operandos suficientes.")
            b = pilha.pop()
            a = pilha.pop()
            pilha.append(aplicar_operador(item, a, b))
        else:
            raise ValueError(f"Elemento inesperado na saída RPN: {item}")

    return pilha[0] if pilha else 0

def construir_contexto_base(ficha: dict) -> dict:
    atributos = ficha.get("atributos", {})
    pericias = ficha.get("pericias", {})
    estado = ficha.get("estado", {})
    totais_nex = ficha.get("totais_nex", {})
    grau_str = ficha.get("grau", "Grau 4")
    grau_num = 0
    if "Grau" in grau_str and "Semi" not in grau_str and "Especial" not in grau_str:
        try:
            grau_num = int(grau_str.split()[1])
        except:
            pass
    elif "Semi" in grau_str:
        grau_num = 5
    elif "Ultra" in grau_str:
        grau_num = 7
    elif "Especial" in grau_str:
        grau_num = 6

    nex_str = ficha.get("nex", "5%").replace("%", "")
    try:
        nex_valor = float(nex_str)
    except:
        nex_valor = 5.0

    ea_pericia = pericias.get("Energia Amaldiçoada", {})
    ea_valor = ea_pericia.get("treinamento", 0) + ea_pericia.get("bonus", 0)

    # Calcula LP_NATURAL (sem bônus)
    lp_natural = ficha.get("lp", 1)  # lp já é o base

    # LP total (base + bônus passivos)
    bonus_lp = ficha.get("bonus_passivos", {}).get("LP", 0)
    lp_total = lp_natural + bonus_lp
    bonus = ficha.get("bonus_passivos", {})

    ab = max(atributos.get("AGI", 1),
             atributos.get("FOR", 1),
             atributos.get("INT", 1),
             atributos.get("VIG", 1),
             atributos.get("PRE", 1))
    
    dt_base = 10 + lp_total + (nex_valor / 2.0) + ab
    dt_tecnica = dt_base + bonus.get("DT_HABILIDADES_TECNICA", 0)


    contexto = {
        "LP": lp_total,
        "LP_NATURAL": lp_natural,
        "AB": ab,
        "GRAU": grau_num,
        "NEX": nex_valor,
        "AGI": atributos.get("AGI", 1),
        "FOR": atributos.get("FOR", 1),
        "INT": atributos.get("INT", 1),
        "VIG": atributos.get("VIG", 1),
        "PRE": atributos.get("PRE", 1),
        "EA": ea_valor,
        "PASSO_DANO_TECNICA": bonus.get("PASSO_DANO_TECNICA", 0),
        "PASSO_TECNICA": bonus.get("PASSO_TECNICA", 0),
        "DADO_TECNICA": bonus.get("DADO_TECNICA", 0),
        "DADO_POR_DADO_TECNICA": bonus.get("DADO_POR_DADO_TECNICA", 0),
        "DANO_PERCENTUAL_GERAL": bonus.get("DANO_PERCENTUAL_GERAL", 0),
        "DANO_PERCENTUAL_TECNICA": bonus.get("DANO_PERCENTUAL_TECNICA", 0),
        "DT_BASE": dt_base,
        "DT_TECNICA": dt_tecnica,
        "DT_HABILIDADES_TECNICA": bonus.get("DT_HABILIDADES_TECNICA", 0),
    }
    return contexto

# ══════════════════════════════════════════════════════════════════════════════
# Importação da classe principal da interface
# ══════════════════════════════════════════════════════════════════════════════
from views.FichaPersonagem import FichaPersonagem