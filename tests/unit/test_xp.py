"""XP e nível: calculations.xp (GAM-05, GAM-15, GAM-16, GAM-18, GAM-24, GAM-25, TST-05).

Unitário: importa só de calculations, da biblioteca padrão e do pytest.
O pytest.ini põe src/ no caminho de import.
"""

import pytest

from calculations import MAX_LEVEL, XpGain, gain_record_xp, gain_transfer_xp, level_cost, next_level_n, record_whole_reais


class TestLevels:
    def test_ten_levels(self):
        assert MAX_LEVEL == 10

    def test_level_cost_is_1000_times_n_squared(self):
        assert level_cost(1) == 1000
        assert level_cost(2) == 4000
        assert level_cost(9) == 81000
        assert level_cost(10) == 100000
        assert sum(level_cost(next_level) for next_level in range(1, 11)) == 385000

    def test_n_is_the_next_level_and_stays_ten(self):
        assert next_level_n(0) == 1
        assert next_level_n(1) == 2
        assert next_level_n(9) == 10
        assert next_level_n(10) == 10

    def test_refuses_levels_out_of_range(self):
        for next_level in [0, 11]:
            with pytest.raises(ValueError):
                level_cost(next_level)

        for level in [-1, 11]:
            with pytest.raises(ValueError):
                next_level_n(level)


class TestTransferXp:
    def test_quarter_of_the_reais_at_level_zero(self):
        assert gain_transfer_xp(0, 0, 10000) == XpGain(0, 25, 25, 0)
        assert gain_transfer_xp(0, 0, 400) == XpGain(0, 1, 1, 0)
        assert gain_transfer_xp(0, 7, 10000) == XpGain(0, 32, 25, 0)

    def test_xp_is_truncated(self):
        assert gain_transfer_xp(0, 0, 399) == XpGain(0, 0, 0, 0)
        assert gain_transfer_xp(0, 0, 1234) == XpGain(0, 3, 3, 0)
        assert gain_transfer_xp(0, 0, 1) == XpGain(0, 0, 0, 0)

    def test_uses_log_of_n_times_ten(self):
        assert gain_transfer_xp(1, 0, 10000) == XpGain(1, 32, 32, 0)
        assert gain_transfer_xp(4, 0, 10000) == XpGain(4, 42, 42, 0)
        assert gain_transfer_xp(10, 0, 10000) == XpGain(10, 50, 50, 0)

    def test_exact_cost_reaches_the_next_level(self):
        assert gain_transfer_xp(0, 0, 400000) == XpGain(1, 0, 1000, 1)
        assert gain_transfer_xp(0, 0, 399999) == XpGain(0, 999, 999, 0)

    def test_level_up_carries_the_rest_with_the_new_n(self):
        assert gain_transfer_xp(0, 990, 10000) == XpGain(1, 19, 29, 1)

    def test_several_levels_in_one_operation(self):
        assert gain_transfer_xp(0, 0, 1700000) == XpGain(2, 259, 5259, 2)

    def test_reaches_level_ten_and_has_no_cap(self):
        assert gain_transfer_xp(0, 0, 83000000) == XpGain(10, 1500, 386500, 10)
        assert gain_transfer_xp(10, 1500, 40000) == XpGain(10, 1700, 200, 0)
        assert gain_transfer_xp(10, 1000000000, 40000) == XpGain(10, 1000000200, 200, 0)

    def test_refuses_invalid_input(self):
        for level, xp, amount_cents in [(0, 0, 0), (0, 0, -1), (0, -1, 100), (0, 1000, 100), (1, 4000, 100), (11, 0, 100), (-1, 0, 100)]:
            with pytest.raises(ValueError):
                gain_transfer_xp(level, xp, amount_cents)


class TestRecordXp:
    def test_n_xp_per_whole_real(self):
        assert gain_record_xp(0, 0, 10) == XpGain(0, 10, 10, 0)
        assert gain_record_xp(2, 0, 10) == XpGain(2, 30, 30, 0)
        assert gain_record_xp(10, 0, 7) == XpGain(10, 70, 70, 0)

    def test_level_up_carries_the_rest_with_the_new_n(self):
        assert gain_record_xp(1, 3995, 10) == XpGain(2, 22, 27, 1)
        assert gain_record_xp(0, 0, 12345) == XpGain(4, 11725, 41725, 4)

    def test_zero_reais_gives_no_xp(self):
        assert gain_record_xp(3, 7, 0) == XpGain(3, 7, 0, 0)

    def test_record_counts_whole_reais(self):
        assert record_whole_reais(100120, 100050) == 1
        assert record_whole_reais(100099, 100050) == 0
        assert record_whole_reais(500000, 0) == 5000
        assert record_whole_reais(99, 0) == 0
        assert record_whole_reais(100, 250) == 0

    def test_refuses_invalid_input(self):
        with pytest.raises(ValueError):
            gain_record_xp(0, 0, -1)

        for new_balance_cents, record_cents in [(-1, 0), (0, -1)]:
            with pytest.raises(ValueError):
                record_whole_reais(new_balance_cents, record_cents)


class TestXpGain:
    def test_fields_in_order(self):
        assert XpGain._fields == ("level", "xp", "xp_gained", "levels_gained")

    def test_returns_int_never_float(self):
        for xp_gain in [gain_transfer_xp(0, 990, 10000), gain_transfer_xp(4, 0, 10000), gain_record_xp(1, 3995, 10)]:
            assert type(xp_gain) is XpGain
            for value in xp_gain:
                assert type(value) is int, xp_gain

        assert type(record_whole_reais(100120, 100050)) is int
