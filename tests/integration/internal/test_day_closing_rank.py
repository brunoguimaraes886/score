"""Ranque e carência na virada (GAM-12, GAM-13, GAM-14, GAM-19, COF-02, CLI-05, CLI-07)."""

from datetime import date, timedelta

from tests.utils import DbUtils, MockGenerator, ObjectGenerator, PayloadGenerator, RequestGenerator


CDI = "0.054266"
FIRST_DAY = date(2026, 6, 1)


def day(offset: int) -> str:
    return (FIRST_DAY + timedelta(days=offset)).isoformat()


def close_day(accounting_date: str) -> None:
    status, response = RequestGenerator.POST_day_closing(PayloadGenerator.day_closing(accounting_date))
    assert status == 200, response


def rank_of(account: dict) -> tuple:
    status, response = RequestGenerator.GET_gamification(account["account_key"], account["account_token"])
    assert status == 200, response
    return response["rank"], response["cdi_percent"], response["grace_until"]


def piggy_bank_balance_of(account: dict) -> int:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response
    return response["piggy_bank_balance"]


def save(account: dict, amount: int) -> None:
    status, response = RequestGenerator.POST_saving(account["account_key"], account["account_token"], PayloadGenerator.saving(amount=amount))
    assert status == 201, response


def redeem(account: dict, amount: int) -> None:
    status, response = RequestGenerator.POST_redemption(account["account_key"], account["account_token"], PayloadGenerator.redemption(amount=amount))
    assert status == 201, response


def create_account_in_grace() -> dict:
    account = ObjectGenerator.create_funded_account(300000)
    save(account, 200000)
    redeem(account, 1)
    return account


class TestDayClosingRank:
    def test_rank_goes_up_at_day_closing(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0), "0.100000")
        account = ObjectGenerator.create_funded_account(200000)
        save(account, 199900)
        assert rank_of(account) == ("DEFAULT", "100", None)
        close_day(day(0))
        assert piggy_bank_balance_of(account) == 200099
        assert rank_of(account) == ("BRONZE", "102.5", None)
        MockGenerator.clear_cdi(day(0))

    def test_yield_rank_follows_the_rank_from_the_next_day(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0), CDI)
        MockGenerator.set_cdi_rate(day(1), CDI)
        account = ObjectGenerator.create_funded_account(1000000)
        save(account, 1000000)
        close_day(day(0))
        assert piggy_bank_balance_of(account) == 1000542
        close_day(day(1))
        assert piggy_bank_balance_of(account) == 1001139
        MockGenerator.clear_cdi(day(0))
        MockGenerator.clear_cdi(day(1))

    def test_grace_starts_and_keeps_yielding_at_the_rank(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0))
        MockGenerator.set_cdi_rate(day(1), CDI)
        account = ObjectGenerator.create_funded_account(300000)
        save(account, 200000)
        redeem(account, 10000)
        assert rank_of(account) == ("BRONZE", "102.5", None)
        close_day(day(0))
        assert rank_of(account) == ("BRONZE", "102.5", "2026-07-01")
        close_day(day(1))
        assert piggy_bank_balance_of(account) == 190105
        assert rank_of(account) == ("BRONZE", "102.5", "2026-07-01")
        MockGenerator.clear_cdi(day(0))
        MockGenerator.clear_cdi(day(1))

    def test_grace_ends_when_the_balance_returns(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0))
        MockGenerator.set_cdi_rate(day(1))
        account = create_account_in_grace()
        close_day(day(0))
        assert rank_of(account) == ("BRONZE", "102.5", "2026-07-01")
        save(account, 1)
        assert rank_of(account) == ("BRONZE", "102.5", "2026-07-01")
        close_day(day(1))
        assert rank_of(account) == ("BRONZE", "102.5", None)
        MockGenerator.clear_cdi(day(0))
        MockGenerator.clear_cdi(day(1))

    def test_rank_falls_straight_to_the_balance_rank_after_thirty_days(self):
        DbUtils.rollback()
        for offset in range(31):
            MockGenerator.set_cdi_rate(day(offset))
        account = ObjectGenerator.create_funded_account(1000000)
        save(account, 1000000)
        redeem(account, 700000)
        assert rank_of(account) == ("GOLD", "110", None)
        close_day(day(0))
        assert rank_of(account) == ("GOLD", "110", "2026-07-01")
        for offset in range(1, 30):
            close_day(day(offset))
        assert day(29) == "2026-06-30"
        assert rank_of(account) == ("GOLD", "110", "2026-07-01")
        close_day(day(30))
        assert rank_of(account) == ("BRONZE", "102.5", None)
        for offset in range(31):
            MockGenerator.clear_cdi(day(offset))

    def test_blocked_account_rank_follows(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0))
        account = create_account_in_grace()
        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
        assert status == 204, response
        close_day(day(0))
        assert rank_of(account) == ("BRONZE", "102.5", "2026-07-01")
        MockGenerator.clear_cdi(day(0))

    def test_closed_account_is_skipped(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0))
        open_account = create_account_in_grace()
        closed_account = ObjectGenerator.create_funded_account(200000)
        save(closed_account, 200000)
        redeem(closed_account, 200000)
        status, response = RequestGenerator.POST_withdrawal(closed_account["account_key"], closed_account["account_token"], PayloadGenerator.withdrawal(amount=200000))
        assert status == 201, response
        status, response = RequestGenerator.DELETE_account(closed_account["account_key"], closed_account["account_token"])
        assert status == 204, response
        close_day(day(0))
        assert rank_of(open_account) == ("BRONZE", "102.5", "2026-07-01")
        assert rank_of(closed_account) == ("BRONZE", "102.5", None)
        MockGenerator.clear_cdi(day(0))
