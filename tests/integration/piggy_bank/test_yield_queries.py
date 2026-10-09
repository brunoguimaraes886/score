from datetime import date, timedelta

from tests.utils import DbUtils, MockGenerator, ObjectGenerator, PayloadGenerator, RequestGenerator


def get_account(account):
    status, result = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, result
    assert "piggy_bank_gross_yield" in result
    return result


def get_category(account, key):
    status, result = RequestGenerator.GET_category(account["account_key"], account["account_token"], key)
    assert status == 200, result
    assert "gross_yield" in result
    return result


class TestYieldQueries:
    def test_query_matches_full_redemption_on_the_same_date(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate("2026-06-01", "1.000000")
        account = ObjectGenerator.create_funded_account(100000)
        key, token = account["account_key"], account["account_token"]
        assert RequestGenerator.POST_saving(key, token, PayloadGenerator.saving(amount=100000))[0] == 201
        assert RequestGenerator.POST_day_closing(PayloadGenerator.day_closing("2026-06-01"))[0] == 200
        summary = get_account(account)
        assert (summary["piggy_bank_gross_yield"], summary["piggy_bank_net_yield"], summary["yield_accounting_date"]) == (1000, 31, "2026-06-02")
        category = RequestGenerator.GET_categories(key, token)[1]["data"][0]
        assert (category["gross_yield"], category["net_yield"], category["yield_accounting_date"]) == (1000, 31, "2026-06-02")
        assert get_category(account, category["category_key"]) == category
        status, result = RequestGenerator.POST_redemption(key, token, PayloadGenerator.redemption(amount=101000))
        assert status == 201, result
        assert result["net_amount"] - 100000 == summary["piggy_bank_net_yield"]
        assert get_account(account)["piggy_bank_gross_yield"] == 0
        MockGenerator.clear_cdi("2026-06-01")

    def test_account_adds_the_separate_category_estimates(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_funded_account(200)
        key, token = account["account_key"], account["account_token"]
        first = RequestGenerator.GET_categories(key, token)[1]["data"][0]["category_key"]
        status, result = RequestGenerator.POST_category(key, token, PayloadGenerator.category(name="carro"))
        assert status == 201, result
        second = result["category_key"]
        for category_key in [first, second]:
            assert RequestGenerator.POST_saving(key, token, PayloadGenerator.saving(amount=100, category_key=category_key))[0] == 201
        for offset in range(30):
            day = (date(2026, 6, 1) + timedelta(days=offset)).isoformat()
            MockGenerator.set_cdi_rate(day, "1.000000" if offset == 0 else None)
            assert RequestGenerator.POST_day_closing(PayloadGenerator.day_closing(day))[0] == 200
            MockGenerator.clear_cdi(day)
        summary = get_account(account)
        assert (summary["piggy_bank_gross_yield"], summary["piggy_bank_net_yield"]) == (2, 0)
        for category_key in [first, second]:
            category = get_category(account, category_key)
            assert (category["gross_yield"], category["net_yield"], category["yield_accounting_date"]) == (1, 0, "2026-07-01")
            status, result = RequestGenerator.POST_redemption(key, token, PayloadGenerator.redemption(amount=101, category_key=category_key))
            assert status == 201, result
            assert (result["iof"], result["ir"], result["net_amount"]) == (0, 1, 100)

    def test_empty_blocked_closed_and_deleted_resources_are_readable(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()
        key, token = account["account_key"], account["account_token"]
        status, result = RequestGenerator.POST_category(key, token, PayloadGenerator.category(name="carro"))
        assert status == 201, result
        category_key = result["category_key"]
        assert RequestGenerator.DELETE_category(key, token, category_key)[0] == 204
        for expected_status in ["ACTIVE", "BLOCKED", "CLOSED"]:
            if expected_status == "BLOCKED":
                assert RequestGenerator.POST_block(key, PayloadGenerator.block())[0] == 204
            if expected_status == "CLOSED":
                assert RequestGenerator.POST_unblock(key)[0] == 204
                assert RequestGenerator.DELETE_account(key, token)[0] == 204
            summary = get_account(account)
            assert summary["status"] == expected_status
            assert (summary["piggy_bank_gross_yield"], summary["piggy_bank_net_yield"]) == (0, 0)
            category = get_category(account, category_key)
            assert (category["gross_yield"], category["net_yield"], category["status"]) == (0, 0, "DELETED")
