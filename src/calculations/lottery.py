"""Sorteio da chance de não debitar (GAM-10, GAM-11, GAM-22). Conta pura: sem banco e sem HTTP.

O gerador de números entra por parâmetro (TST-06): na API, o do sistema
operacional; no teste, um falso, que devolve o número que o teste quer.
"""


# GAM-22: concorre a transferência de até R$ 100,00, sem contar a tarifa.
PRIZE_LIMIT_CENTS = 10000

# GAM-10: cada ponto em chance vale 0,1 p.p. = 1 número em 1000.
DRAW_SIZE = 1000

# GAM-10, GAM-15: no máximo 10 pontos em chance (1%).
MAX_CHANCE_POINTS = 10


def is_eligible_for_prize(amount_cents: int) -> bool:
    """True quando a transferência concorre ao sorteio: valor de 1 a PRIZE_LIMIT_CENTS centavos, sem a tarifa (GAM-22)."""
    if type(amount_cents) is not int:
        raise TypeError(f"amount_cents precisa ser int, veio {type(amount_cents).__name__}")

    if amount_cents < 1:
        raise ValueError(f"amount_cents precisa ser pelo menos 1, veio {amount_cents}")

    return amount_cents <= PRIZE_LIMIT_CENTS


def draw_prize(chance_points: int, rng) -> bool:
    """Sorteia um número de 0 a DRAW_SIZE − 1 com `rng`; ganha quem tirou menos que os pontos em chance (GAM-10, GAM-11).

    `rng` é qualquer objeto com randrange(stop), como random.SystemRandom.
    Com 0 pontos, nunca ganha; com 10, ganha em 10 de 1000 números (1%).
    """
    if type(chance_points) is not int:
        raise TypeError(f"chance_points precisa ser int, veio {type(chance_points).__name__}")

    if chance_points < 0 or chance_points > MAX_CHANCE_POINTS:
        raise ValueError(f"chance_points precisa estar entre 0 e {MAX_CHANCE_POINTS}, veio {chance_points}")

    return rng.randrange(DRAW_SIZE) < chance_points
