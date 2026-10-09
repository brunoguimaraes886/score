from tests.utils import DbUtils, MockGenerator, ObjectGenerator, PayloadGenerator, RequestGenerator


MAXIMUM = 9223372036854775807


def account_data(account):
    status, result = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, result
    return result


def entries(account):
    status, result = RequestGenerator.GET_entries(account["account_key"], account["account_token"], {"limit": "100"})
    assert status == 200, result
    return result["data"]


class TestNumericOverflow:
    def test_deposit_at_limit_rejects_next_cent_and_does_not_keep_the_key(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_funded_account(MAXIMUM)
        key, token = account["account_key"], account["account_token"]
        before = entries(account)
        payload = PayloadGenerator.deposit(amount=1)
        status, result = RequestGenerator.POST_deposit(key, payload)
        assert status == 422, result
        assert result["code"] == "QIT001032"
        assert account_data(account)["balance"] == MAXIMUM
        assert entries(account) == before
        assert RequestGenerator.POST_deposit(key, PayloadGenerator.deposit(amount=MAXIMUM + 1))[0] == 400
        assert RequestGenerator.POST_withdrawal(key, token, PayloadGenerator.withdrawal(amount=1))[0] == 201
        assert RequestGenerator.POST_deposit(key, payload)[0] == 201
        assert account_data(account)["balance"] == MAXIMUM

    def test_transfer_overflow_leaves_both_accounts_and_xp_unchanged(self):
        DbUtils.rollback()
        origin = ObjectGenerator.create_funded_account(10100)
        destination = ObjectGenerator.create_funded_account(MAXIMUM)
        before = [entries(origin), entries(destination)]
        payload = PayloadGenerator.transfer(destination["account_key"], amount=10000)
        status, result = RequestGenerator.POST_transfer(origin["account_key"], origin["account_token"], payload)
        assert status == 422, result
        assert result["code"] == "QIT001032"
        assert [account_data(a)["balance"] for a in [origin, destination]] == [10100, MAXIMUM]
        assert [entries(origin), entries(destination)] == before
        for account in [origin, destination]:
            assert RequestGenerator.GET_gamification(account["account_key"], account["account_token"])[1]["xp"] == 0

    def test_yield_overflow_rolls_back_the_whole_day(self):
        DbUtils.rollback()
        earlier = ObjectGenerator.create_funded_account(1000)
        earlier_key, earlier_token = earlier["account_key"], earlier["account_token"]
        assert RequestGenerator.POST_saving(earlier_key, earlier_token, PayloadGenerator.saving(amount=1000))[0] == 201
        earlier_before = account_data(earlier)
        earlier_progress = RequestGenerator.GET_gamification(earlier_key, earlier_token)[1]
        earlier_entries = RequestGenerator.GET_piggy_bank_entries(earlier_key, earlier_token)[1]
        account = ObjectGenerator.create_funded_account(MAXIMUM)
        key, token = account["account_key"], account["account_token"]
        assert RequestGenerator.POST_saving(key, token, PayloadGenerator.saving(amount=MAXIMUM))[0] == 201
        before = account_data(account)
        before_progress = RequestGenerator.GET_gamification(key, token)[1]
        before_entries = RequestGenerator.GET_piggy_bank_entries(key, token)[1]
        MockGenerator.set_cdi_rate("2026-06-01", "1.000000")
        payload = PayloadGenerator.day_closing("2026-06-01")
        status, result = RequestGenerator.POST_day_closing(payload)
        assert status == 422, result
        assert result["code"] == "QIT001032"
        assert account_data(earlier) == earlier_before
        assert RequestGenerator.GET_gamification(earlier_key, earlier_token)[1] == earlier_progress
        assert RequestGenerator.GET_piggy_bank_entries(earlier_key, earlier_token)[1] == earlier_entries
        assert account_data(account) == before
        assert RequestGenerator.GET_gamification(key, token)[1] == before_progress
        assert RequestGenerator.GET_piggy_bank_entries(key, token)[1] == before_entries
        MockGenerator.set_cdi_rate("2026-06-01")
        status, result = RequestGenerator.POST_day_closing(payload)
        assert status == 200, result
        assert result["accounting_date"] == "2026-06-02"
        MockGenerator.clear_cdi("2026-06-01")
