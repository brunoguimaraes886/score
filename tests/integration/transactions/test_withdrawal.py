"""Saque: POST /accounts/{account_key}/withdrawals (MOV-05, MOV-07, MOV-08, MOV-09, MOV-12, MOV-15, MOV-19, CLI-09, R8).

Só o dono saca, com o ACCOUNT-TOKEN. O saldo cai exatamente o valor, sem
tarifa, e nunca fica negativo. A resposta traz a key da operação e o
saldo novo. Os testes que erram o token começam com DbUtils.rollback() (PRD-10).
"""

import re
from concurrent.futures import ThreadPoolExecutor

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator


UUID_V4 = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
PARALLEL_REQUESTS = 8


def balance_of(account: dict) -> int:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response
    assert type(response["balance"]) is int, response

    return response["balance"]


def withdraw(account: dict, payload: dict) -> tuple:
    """Saca da conta com o token dela."""
    return RequestGenerator.POST_withdrawal(account["account_key"], account["account_token"], payload)


class TestWithdrawal:
    def test_withdraws(self):
        account = ObjectGenerator.create_funded_account(100000)

        status, response = withdraw(account, PayloadGenerator.withdrawal(amount=30000))

        assert status == 201, response
        assert sorted(response) == ["balance", "transaction_key"]
        assert UUID_V4.match(response["transaction_key"])
        assert type(response["balance"]) is int
        assert response["balance"] == 70000
        assert balance_of(account) == 70000

    def test_withdraws_the_whole_balance(self):
        account = ObjectGenerator.create_funded_account(5000)

        status, response = withdraw(account, PayloadGenerator.withdrawal(amount=5000))

        assert status == 201, response
        assert response["balance"] == 0
        assert balance_of(account) == 0

    def test_refuses_insufficient_balance(self):
        account = ObjectGenerator.create_funded_account(5000)

        status, response = withdraw(account, PayloadGenerator.withdrawal(amount=5001))
        assert status == 422, response
        assert response["code"] == "QIT001015"
        assert balance_of(account) == 5000

        empty_account = ObjectGenerator.create_account()

        status, response = withdraw(empty_account, PayloadGenerator.withdrawal(amount=1))
        assert status == 422, response
        assert response["code"] == "QIT001015"
        assert balance_of(empty_account) == 0

    def test_refuses_body_out_of_schema(self):
        account = ObjectGenerator.create_funded_account(5000)
        bodies = []

        for amount in [0, -1, 1.5, 1000.0, "1000", True]:
            bodies.append(PayloadGenerator.withdrawal(amount=amount))

        for field in ["amount", "request_control_key"]:
            body = PayloadGenerator.withdrawal()
            del body[field]
            bodies.append(body)

        bodies.append(dict(PayloadGenerator.withdrawal(), extra=1))

        for body in bodies:
            status, response = withdraw(account, body)

            assert status == 400, (body, response)
            assert response["code"] == "QIT000001"

        assert balance_of(account) == 5000

    def test_blocked_or_closed_account_refuses_withdrawal(self):
        account = ObjectGenerator.create_funded_account(5000)

        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
        assert status == 204, response

        status, response = withdraw(account, PayloadGenerator.withdrawal(amount=1000))
        assert status == 409, response
        assert response["code"] == "QIT001011"
        assert balance_of(account) == 5000

        status, response = RequestGenerator.POST_unblock(account["account_key"])
        assert status == 204, response

        status, response = withdraw(account, PayloadGenerator.withdrawal(amount=5000))
        assert status == 201, response

        status, response = RequestGenerator.DELETE_account(account["account_key"], account["account_token"])
        assert status == 204, response

        status, response = withdraw(account, PayloadGenerator.withdrawal(amount=1))
        assert status == 409, response
        assert response["code"] == "QIT001011"

    def test_other_account_token_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_funded_account(5000)
        other_account = ObjectGenerator.create_account()

        status, response = RequestGenerator.POST_withdrawal(account["account_key"], other_account["account_token"], PayloadGenerator.withdrawal(amount=1000))
        assert status == 404, response
        assert response["code"] == "QIT001010"
        assert balance_of(account) == 5000

        status, response = withdraw(account, PayloadGenerator.withdrawal(amount=1000))
        assert status == 201, response
        assert balance_of(account) == 4000

    def test_missing_or_wrong_token_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_funded_account(5000)

        for account_token in [None, "token_errado"]:
            status, response = RequestGenerator.POST_withdrawal(account["account_key"], account_token, PayloadGenerator.withdrawal(amount=1000))

            assert status == 404, (account_token, response)
            assert response["code"] == "QIT001010"

        assert balance_of(account) == 5000

    def test_repeated_request_returns_first_response(self):
        account = ObjectGenerator.create_funded_account(10000)
        payload = PayloadGenerator.withdrawal(amount=3000)

        first_status, first_response = withdraw(account, payload)
        second_status, second_response = withdraw(account, payload)

        assert first_status == 201, first_response
        assert second_status == 201, second_response
        assert second_response == first_response
        assert first_response["balance"] == 7000

        status, response = withdraw(account, PayloadGenerator.withdrawal(amount=2000))
        assert status == 201, response

        third_status, third_response = withdraw(account, payload)
        assert third_status == 201, third_response
        assert third_response == first_response
        assert balance_of(account) == 5000

        # A repetição simultânea deve passar mesmo quando a primeira esgota o saldo.
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier

        raced = ObjectGenerator.create_funded_account(1000)
        raced_payload = PayloadGenerator.withdrawal(amount=1000)
        gate = Barrier(2)

        def send_same(_index):
            gate.wait(timeout=5)
            return withdraw(raced, raced_payload)

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(send_same, range(2)))

        assert results[0][0] == 201, results
        assert results == [results[0], results[0]], results
        assert balance_of(raced) == 0

    def test_same_key_with_other_request_is_409(self):
        account = ObjectGenerator.create_funded_account(10000)
        payload = PayloadGenerator.withdrawal(amount=3000)

        status, response = withdraw(account, payload)
        assert status == 201, response

        status, response = withdraw(account, dict(payload, amount=3001))
        assert status == 409, response
        assert response["code"] == "QIT001014"

        deposit_payload = PayloadGenerator.deposit(amount=3000, request_control_key=payload["request_control_key"])
        status, response = RequestGenerator.POST_deposit(account["account_key"], deposit_payload)
        assert status == 409, response
        assert response["code"] == "QIT001014"

        assert balance_of(account) == 7000

    def test_concurrent_withdrawals_never_go_negative(self):
        account = ObjectGenerator.create_funded_account(10000)
        payloads = [PayloadGenerator.withdrawal(amount=3000) for _index in range(PARALLEL_REQUESTS)]

        with ThreadPoolExecutor(max_workers=PARALLEL_REQUESTS) as executor:
            results = list(executor.map(lambda payload: withdraw(account, payload), payloads))

        statuses = sorted(status for status, _response in results)
        assert statuses == [201] * 3 + [422] * (PARALLEL_REQUESTS - 3), results
        assert balance_of(account) == 1000
