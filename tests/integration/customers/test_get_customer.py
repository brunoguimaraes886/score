"""Consulta do cliente: GET /customers/{customer_key} (API-17, R8, R5)."""

from uuid import uuid4

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator


def assert_no_internal_id(body: dict) -> None:
    for field in body:
        assert field != "id", field
        assert not field.endswith("_id"), field


def assert_customer_not_found(status: int, response: dict) -> None:
    assert status == 404, response
    assert response["code"] == "QIT001008"


def assert_owner_reads_customer(account: dict) -> None:
    status, response = RequestGenerator.GET_customer(account["customer_key"], account["account_token"])
    assert status == 200, response


class TestGetCustomer:
    def test_owner_gets_customer(self):
        payload = PayloadGenerator.customer()
        status, response = RequestGenerator.POST_customer(payload)
        assert status == 201, response
        customer_key = response["customer_key"]
        account = ObjectGenerator.create_account(customer_key)
        status, response = RequestGenerator.GET_customer(customer_key, account["account_token"])
        assert status == 200, response
        assert response == {
            "customer_key": customer_key,
            "name": payload["name"],
            "document_number": payload["document_number"],
            "email": payload["email"],
            "birthdate": payload["birthdate"],
        }
        assert_no_internal_id(response)

    def test_other_account_token_is_404(self):
        DbUtils.rollback()
        first = ObjectGenerator.create_account()
        second = ObjectGenerator.create_account()
        assert_owner_reads_customer(first)
        status, response = RequestGenerator.GET_customer(first["customer_key"], second["account_token"])
        assert_customer_not_found(status, response)
        status, response = RequestGenerator.GET_customer(second["customer_key"], first["account_token"])
        assert_customer_not_found(status, response)

    def test_missing_or_wrong_token_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()
        assert_owner_reads_customer(account)
        for account_token in [None, "token_errado"]:
            status, response = RequestGenerator.GET_customer(account["customer_key"], account_token)
            assert_customer_not_found(status, response)

    def test_unknown_customer_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()
        assert_owner_reads_customer(account)
        for customer_key in [str(uuid4()), "nao-e-uma-key"]:
            status, response = RequestGenerator.GET_customer(customer_key, account["account_token"])
            assert_customer_not_found(status, response)

    def test_customer_without_account_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()
        customer_key = ObjectGenerator.create_customer()
        assert_owner_reads_customer(account)
        for account_token in [account["account_token"], None]:
            status, response = RequestGenerator.GET_customer(customer_key, account_token)
            assert_customer_not_found(status, response)
