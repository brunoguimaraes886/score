"""XP e nível da gamificação (GAM-05, GAM-15, GAM-16, GAM-18, GAM-24, GAM-25). Conta pura: sem banco e sem HTTP.

O XP não é dinheiro, mas a conta também não passa por float: as frações
são Fraction (exatas), e o único número aproximado é o log10, calculado
em Decimal com LOG_PRECISION dígitos.
"""

from decimal import Decimal, localcontext
from fractions import Fraction
from math import floor
from typing import NamedTuple


# GAM-15: 10 níveis; o nível nunca cai (GAM-05).
MAX_LEVEL = 10

# GAM-24: cada nível custa 1.000 × n² de XP.
LEVEL_COST_FACTOR = 1000

# GAM-16, GAM-18: XP da transferência = (x / 4) · log10(n · 10), com
# x = centavos ÷ 100. Em centavos: centavos / 400 · log10(n · 10).
TRANSFER_XP_CENTS_DIVISOR = 400
LOG_ARGUMENT_FACTOR = 10

# GAM-25: o XP do recorde conta reais inteiros.
CENTS_PER_REAL = 100

# Dígitos do log10 em Decimal: muito mais do que o XP inteiro precisa.
LOG_PRECISION = 50


class XpGain(NamedTuple):
    """O resultado de um ganho de XP: o nível e o XP depois dele, quanto XP entrou e quantos níveis subiram."""

    level: int
    xp: int
    xp_gained: int
    levels_gained: int


def next_level_n(level: int) -> int:
    """O n das fórmulas (GAM-16): o próximo nível. Nível 0 → 1; nível 9 → 10; no nível 10, n continua 10."""
    if level < 0 or level > MAX_LEVEL:
        raise ValueError(f"level precisa estar entre 0 e {MAX_LEVEL}, veio {level}")

    if level == MAX_LEVEL:
        return MAX_LEVEL

    return level + 1


def level_cost(next_level: int) -> int:
    """O XP que custa chegar a next_level, saindo do nível anterior (GAM-24): 1.000 × n²."""
    if next_level < 1 or next_level > MAX_LEVEL:
        raise ValueError(f"next_level precisa estar entre 1 e {MAX_LEVEL}, veio {next_level}")

    return LEVEL_COST_FACTOR * next_level * next_level


def record_whole_reais(new_balance_cents: int, record_cents: int) -> int:
    """Quantos reais inteiros o saldo novo do cofrinho passou do recorde (GAM-25).

    reais inteiros do saldo novo − reais inteiros do recorde; nunca menos
    que 0. Os centavos não se perdem: viram XP quando completam um real.
    """
    if new_balance_cents < 0 or record_cents < 0:
        raise ValueError(f"saldo e recorde não podem ser negativos, vieram {new_balance_cents} e {record_cents}")

    whole_reais = new_balance_cents // CENTS_PER_REAL - record_cents // CENTS_PER_REAL

    if whole_reais < 0:
        return 0

    return whole_reais


def gain_transfer_xp(level: int, xp: int, amount_cents: int) -> XpGain:
    """O XP de uma transferência de amount_cents para quem está em `level` com `xp` (GAM-16, GAM-17).

    Cada centavo vale log10(n · 10) / 400 de XP, com o n do nível em que
    a conta está naquele momento.
    """
    if amount_cents < 1:
        raise ValueError(f"amount_cents precisa ser pelo menos 1, veio {amount_cents}")

    return _gain(level, xp, Fraction(amount_cents), _transfer_xp_per_cent)


def gain_record_xp(level: int, xp: int, whole_reais: int) -> XpGain:
    """O XP de um novo recorde do cofrinho: n de XP por real inteiro (GAM-16, GAM-25)."""
    if whole_reais < 0:
        raise ValueError(f"whole_reais não pode ser negativo, veio {whole_reais}")

    return _gain(level, xp, Fraction(whole_reais), _record_xp_per_real)


def _transfer_xp_per_cent(n: int) -> Fraction:
    with localcontext() as context:
        context.prec = LOG_PRECISION
        log = Decimal(n * LOG_ARGUMENT_FACTOR).log10()

    return Fraction(log) / TRANSFER_XP_CENTS_DIVISOR


def _record_xp_per_real(n: int) -> Fraction:
    return Fraction(n)


def _gain(level: int, xp: int, units: Fraction, xp_per_unit) -> XpGain:
    """Soma o XP de `units` (centavos ou reais) a quem está em `level` com `xp`.

    Enquanto o valor que resta completa o nível, a parte do valor que
    completa o nível é gasta com o n desse nível, o nível sobe, o XP zera
    e o resto do valor segue com o n novo (GAM-05, GAM-24). No nível 10, o
    XP cresce sem teto (GAM-16). O XP final é truncado uma vez, no fim
    (GAM-18): nenhuma fração se perde ao subir de nível.
    """
    if xp < 0:
        raise ValueError(f"xp não pode ser negativo, veio {xp}")

    if level < MAX_LEVEL and xp >= level_cost(next_level_n(level)):
        raise ValueError(f"xp {xp} já completa o nível {level + 1}")

    start_level = level
    start_xp = xp
    current_xp = Fraction(xp)
    remaining = units
    completed_levels_cost = 0

    while level < MAX_LEVEL:
        n = next_level_n(level)
        rate = xp_per_unit(n)
        missing_xp = level_cost(n) - current_xp

        if remaining * rate < missing_xp:
            break

        remaining = remaining - missing_xp / rate
        completed_levels_cost = completed_levels_cost + level_cost(n)
        level = level + 1
        current_xp = Fraction(0)

    final_xp = floor(current_xp + remaining * xp_per_unit(next_level_n(level)))

    return XpGain(level, final_xp, completed_levels_cost + final_xp - start_xp, level - start_level)
