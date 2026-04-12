def formatar_numero_grande(valor: int) -> str:
    if abs(valor) < 1000:
        return str(valor)
    sufixos = ['', 'K', 'M', 'B', 'T', 'Qa', 'Qi', 'Sx', 'Sp', 'Oc', 'No', 'Dc']
    valor_float = float(valor)
    idx = 0
    while abs(valor_float) >= 1000 and idx < len(sufixos) - 1:
        valor_float /= 1000.0
        idx += 1
    # Formata com até duas casas decimais e remove zeros desnecessários
    formatado = f"{valor_float:,.2f}".rstrip('0').rstrip('.')
    return f"{formatado}{sufixos[idx]}"