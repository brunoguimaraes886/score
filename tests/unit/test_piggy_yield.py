"""Rendimento diário: calculations.piggy_yield (COF-02, COF-13, COF-15, TST-05).

Unitário: importa só de calculations, da biblioteca padrão e do pytest.
CDI de teste: 0,054266% ao dia; a 100% do CDI, a taxa diária é 0,00054266.
"""

from decimal import Decimal

import pytest

from calculations import daily_rate, lot_yield


CDI = "0.054266"
RATE = Decimal("0.00054266")


class TestDailyRate:
    def test_default_rank_is_the_cdi(self):
        assert daily_rate(CDI, "100") == RATE

    def test_rate_of_each_rank(self):
        assert daily_rate(CDI, "102.5") == Decimal("0.00055622")
        assert daily_rate(CDI, "105") == Decimal("0.00056979")
        assert daily_rate(CDI, "110") == Decimal("0.00059692")
        assert daily_rate(CDI, "115") == Decimal("0.00062405")
        assert daily_rate(CDI, "120") == Decimal("0.00065119")

    def test_rate_is_truncated_at_eight_places(self):
        rate = daily_rate(CDI, "110")

        assert rate != Decimal("0.00059693")
        assert rate.as_tuple().exponent == -8
        assert daily_rate("1.000000", "100") == Decimal("0.01")

    def test_refuses_float_and_negative(self):
        with pytest.raises(TypeError):
            daily_rate(0.054266, "100")

        with pytest.raises(TypeError):
            daily_rate(CDI, 100)

        with pytest.raises(ValueError):
            daily_rate("-0.054266", "100")


class TestLotYield:
    def test_keeps_the_fraction_of_the_cent(self):
        assert lot_yield(1000000, Decimal("0"), RATE) == (542, Decimal("0.66"))
        assert lot_yield(100000, Decimal("0"), RATE) == (54, Decimal("0.266"))

    def test_fraction_carries_to_the_next_day(self):
        balance = 100000
        residue = Decimal("0")
        gains = []

        for _ in range(5):
            cents, residue = lot_yield(balance, residue, RATE)
            gains.append(cents)
            balance = balance + cents

        assert gains == [54, 54, 54, 55, 54]
        assert balance == 100271
        assert residue == Decimal("0.62357906")

    def test_small_lot_waits_for_a_whole_cent(self):
        assert lot_yield(1000, Decimal("0"), RATE) == (0, Decimal("0.54266"))
        assert lot_yield(1000, Decimal("0.54266"), RATE) == (1, Decimal("0.08532"))

    def test_zero_rate_keeps_the_residue(self):
        assert lot_yield(500, Decimal("0.3"), Decimal("0")) == (0, Decimal("0.3"))

    def test_refuses_invalid_input(self):
        for lot_balance_cents, residue, rate in [(1000.0, Decimal("0"), RATE), (1000, 0.5, RATE), (1000, Decimal("0"), 0.0005)]:
            with pytest.raises(TypeError):
                lot_yield(lot_balance_cents, residue, rate)

        for lot_balance_cents, residue, rate in [(-1, Decimal("0"), RATE), (1000, Decimal("1"), RATE), (1000, Decimal("-0.1"), RATE), (1000, Decimal("0"), Decimal("-0.1"))]:
            with pytest.raises(ValueError):
                lot_yield(lot_balance_cents, residue, rate)

    def test_returns_int_and_decimal_never_float(self):
        cents, residue = lot_yield(100000, Decimal("0"), RATE)

        assert type(cents) is int
        assert type(residue) is Decimal
        assert type(daily_rate(CDI, "100")) is Decimal
