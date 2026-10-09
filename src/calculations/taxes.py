"""IOF e IR do resgate do cofrinho (COF-12, COF-24). Conta pura: sem banco e sem HTTP.

Os percentuais ficam em texto, como em ranks.py, e viram Decimal exato na
conta (R6). O prazo de cada lote é contado em dias corridos do relógio do
banco: a data contábil do resgate menos a data contábil do lote.
"""

from decimal import ROUND_CEILING, Decimal, localcontext


# COF-12: IOF regressivo, a tabela real (Decreto 6.306/2007, anexo): o
# percentual do rendimento que vira IOF no resgate com 1, 2, ..., 29 dias.
IOF_PERCENT_BY_DAY = (
    "96", "93", "90", "86", "83", "80", "76", "73", "70", "66",
    "63", "60", "56", "53", "50", "46", "43", "40", "36", "33",
    "30", "26", "23", "20", "16", "13", "10", "6", "3",
)

# COF-12: a partir de 30 dias, sem IOF.
IOF_FREE_DAYS = 30

# COF-12: IR regressivo pelo prazo do lote: (até quantos dias, percentual).
IR_PERCENT_BY_TERM = (
    (180, "22.5"),
    (360, "20"),
    (720, "17.5"),
)

# COF-12: acima de 720 dias.
IR_LONG_TERM_PERCENT = "15"

# Para passar de percentual para fração.
PERCENT = Decimal(100)

# Dígitos significativos da conta em Decimal: sobra para qualquer valor em BIGINT.
TAX_PRECISION = 50


def iof_percent(days: int) -> str:
    """O percentual do rendimento que vira IOF num resgate com `days` dias de prazo (COF-12).

    De 1 a 29 dias, a tabela real; a partir de 30, "0". Menos de 1 dia não
    tem rendimento (o lote só rende na virada, que avança o relógio), e é
    recusado com ValueError.
    """
    if type(days) is not int:
        raise TypeError(f"days precisa ser int, veio {type(days).__name__}")

    if days < 1:
        raise ValueError(f"o IOF conta a partir de 1 dia, veio {days}")

    if days >= IOF_FREE_DAYS:
        return "0"

    return IOF_PERCENT_BY_DAY[days - 1]


def ir_percent(days: int) -> str:
    """O percentual de IR sobre o rendimento de um lote com `days` dias de prazo (COF-12).

    22,5% até 180 dias; 20% até 360; 17,5% até 720; 15% acima de 720.
    """
    if type(days) is not int:
        raise TypeError(f"days precisa ser int, veio {type(days).__name__}")

    if days < 0:
        raise ValueError(f"prazo negativo: {days}")

    for limit_days, percent in IR_PERCENT_BY_TERM:
        if days <= limit_days:
            return percent

    return IR_LONG_TERM_PERCENT


def redemption_taxes(yield_parts: list) -> tuple:
    """O IOF e o IR de um resgate: (iof, ir), em centavos inteiros (COF-12, COF-24).

    `yield_parts`: uma tupla (dias de prazo, centavos de rendimento) por
    lote de onde o resgate tirou dinheiro. O imposto incide só sobre o
    rendimento (COF-24); parte sem rendimento não paga nada.

    Em cada lote, como na vida real: IOF = rendimento × iof_percent(dias);
    IR = (rendimento − IOF) × ir_percent(dias). Os valores exatos de todos
    os lotes são somados, e cada imposto é arredondado uma vez, no total do
    resgate, para cima (COF-12). O imposto nunca passa do rendimento: o IR
    para em rendimento − IOF (COF-24).
    """
    yield_total = 0
    iof_exact = Decimal(0)
    ir_exact = Decimal(0)

    with localcontext() as context:
        context.prec = TAX_PRECISION

        for days, yield_cents in yield_parts:
            for name, value in [("days", days), ("yield_cents", yield_cents)]:
                if type(value) is not int:
                    raise TypeError(f"{name} precisa ser int, veio {type(value).__name__}")

            if days < 0 or yield_cents < 0:
                raise ValueError(f"parte de resgate inválida: {days} dias, {yield_cents} centavos")

            if yield_cents == 0:
                continue

            lot_iof = Decimal(yield_cents) * Decimal(iof_percent(days)) / PERCENT
            lot_ir = (Decimal(yield_cents) - lot_iof) * Decimal(ir_percent(days)) / PERCENT

            yield_total = yield_total + yield_cents
            iof_exact = iof_exact + lot_iof
            ir_exact = ir_exact + lot_ir

        iof = int(iof_exact.to_integral_value(rounding=ROUND_CEILING))
        ir = int(ir_exact.to_integral_value(rounding=ROUND_CEILING))

    return iof, min(ir, yield_total - iof)
