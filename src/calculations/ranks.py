"""Ranques do cofrinho (GAM-12, GAM-13, GAM-14, COF-02). Conta pura: sem banco e sem HTTP.

Os ranques são os enumerators da tabela piggy_rank, em texto: esta pasta
não importa models.
"""


# GAM-12: do menor para o maior.
RANK_ORDER = ("DEFAULT", "BRONZE", "SILVER", "GOLD", "PLATINUM", "DIAMOND")

# GAM-13: o saldo mínimo do cofrinho, em centavos, para alcançar cada ranque.
RANK_MINIMUM_CENTS = {
    "DEFAULT": 0,
    "BRONZE": 200000,
    "SILVER": 500000,
    "GOLD": 1000000,
    "PLATINUM": 3000000,
    "DIAMOND": 5000000,
}

# COF-02: quanto o cofrinho rende em cada ranque, em % do CDI. Em texto:
# vira Decimal exato na conta do rendimento (R6) e sai igual na resposta
# da gamificação (docs/rotas.md, "Formatos").
RANK_CDI_PERCENT = {
    "DEFAULT": "100",
    "BRONZE": "102.5",
    "SILVER": "105",
    "GOLD": "110",
    "PLATINUM": "115",
    "DIAMOND": "120",
}

# GAM-14: dias de carência, contados do dia em que o cofrinho caiu abaixo
# do mínimo do ranque.
GRACE_DAYS = 30


def rank_for_balance(balance_cents: int) -> str:
    """O maior ranque cujo mínimo o saldo do cofrinho alcança (GAM-12, GAM-13). Sem teto (COF-11)."""
    if balance_cents < 0:
        raise ValueError(f"saldo do cofrinho não pode ser negativo, veio {balance_cents}")

    rank = RANK_ORDER[0]
    for candidate in RANK_ORDER:
        if balance_cents >= RANK_MINIMUM_CENTS[candidate]:
            rank = candidate

    return rank
