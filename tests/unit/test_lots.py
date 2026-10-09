"""Resgate de um lote: calculations.lots (COF-24, TST-05).

Unitário: importa só de calculations, da biblioteca padrão e do pytest.
Principal e rendimento saem na proporção do lote; a parte de rendimento é
arredondada para cima ao centavo (decisão de 08/10).
"""

import pytest

from calculations import split_redemption


class TestSplitRedemption:
    def test_whole_lot_takes_everything(self):
        assert split_redemption(10000, 250, 10250) == (10000, 250)

    def test_part_follows_the_proportion(self):
        assert split_redemption(10000, 250, 4100) == (4000, 100)
        assert split_redemption(100000, 54, 50000) == (49973, 27)

    def test_yield_part_rounds_up(self):
        assert split_redemption(10000, 1, 100) == (99, 1)
        assert split_redemption(10000, 250, 1) == (0, 1)

    def test_lot_without_yield(self):
        assert split_redemption(5000, 0, 3000) == (3000, 0)

    def test_parts_always_add_up(self):
        for amount_cents in range(1, 43):
            principal_part, yield_part = split_redemption(37, 5, amount_cents)

            assert principal_part + yield_part == amount_cents
            assert 0 <= principal_part <= 37
            assert 0 <= yield_part <= 5

    def test_refuses_invalid_input(self):
        for principal_remaining, yield_remaining, amount_cents in [(100, 10, 0), (100, 10, 111), (-1, 10, 5), (100, -1, 5), (0, 0, 1)]:
            with pytest.raises(ValueError):
                split_redemption(principal_remaining, yield_remaining, amount_cents)

    def test_returns_int_never_float(self):
        for value in split_redemption(100000, 54, 50000):
            assert type(value) is int
