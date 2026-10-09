"""IOF e IR do resgate: calculations.taxes (COF-12, COF-24, TST-05).

Unitário: importa só de calculations, da biblioteca padrão e do pytest.
Em cada lote, IOF = rendimento × % do IOF pelo prazo; IR = (rendimento −
IOF) × % do IR pelo prazo, como na vida real. Cada imposto é somado em
todos os lotes e arredondado uma vez, para cima; o imposto nunca passa do
rendimento.
"""

import pytest

from calculations import iof_percent, ir_percent, redemption_taxes


IOF_TABLE = [
    "96", "93", "90", "86", "83", "80", "76", "73", "70", "66",
    "63", "60", "56", "53", "50", "46", "43", "40", "36", "33",
    "30", "26", "23", "20", "16", "13", "10", "6", "3",
]


class TestIofPercent:
    def test_real_table_from_day_one_to_twenty_nine(self):
        assert [iof_percent(days) for days in range(1, 30)] == IOF_TABLE

    def test_zero_from_thirty_days(self):
        for days in [30, 31, 180, 3650]:
            assert iof_percent(days) == "0"

    def test_refuses_invalid_days(self):
        for days in [0, -1]:
            with pytest.raises(ValueError):
                iof_percent(days)

        with pytest.raises(TypeError):
            iof_percent(1.0)


class TestIrPercent:
    def test_brackets_by_term(self):
        expected = {0: "22.5", 1: "22.5", 180: "22.5", 181: "20", 360: "20", 361: "17.5", 720: "17.5", 721: "15", 3650: "15"}

        for days, percent in expected.items():
            assert ir_percent(days) == percent, days

    def test_refuses_invalid_days(self):
        with pytest.raises(ValueError):
            ir_percent(-1)

        with pytest.raises(TypeError):
            ir_percent(30.0)


class TestRedemptionTaxes:
    def test_one_day_lot(self):
        assert redemption_taxes([(1, 1000)]) == (960, 9)
        assert redemption_taxes([(1, 500)]) == (480, 5)

    def test_ir_base_is_the_yield_minus_iof(self):
        assert redemption_taxes([(15, 1000)]) == (500, 113)
        assert redemption_taxes([(29, 1000)]) == (30, 219)
        # IOF exato 4,5: IR ceil(4,5 * 22,5%) = 2, antes do limite.
        assert redemption_taxes([(15, 9)]) == (5, 2)

    def test_no_iof_from_thirty_days(self):
        assert redemption_taxes([(30, 1000)]) == (0, 225)

    def test_long_terms(self):
        assert redemption_taxes([(181, 1000)]) == (0, 200)
        assert redemption_taxes([(361, 1000)]) == (0, 175)
        assert redemption_taxes([(721, 1000)]) == (0, 150)

    def test_each_lot_uses_its_own_term(self):
        assert redemption_taxes([(2, 1005), (1, 500)]) == (1415, 21)
        assert redemption_taxes([(1, 500), (2, 1005)]) == (1415, 21)

    def test_rounds_once_for_the_whole_redemption(self):
        assert redemption_taxes([(15, 1)]) == (1, 0)
        assert redemption_taxes([(15, 1), (15, 1)]) == (1, 1)

    def test_tax_never_passes_the_yield(self):
        assert redemption_taxes([(1, 1)]) == (1, 0)
        assert redemption_taxes([(30, 1)]) == (0, 1)

        for days in range(1, 40):
            for yield_cents in range(1, 30):
                iof, ir = redemption_taxes([(days, yield_cents)])

                assert iof + ir <= yield_cents, (days, yield_cents)

    def test_parts_without_yield_pay_nothing(self):
        assert redemption_taxes([]) == (0, 0)
        assert redemption_taxes([(0, 0), (400, 0)]) == (0, 0)
        assert redemption_taxes([(0, 0), (1, 1000)]) == (960, 9)

    def test_refuses_invalid_input(self):
        for yield_parts in [[(1, -1)], [(-1, 0)], [(0, 1)]]:
            with pytest.raises(ValueError):
                redemption_taxes(yield_parts)

        for yield_parts in [[(1, 1.5)], [(1.0, 10)]]:
            with pytest.raises(TypeError):
                redemption_taxes(yield_parts)

    def test_returns_int_never_float(self):
        for value in redemption_taxes([(2, 1005), (1, 500)]):
            assert type(value) is int

        assert type(iof_percent(1)) is str
        assert type(ir_percent(1)) is str
