"""Abertura de conta: POST /customers/{customer_key}/accounts (CLI-01, CLI-04, API-16, TST-03)."""

import re
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from tests.utils import DbUtils, ObjectGenerator, RequestGenerator


UUID_V4 = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
ACCOUNT_TOKEN = re.compile(r"^[A-Za-z0-9_-]{43}$")
PARALLEL_REQUESTS = 8


def assert_no_internal_id(body: dict) -> None:
    for field in body:
        assert field != "id", field
        assert not field.endswith("_id"), field


class TestOpenAccount:
    def test_opens_account(self):
        customer_key = ObjectGenerator.create_customer()
        status, response = RequestGenerator.POST_account(customer_key)
        assert status == 201, response
        assert sorted(response) == ["account_key", "account_token"]
        assert UUID_V4.match(response["account_key"])
        assert ACCOUNT_TOKEN.match(response["account_token"])
        assert_no_internal_id(response)
        other_account = ObjectGenerator.create_account()
        assert other_account["account_key"] != response["account_key"]
        assert other_account["account_token"] != response["account_token"]

    def test_refuses_unknown_customer(self):
        for customer_key in [str(uuid4()), "nao-e-uma-key"]:
            status, response = RequestGenerator.POST_account(customer_key)
            assert status == 404, (customer_key, response)
            assert response["code"] == "QIT001008"
            assert "account_key" not in response
            assert "account_token" not in response

    def test_refuses_second_open_account(self):
        account = ObjectGenerator.create_account()
        status, response = RequestGenerator.POST_account(account["customer_key"])
        assert status == 409, response
        assert response["code"] == "QIT001009"

    def test_requires_internal_token(self):
        DbUtils.rollback()
        status, response = RequestGenerator.POST_account(ObjectGenerator.create_customer())
        assert status == 201, response
        customer_key = ObjectGenerator.create_customer()
        for internal_token in [None, "token_errado"]:
            status, response = RequestGenerator.POST_account(customer_key, internal_token=internal_token)
            assert status == 403, (internal_token, response)
            assert response["code"] == "QIT000002"
        status, response = RequestGenerator.POST_account(customer_key)
        assert status == 201, response

    def test_concurrent_openings(self):
        customer_key = ObjectGenerator.create_customer()
        with ThreadPoolExecutor(max_workers=PARALLEL_REQUESTS) as executor:
            results = list(executor.map(RequestGenerator.POST_account, [customer_key] * PARALLEL_REQUESTS))
        statuses = sorted(status for status, _response in results)
        assert statuses == [201] + [409] * (PARALLEL_REQUESTS - 1), results
        codes = [response["code"] for status, response in results if status == 409]
        assert codes == ["QIT001009"] * (PARALLEL_REQUESTS - 1), codes
