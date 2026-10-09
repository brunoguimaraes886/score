"""Rendimento diário do cofrinho (COF-02, COF-13, COF-15). Conta pura: sem banco e sem HTTP.

Dinheiro inteiro em centavos (int); a taxa e a fração de centavo em
Decimal, nunca float (R6).
"""

from decimal import ROUND_DOWN, Decimal, localcontext


# COF-15: a taxa diária e o resíduo do lote têm 8 casas.
EIGHT_PLACES = Decimal("0.00000001")

# Para passar de percentual para fração.
PERCENT = Decimal(100)

# Dígitos significativos da conta em Decimal: sobra para qualquer saldo em BIGINT.
YIELD_PRECISION = 50


def daily_rate(cdi_daily_percent: str, rank_cdi_percent: str) -> Decimal:
    """A taxa do dia como fração, truncada na 8ª casa (COF-02, COF-15).

    cdi_daily_percent: o CDI do dia em % ao dia, como o Banco Central o
    publica ("0.054266" = 0,054266% ao dia). rank_cdi_percent: o % do CDI
    do ranque (RANK_CDI_PERCENT, "102.5"). Os dois em texto, nunca float.
    A taxa é CDI ÷ 100 × percentual ÷ 100, cortada na 8ª casa: o banco
    nunca paga a mais (decisão de 08/10). 0,054266% a 110% = 0,000596926 →
    0,00059692.
    """
    for name, value in [("cdi_daily_percent", cdi_daily_percent), ("rank_cdi_percent", rank_cdi_percent)]:
        if type(value) is not str:
            raise TypeError(f"{name} precisa ser texto, veio {type(value).__name__}")

    with localcontext() as context:
        context.prec = YIELD_PRECISION
        rate = Decimal(cdi_daily_percent) / PERCENT * Decimal(rank_cdi_percent) / PERCENT

        if rate < 0:
            raise ValueError(f"taxa negativa: {cdi_daily_percent} x {rank_cdi_percent}")

        return rate.quantize(EIGHT_PLACES, rounding=ROUND_DOWN)


def lot_yield(lot_balance_cents: int, residue: Decimal, rate: Decimal) -> tuple:
    """O rendimento de um lote num dia: (centavos inteiros, resíduo novo) (COF-13, COF-15).

    O valor exato é o saldo do lote × a taxa + o resíduo de ontem. Os
    centavos inteiros viram lançamento hoje; a fração (de 0 a menos de 1
    centavo) fica no lote para amanhã. Com a taxa e o resíduo em 8 casas, a
    conta é exata: nada se arredonda aqui.
    """
    if type(lot_balance_cents) is not int:
        raise TypeError(f"lot_balance_cents precisa ser int, veio {type(lot_balance_cents).__name__}")

    for name, value in [("residue", residue), ("rate", rate)]:
        if type(value) is not Decimal:
            raise TypeError(f"{name} precisa ser Decimal, veio {type(value).__name__}")

    if lot_balance_cents < 0:
        raise ValueError(f"saldo do lote não pode ser negativo, veio {lot_balance_cents}")

    if residue < 0 or residue >= 1:
        raise ValueError(f"o resíduo é uma fração de centavo, de 0 a menos de 1; veio {residue}")

    if rate < 0:
        raise ValueError(f"taxa negativa: {rate}")

    with localcontext() as context:
        context.prec = YIELD_PRECISION
        exact = Decimal(lot_balance_cents) * rate + residue
        cents = int(exact.to_integral_value(rounding=ROUND_DOWN))

        return cents, (exact - cents).quantize(EIGHT_PLACES, rounding=ROUND_DOWN)
