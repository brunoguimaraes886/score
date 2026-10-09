"""Resgate de um lote do cofrinho (COF-24). Conta pura: sem banco e sem HTTP."""


def split_redemption(principal_remaining: int, yield_remaining: int, amount_cents: int) -> tuple:
    """Quanto de um resgate sai do principal e quanto do rendimento de um lote: (principal, rendimento), em centavos.

    As duas partes saem na proporção do lote (COF-24). A parte de
    rendimento é arredondada para cima ao centavo, e o principal fica com o
    resto: como na tarifa (MOV-10) e no imposto (COF-12), dividir o resgate
    nunca sai mais barato (decisão de 08/10). Como o resgate não passa do
    saldo do lote, a parte de rendimento nunca passa do rendimento do lote,
    e a de principal nunca passa do principal.
    """
    if principal_remaining < 0 or yield_remaining < 0:
        raise ValueError(f"lote com valor negativo: principal {principal_remaining}, rendimento {yield_remaining}")

    lot_balance = principal_remaining + yield_remaining

    if amount_cents < 1 or amount_cents > lot_balance:
        raise ValueError(f"o resgate de {amount_cents} centavos não cabe no lote de {lot_balance}")

    # -(-a // b) é a divisão inteira arredondada para cima, sem float.
    yield_part = -(-amount_cents * yield_remaining // lot_balance)

    return amount_cents - yield_part, yield_part
