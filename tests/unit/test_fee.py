"""Tarifa da transferência: calculate_fee (MOV-06, MOV-10, GAM-09, TST-05).

Unitário: importa só de calculations, da biblioteca padrão e do pytest.
O pytest.ini põe src/ no caminho de import.
"""

import pytest

from calculations import calculate_fee


class TestCalculateFee:
    def test_one_percent_of_the_amount(self):
        assert calculate_fee(10000, 0) == 100
        assert calculate_fee(100, 0) == 1
        assert calculate_fee(1200, 0) == 12
        assert calculate_fee(100000, 0) == 1000

    def test_rounds_up_to_the_cent(self):
        assert calculate_fee(1234, 0) == 13
        assert calculate_fee(101, 0) == 2
        assert calculate_fee(99, 0) == 1
        assert calculate_fee(1, 0) == 1
        assert calculate_fee(1000, 9) == 1
        assert calculate_fee(1, 9) == 1

    def test_splitting_never_costs_less(self):
        for first in range(1, 301, 7):
            for second in range(1, 301, 11):
                assert calculate_fee(first, 0) + calculate_fee(second, 0) >= calculate_fee(first + second, 0), (first, second)

    def test_each_fee_point_removes_a_tenth_of_a_percentage_point(self):
        for fee_points in range(0, 11):
            assert calculate_fee(10000, fee_points) == 100 - 10 * fee_points, fee_points

    def test_ten_fee_points_make_the_fee_zero(self):
        assert calculate_fee(1, 10) == 0
        assert calculate_fee(1000000000000, 10) == 0

    def test_returns_int_never_float(self):
        for amount_cents, fee_points in [(1, 0), (1234, 0), (10000, 3), (1, 10)]:
            assert type(calculate_fee(amount_cents, fee_points)) is int, (amount_cents, fee_points)

    def test_exact_for_the_largest_bigint(self):
        assert calculate_fee(9223372036854775807, 0) == 92233720368547759

    def test_refuses_points_out_of_range(self):
        for fee_points in [-1, 11]:
            with pytest.raises(ValueError):
                calculate_fee(10000, fee_points)

    def test_refuses_amount_below_one_cent(self):
        for amount_cents in [0, -1]:
            with pytest.raises(ValueError):
                calculate_fee(amount_cents, 0)
