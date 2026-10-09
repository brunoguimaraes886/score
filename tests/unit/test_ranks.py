"""Ranques do cofrinho: calculations.ranks (GAM-12, GAM-13, GAM-14, COF-02, COF-11, TST-05).

Unitário: importa só de calculations, da biblioteca padrão e do pytest.
O pytest.ini põe src/ no caminho de import.
"""

from decimal import Decimal

import pytest

from calculations import GRACE_DAYS, RANK_CDI_PERCENT, RANK_MINIMUM_CENTS, RANK_ORDER, rank_for_balance


class TestRanks:
    def test_order_from_default_to_diamond(self):
        assert RANK_ORDER == ("DEFAULT", "BRONZE", "SILVER", "GOLD", "PLATINUM", "DIAMOND")

    def test_minimum_of_each_rank(self):
        assert RANK_MINIMUM_CENTS == {
            "DEFAULT": 0,
            "BRONZE": 200000,
            "SILVER": 500000,
            "GOLD": 1000000,
            "PLATINUM": 3000000,
            "DIAMOND": 5000000,
        }

    def test_cdi_percent_of_each_rank(self):
        assert RANK_CDI_PERCENT == {
            "DEFAULT": "100",
            "BRONZE": "102.5",
            "SILVER": "105",
            "GOLD": "110",
            "PLATINUM": "115",
            "DIAMOND": "120",
        }

    def test_grace_is_thirty_days(self):
        assert GRACE_DAYS == 30

    def test_rank_for_balance_at_each_minimum(self):
        assert rank_for_balance(0) == "DEFAULT"
        assert rank_for_balance(199999) == "DEFAULT"
        assert rank_for_balance(200000) == "BRONZE"
        assert rank_for_balance(499999) == "BRONZE"
        assert rank_for_balance(500000) == "SILVER"
        assert rank_for_balance(999999) == "SILVER"
        assert rank_for_balance(1000000) == "GOLD"
        assert rank_for_balance(2999999) == "GOLD"
        assert rank_for_balance(3000000) == "PLATINUM"
        assert rank_for_balance(4999999) == "PLATINUM"
        assert rank_for_balance(5000000) == "DIAMOND"

    def test_no_maximum(self):
        assert rank_for_balance(9223372036854775807) == "DIAMOND"

    def test_refuses_negative_balance(self):
        with pytest.raises(ValueError):
            rank_for_balance(-1)

    def test_returns_text_never_float(self):
        for rank in RANK_ORDER:
            assert type(RANK_CDI_PERCENT[rank]) is str
            assert type(RANK_MINIMUM_CENTS[rank]) is int
            assert Decimal(RANK_CDI_PERCENT[rank]) >= Decimal("100")

        assert type(rank_for_balance(200000)) is str
