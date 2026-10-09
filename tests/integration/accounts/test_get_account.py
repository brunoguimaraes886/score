"""Consulta da conta: GET /accounts/{account_key} (R8, API-09, API-16, R5, DAD-08)."""

from datetime import datetime
from uuid import uuid4

from tests.utils import DbUtils, ObjectGenerator, RequestGenerator


ACCOUNT_FIELDS = ["account_key", "balance", "created_at", "customer_key", "piggy_bank_balance", "piggy_bank_gross_yield", "piggy_bank_net_yield", "status", "yield_accounting_date"]


def assert_no_internal_id(body: dict) -> None:
    for field in body:
        assert field != "id", field
        assert not field.endswith("_id"), field


def assert_account_not_found(status: int, response: dict) -> None:
    assert status == 404, response
    assert response["code"] == "QIT001010"


def assert_owner_reads(account: dict) -> None:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response


class TestGetAccount:
    def test_gets_new_account(self):
        account = ObjectGenerator.create_account()
        status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
        assert status == 200, response
        assert sorted(response) == ACCOUNT_FIELDS
        assert response["account_key"] == account["account_key"]
        assert response["customer_key"] == account["customer_key"]
        assert response["status"] == "ACTIVE"
        assert type(response["balance"]) is int
        assert response["balance"] == 0
        assert type(response["piggy_bank_balance"]) is int
        assert response["piggy_bank_balance"] == 0
        datetime.fromisoformat(response["created_at"])
        assert account["account_token"] not in str(response)
        assert_no_internal_id(response)

    def test_other_account_token_is_404(self):
        DbUtils.rollback()
        first = ObjectGenerator.create_account()
        second = ObjectGenerator.create_account()
        assert_owner_reads(first)
        status, response = RequestGenerator.GET_account(first["account_key"], second["account_token"])
        assert_account_not_found(status, response)
        status, response = RequestGenerator.GET_account(second["account_key"], first["account_token"])
        assert_account_not_found(status, response)

    def test_missing_or_wrong_token_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()
        assert_owner_reads(account)
        for account_token in [None, "token_errado", account["account_key"]]:
            status, response = RequestGenerator.GET_account(account["account_key"], account_token)
            assert_account_not_found(status, response)

    def test_unknown_account_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()
        assert_owner_reads(account)
        for account_key in [str(uuid4()), "nao-e-uma-key"]:
            status, response = RequestGenerator.GET_account(account_key, account["account_token"])
            assert_account_not_found(status, response)

    def test_requires_internal_token(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()
        assert_owner_reads(account)
        status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"], internal_token=None)
        assert status == 403, response
        assert response["code"] == "QIT000002"
