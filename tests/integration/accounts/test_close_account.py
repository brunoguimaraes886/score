"""Encerrar conta: DELETE /accounts/{account_key} (CLI-04, CLI-05, CLI-06, CLI-09, API-17, R8)."""

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator


def account_status(account: dict) -> str:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response
    return response["status"]


def close(account: dict) -> None:
    status, response = RequestGenerator.DELETE_account(account["account_key"], account["account_token"])
    assert status == 204, response
    assert response is None


def assert_not_active(status: int, response: dict) -> None:
    assert status == 409, response
    assert response["code"] == "QIT001011"


def assert_account_not_found(status: int, response: dict) -> None:
    assert status == 404, response
    assert response["code"] == "QIT001010"


class TestCloseAccount:
    def test_closes_account(self):
        account = ObjectGenerator.create_account()
        close(account)
        status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
        assert status == 200, response
        assert response["status"] == "CLOSED"
        assert response["balance"] == 0

    def test_closed_account_cannot_be_closed_again(self):
        account = ObjectGenerator.create_account()
        close(account)
        status, response = RequestGenerator.DELETE_account(account["account_key"], account["account_token"])
        assert_not_active(status, response)
        assert account_status(account) == "CLOSED"

    def test_blocked_account_cannot_be_closed(self):
        account = ObjectGenerator.create_account()
        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
        assert status == 204, response
        status, response = RequestGenerator.DELETE_account(account["account_key"], account["account_token"])
        assert_not_active(status, response)
        assert account_status(account) == "BLOCKED"
        status, response = RequestGenerator.POST_unblock(account["account_key"])
        assert status == 204, response
        close(account)
        assert account_status(account) == "CLOSED"

    def test_customer_opens_new_account_after_closing(self):
        old_account = ObjectGenerator.create_account()
        close(old_account)
        status, response = RequestGenerator.POST_account(old_account["customer_key"])
        assert status == 201, response
        new_account = {"customer_key": old_account["customer_key"], "account_key": response["account_key"], "account_token": response["account_token"]}
        assert new_account["account_key"] != old_account["account_key"]
        assert new_account["account_token"] != old_account["account_token"]
        status, response = RequestGenerator.GET_account(new_account["account_key"], new_account["account_token"])
        assert status == 200, response
        assert response["status"] == "ACTIVE"
        assert response["balance"] == 0
        assert account_status(old_account) == "CLOSED"
        status, response = RequestGenerator.GET_customer(old_account["customer_key"], old_account["account_token"])
        assert status == 404, response
        assert response["code"] == "QIT001008"
        status, response = RequestGenerator.GET_customer(new_account["customer_key"], new_account["account_token"])
        assert status == 200, response
        status, response = RequestGenerator.POST_account(old_account["customer_key"])
        assert status == 409, response
        assert response["code"] == "QIT001009"

    def test_closed_account_cannot_be_blocked_or_unblocked(self):
        account = ObjectGenerator.create_account()
        close(account)
        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
        assert_not_active(status, response)
        status, response = RequestGenerator.POST_unblock(account["account_key"])
        assert status == 409, response
        assert response["code"] == "QIT001013"
        assert account_status(account) == "CLOSED"

    def test_other_account_token_is_404(self):
        DbUtils.rollback()
        first = ObjectGenerator.create_account()
        second = ObjectGenerator.create_account()
        status, response = RequestGenerator.DELETE_account(first["account_key"], second["account_token"])
        assert_account_not_found(status, response)
        assert account_status(first) == "ACTIVE"
        close(first)

    def test_missing_or_wrong_token_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()
        for account_token in [None, "token_errado"]:
            status, response = RequestGenerator.DELETE_account(account["account_key"], account_token)
            assert_account_not_found(status, response)
        assert account_status(account) == "ACTIVE"
