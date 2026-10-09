"""Tarifa da transferência (MOV-06, MOV-10, GAM-09). Conta pura: só inteiros, sem banco e sem HTTP."""


# MOV-06: a tarifa cheia é 1% = 10 décimos de ponto percentual.
FULL_FEE_TENTHS_OF_PERCENT = 10

# GAM-09, GAM-15: cada ponto em tarifa tira 1 décimo de ponto percentual;
# com os 10 pontos, a tarifa é 0%.
MAX_FEE_POINTS = 10

# Um décimo de ponto percentual é 1/1000 do valor.
TENTHS_OF_PERCENT_DIVISOR = 1000


def calculate_fee(amount_cents: int, fee_points: int) -> int:
    """A tarifa da transferência, em centavos inteiros.

    tarifa = teto(amount_cents × (10 − fee_points) / 1000)

    Arredonda para cima ao centavo (MOV-10): 1% de R$ 12,34 = 12,34
    centavos → 13. Assim, dividir uma transferência em duas nunca sai mais
    barato. A conta é feita só com inteiros: somar o divisor menos 1 antes
    da divisão inteira (//) é o teto sem passar por float (R6, DAD-08).

    Recusa com ValueError o que nenhuma regra permite: valor abaixo de 1
    centavo (API-18) e pontos fora de 0 a 10 (GAM-09).
    """
    if amount_cents < 1:
        raise ValueError(f"amount_cents precisa ser pelo menos 1, veio {amount_cents}")

    if fee_points < 0 or fee_points > MAX_FEE_POINTS:
        raise ValueError(f"fee_points precisa estar entre 0 e {MAX_FEE_POINTS}, veio {fee_points}")

    tenths_of_percent = FULL_FEE_TENTHS_OF_PERCENT - fee_points

    return (amount_cents * tenths_of_percent + TENTHS_OF_PERCENT_DIVISOR - 1) // TENTHS_OF_PERCENT_DIVISOR
