"""Sorteio da chance de não debitar: calculations.lottery (GAM-10, GAM-11, GAM-22, TST-05, TST-06).

Unitário: importa só de calculations, da biblioteca padrão e do pytest.
O gerador de números é falso (TST-06): devolve sempre o número que o
teste escolheu e anota com que limite foi chamado.
"""

import pytest

from calculations import DRAW_SIZE, PRIZE_LIMIT_CENTS, calculate_fee, draw_prize, is_eligible_for_prize


class FakeRandom:
    """Gerador falso: randrange devolve sempre `value` e guarda o limite pedido."""

    def __init__(self, value: int) -> None:
        self.value = value
        self.stops = []

    def randrange(self, stop: int) -> int:
        self.stops.append(stop)

        return self.value


class TestEligibility:
    def test_prize_limit_is_one_hundred_reais(self):
        assert PRIZE_LIMIT_CENTS == 10000
        assert DRAW_SIZE == 1000

    def test_eligible_up_to_the_limit(self):
        assert is_eligible_for_prize(1) is True
        assert is_eligible_for_prize(10000) is True
        assert is_eligible_for_prize(10001) is False
        assert is_eligible_for_prize(9223372036854775807) is False

    def test_refuses_invalid_amount(self):
        for amount_cents in [0, -1]:
            with pytest.raises(ValueError):
                is_eligible_for_prize(amount_cents)

        with pytest.raises(TypeError):
            is_eligible_for_prize(100.0)


class TestDrawPrize:
    def test_each_point_is_one_in_a_thousand(self):
        rng = FakeRandom(0)
        assert draw_prize(1, rng) is True
        assert rng.stops == [1000]

        assert draw_prize(1, FakeRandom(1)) is False
        assert draw_prize(10, FakeRandom(9)) is True
        assert draw_prize(10, FakeRandom(10)) is False
        assert draw_prize(10, FakeRandom(999)) is False

    def test_without_points_never_wins(self):
        for value in [0, 1, 999]:
            assert draw_prize(0, FakeRandom(value)) is False

    def test_refuses_invalid_points(self):
        for chance_points in [-1, 11]:
            with pytest.raises(ValueError):
                draw_prize(chance_points, FakeRandom(0))

        with pytest.raises(TypeError):
            draw_prize(1.0, FakeRandom(0))

    def test_one_chance_point_is_worth_one_fee_point_at_the_limit(self):
        fee_point_saving = calculate_fee(PRIZE_LIMIT_CENTS, 0) - calculate_fee(PRIZE_LIMIT_CENTS, 1)
        winning_numbers = sum(1 for value in range(DRAW_SIZE) if draw_prize(1, FakeRandom(value)))

        assert fee_point_saving == 10
        assert winning_numbers * PRIZE_LIMIT_CENTS // DRAW_SIZE == fee_point_saving

    def test_returns_bool(self):
        assert type(is_eligible_for_prize(500)) is bool
        assert type(draw_prize(5, FakeRandom(3))) is bool
