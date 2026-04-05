import json
import os

CAMINHO_SKILLTREES = os.path.join(os.path.dirname(__file__), "..", "data", "skilltrees.json")

def carregar_skilltrees() -> dict:
    with open(CAMINHO_SKILLTREES, "r", encoding="utf-8") as f:
        return json.load(f)

def nos_da_arvore(atributo: str, skilltrees: dict) -> list:
    return skilltrees.get(atributo, {}).get("nos", [])

def pontos_disponiveis_skilltree(valor_atributo: int) -> int:
    return valor_atributo * 2

def requisitos_satisfeitos(no: dict, nos_comprados: set) -> bool:
    return all(req in nos_comprados for req in no["requisitos"])

def pode_comprar(no: dict, nos_comprados: set, pontos_disponiveis: int) -> bool:
    return (
        no["id"] not in nos_comprados and
        requisitos_satisfeitos(no, nos_comprados) and
        pontos_disponiveis >= no["custo"]
    )

def calcular_posicoes(nos: list) -> dict:
    """
    Calcula posições (coluna, linha) de cada nó.
    - Coluna = profundidade (distância da raiz)
    - Linha  = posição vertical, mantendo filhos próximos aos pais
               e garantindo que não haja dois nós na mesma célula.
    Retorna dict { no_id: (coluna, linha) }
    """
    nos_por_id = {no["id"]: no for no in nos}

    # ── Passo 1: calcula coluna de cada nó ───────────────────────────────────
    colunas = {}

    def get_coluna(no_id, visitados=None):
        if visitados is None:
            visitados = set()
        if no_id in colunas:
            return colunas[no_id]
        if no_id in visitados:  # ciclo — não deve acontecer mas protege
            return 0
        visitados.add(no_id)
        no = nos_por_id[no_id]
        if not no["requisitos"]:
            colunas[no_id] = 0
        else:
            colunas[no_id] = 1 + max(get_coluna(r, visitados) for r in no["requisitos"])
        return colunas[no_id]

    for no in nos:
        get_coluna(no["id"])

    # ── Passo 2: agrupa por coluna mantendo ordem original ───────────────────
    por_coluna = {}
    for no in nos:
        col = colunas[no["id"]]
        por_coluna.setdefault(col, []).append(no["id"])

    # ── Passo 3: posiciona linha a linha, resolvendo colisões ────────────────
    posicoes  = {}   # { no_id: (coluna, linha) }
    ocupadas  = {}   # { coluna: set(linhas ocupadas) }

    def linha_media_pais(no_id):
        no = nos_por_id[no_id]
        pais = [posicoes[r][1] for r in no["requisitos"] if r in posicoes]
        return sum(pais) / len(pais) if pais else 0

    def proxima_linha_livre(col, linha_desejada):
        """Encontra a linha livre mais próxima da linha desejada."""
        usadas = ocupadas.get(col, set())
        if linha_desejada not in usadas:
            return linha_desejada
        # Busca em espiral: 0, +1, -1, +2, -2, ...
        for delta in range(1, len(nos) + 1):
            for candidata in (linha_desejada + delta, linha_desejada - delta):
                if candidata >= 0 and candidata not in usadas:
                    return candidata
        return linha_desejada  # fallback (não deve chegar aqui)

    for col in sorted(por_coluna.keys()):
        nos_col = por_coluna[col]

        # Ordena pela posição média dos pais já posicionados
        nos_col_ordenados = sorted(
            nos_col,
            key=lambda nid: (linha_media_pais(nid), nos.index(nos_por_id[nid]))
        )

        ocupadas[col] = set()
        for no_id in nos_col_ordenados:
            linha_ideal  = round(linha_media_pais(no_id))
            linha_final  = proxima_linha_livre(col, linha_ideal)
            posicoes[no_id] = (col, linha_final)
            ocupadas[col].add(linha_final)

    return posicoes

def vender_no(no, nos_comprados, pontos_skilltree):
    if no["id"] in nos_comprados:
        nos_comprados.remove(no["id"])
        pontos_skilltree += no["custo"]
    return nos_comprados, pontos_skilltree

def tem_filhos_comprados(no_id, todos_nos, nos_comprados):
    for no in todos_nos:
        if no["id"] in nos_comprados and no_id in no["requisitos"]:
            return True
    return False