"""XP do recorde na virada: POST /internal/day_closings e a gamificação."""

from tests.utils import DbUtils, MockGenerator, ObjectGenerator, PayloadGenerator, RequestGenerator


ONE_PERCENT = "1.000000"
HALF_PERCENT = "0.500000"


def close_day(accounting_date: str) -> None:
    status, response = RequestGenerator.POST_day_closing(PayloadGenerator.day_closing(accounting_date))
    assert status == 200, response


def record_progress_of(account: dict) -> tuple:
    status, response = RequestGenerator.GET_gamification(account["account_key"], account["account_token"])
    assert status == 200, response
    return response["level"], response["xp"], response["piggy_record"]


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


class TestDayClosingRecordXp:
    def test_yield_above_the_record_gives_xp(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate("2026-06-01", ONE_PERCENT)
        account = ObjectGenerator.create_funded_account(100000)
        save(account, 100000)
        assert record_progress_of(account) == (1, 0, 100000)
        close_day("2026-06-01")
        assert piggy_bank_balance_of(account) == 101000
        assert record_progress_of(account) == (1, 20, 101000)
        MockGenerator.clear_cdi("2026-06-01")

    def test_yield_below_the_record_gives_no_xp_until_it_passes(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate("2026-06-01", ONE_PERCENT)
        MockGenerator.set_cdi_rate("2026-06-02", ONE_PERCENT)
        account = ObjectGenerator.create_funded_account(100000)
        save(account, 100000)
        redeem(account, 1000)
        assert record_progress_of(account) == (1, 0, 100000)
        close_day("2026-06-01")
        assert piggy_bank_balance_of(account) == 99990
        assert record_progress_of(account) == (1, 0, 100000)
        close_day("2026-06-02")
        assert piggy_bank_balance_of(account) == 100989
        assert record_progress_of(account) == (1, 18, 100989)
        MockGenerator.clear_cdi("2026-06-01")
        MockGenerator.clear_cdi("2026-06-02")

    def test_cents_of_yield_become_xp_when_they_complete_a_real(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate("2026-06-01", HALF_PERCENT)
        MockGenerator.set_cdi_rate("2026-06-02", HALF_PERCENT)
        account = ObjectGenerator.create_funded_account(10000)
        save(account, 10000)
        assert record_progress_of(account) == (0, 100, 10000)
        close_day("2026-06-01")
        assert piggy_bank_balance_of(account) == 10050
        assert record_progress_of(account) == (0, 100, 10050)
        close_day("2026-06-02")
        assert piggy_bank_balance_of(account) == 10100
        assert record_progress_of(account) == (0, 101, 10100)
        MockGenerator.clear_cdi("2026-06-01")
        MockGenerator.clear_cdi("2026-06-02")

    def test_blocked_account_gains_record_xp(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate("2026-06-01", ONE_PERCENT)
        account = ObjectGenerator.create_funded_account(100000)
        save(account, 100000)
        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
        assert status == 204, response
        close_day("2026-06-01")
        assert piggy_bank_balance_of(account) == 101000
        assert record_progress_of(account) == (1, 20, 101000)
        MockGenerator.clear_cdi("2026-06-01")
