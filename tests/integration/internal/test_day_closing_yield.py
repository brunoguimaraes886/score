"""Rendimento na virada: POST /internal/day_closings e o cofrinho (COF-02, COF-13, COF-15, COF-16, COF-22, COF-23, CLI-07, GAM-19).

Cada lote rende sobre o próprio saldo, pela taxa do ranque que rende no
dia; os centavos inteiros entram no cofrinho, e a fração fica para o dia
seguinte. CDI de teste: 0,054266% ao dia (taxa 0,00054266 a 100%). Todo
teste começa com DbUtils.rollback() (o relógio volta a 2026-06-01) e
programa no Mockserver a taxa de cada dia que fecha.
"""

from datetime import date, timedelta

from tests.utils import DbUtils, MockGenerator, ObjectGenerator, PayloadGenerator, RequestGenerator


CDI = "0.054266"
FIRST_DAY = date(2026, 6, 1)


def day(offset: int) -> str:
    return (FIRST_DAY + timedelta(days=offset)).isoformat()


def close_day(accounting_date: str) -> None:
    status, response = RequestGenerator.POST_day_closing(PayloadGenerator.day_closing(accounting_date))
    assert status == 200, response


def piggy_bank_balance_of(account: dict) -> int:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response
    return response["piggy_bank_balance"]


def piggy_bank_entries(account: dict) -> list:
    status, response = RequestGenerator.GET_piggy_bank_entries(account["account_key"], account["account_token"], {"limit": "100"})
    assert status == 200, response
    return response["data"]


def save(account: dict, amount: int) -> None:
    status, response = RequestGenerator.POST_saving(account["account_key"], account["account_token"], PayloadGenerator.saving(amount=amount))
    assert status == 201, response


def redeem(account: dict, amount: int) -> None:
    status, response = RequestGenerator.POST_redemption(account["account_key"], account["account_token"], PayloadGenerator.redemption(amount=amount))
    assert status == 201, response


class TestDayClosingYield:
    def test_yields_whole_cents_and_keeps_the_fraction(self):
        DbUtils.rollback()
        for offset in range(4):
            MockGenerator.set_cdi_rate(day(offset), CDI)
        account = ObjectGenerator.create_funded_account(100000)
        save(account, 100000)
        balances = []
        for offset in range(4):
            close_day(day(offset))
            balances.append(piggy_bank_balance_of(account))
        assert balances == [100054, 100108, 100162, 100217]
        for offset in range(4):
            MockGenerator.clear_cdi(day(offset))

    def test_each_lot_yields_on_its_own(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0), CDI)
        two_lots = ObjectGenerator.create_funded_account(2000)
        one_lot = ObjectGenerator.create_funded_account(2000)
        save(two_lots, 1000)
        save(two_lots, 1000)
        save(one_lot, 2000)
        close_day(day(0))
        assert piggy_bank_balance_of(one_lot) == 2001
        assert piggy_bank_balance_of(two_lots) == 2000
        MockGenerator.clear_cdi(day(0))

    def test_redeemed_money_does_not_yield_the_day(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0), CDI)
        account = ObjectGenerator.create_funded_account(100000)
        save(account, 100000)
        redeem(account, 40000)
        close_day(day(0))
        assert piggy_bank_balance_of(account) == 60032
        MockGenerator.clear_cdi(day(0))

    def test_day_without_rate_does_not_yield(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0))
        MockGenerator.set_cdi_rate(day(1), CDI)
        account = ObjectGenerator.create_funded_account(100000)
        save(account, 100000)
        close_day(day(0))
        assert piggy_bank_balance_of(account) == 100000
        assert [entry["transaction_type"] for entry in piggy_bank_entries(account)] == ["SAVE"]
        close_day(day(1))
        assert piggy_bank_balance_of(account) == 100054
        MockGenerator.clear_cdi(day(0))
        MockGenerator.clear_cdi(day(1))

    def test_blocked_account_still_yields(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0), CDI)
        account = ObjectGenerator.create_funded_account(100000)
        save(account, 100000)
        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
        assert status == 204, response
        close_day(day(0))
        assert piggy_bank_balance_of(account) == 100054
        MockGenerator.clear_cdi(day(0))

    def test_yield_uses_the_rank_of_the_start_of_the_day(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0), CDI)
        account = ObjectGenerator.create_funded_account(1000000)
        save(account, 1000000)
        status, response = RequestGenerator.GET_gamification(account["account_key"], account["account_token"])
        assert status == 200, response
        assert response["rank"] == "GOLD"
        close_day(day(0))
        assert piggy_bank_balance_of(account) == 1000542
        MockGenerator.clear_cdi(day(0))

    def test_yield_entry_is_paid_by_the_bank(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0), CDI)
        account = ObjectGenerator.create_funded_account(100000)
        save(account, 100000)
        close_day(day(0))
        entries = piggy_bank_entries(account)
        yield_entry = entries[0]
        assert (yield_entry["transaction_type"], yield_entry["entry_type"], yield_entry["amount"], yield_entry["balance_after"]) == ("YIELD", "YIELD", 54, 100054)
        assert yield_entry["category"]["name"] == "economias"
        assert yield_entry["counterparty"] == {"type": "BANK"}
        assert yield_entry["accounting_date"] == "2026-06-01"
        assert sum(entry["amount"] for entry in entries) == piggy_bank_balance_of(account) == 100054
        status, response = RequestGenerator.GET_transaction(account["account_key"], account["account_token"], yield_entry["transaction_key"])
        assert status == 200, response
        assert (response["type"], response["accounting_date"]) == ("YIELD", "2026-06-01")
        assert "gross_amount" not in response
        assert [(entry["entry_type"], entry["amount"], entry["counterparty"]) for entry in response["entries"]] == [("YIELD", 54, {"type": "BANK"})]
        status, response = RequestGenerator.GET_entries(account["account_key"], account["account_token"])
        assert status == 200, response
        assert [entry["transaction_type"] for entry in response["data"]] == ["SAVE", "DEPOSIT"]
        MockGenerator.clear_cdi(day(0))
