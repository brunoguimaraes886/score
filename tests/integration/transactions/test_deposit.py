"""Depósito: POST /accounts/{account_key}/deposits (MOV-07, MOV-09, MOV-12, MOV-15, MOV-16, MOV-19, CLI-09).

Qualquer um com o INTERNAL-TOKEN deposita em qualquer conta de cliente,
informando nome e CPF ou CNPJ de quem deposita; não pede ACCOUNT-TOKEN.
O saldo sobe exatamente o valor, sem tarifa. A resposta traz só a key da
operação. Os testes que erram o token começam com DbUtils.rollback() (PRD-10).
"""

import re
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RandomGenerator, RequestGenerator


UUID_V4 = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
PARALLEL_REQUESTS = 8


def balance_of(account: dict) -> int:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response
    assert type(response["balance"]) is int, response

    return response["balance"]


def deposit(account: dict, payload: dict) -> tuple:
    return RequestGenerator.POST_deposit(account["account_key"], payload)


class TestDeposit:
    def test_deposits_into_account(self):
        account = ObjectGenerator.create_account()

        status, response = deposit(account, PayloadGenerator.deposit(amount=50000))

        assert status == 201, response
        assert sorted(response) == ["transaction_key"]
        assert UUID_V4.match(response["transaction_key"])
        assert balance_of(account) == 50000

        status, response = deposit(account, PayloadGenerator.deposit(amount=2550))

        assert status == 201, response
        assert balance_of(account) == 52550

    def test_deposits_with_cnpj(self):
        account = ObjectGenerator.create_account()

        status, response = deposit(account, PayloadGenerator.deposit(amount=1, depositor_document=RandomGenerator.generate_cnpj()))

        assert status == 201, response
        assert balance_of(account) == 1

    def test_refuses_invalid_document(self):
        account = ObjectGenerator.create_account()

        for depositor_document in ["123.456.789-00", "111.111.111-11", "11.222.333/0001-80", "11.111.111/1111-11"]:
            status, response = deposit(account, PayloadGenerator.deposit(depositor_document=depositor_document))

            assert status == 422, (depositor_document, response)
            assert response["code"] == "QIT001003"

        assert balance_of(account) == 0

    def test_refuses_body_out_of_schema(self):
        account = ObjectGenerator.create_account()
        bodies = []

        for amount in [0, -1, 50.5, 5050.0, "5050", True, None]:
            bodies.append(PayloadGenerator.deposit(amount=amount))

        for field in ["depositor_name", "depositor_document", "amount", "request_control_key"]:
            body = PayloadGenerator.deposit()
            del body[field]
            bodies.append(body)

        bodies.append(dict(PayloadGenerator.deposit(), extra=1))
        bodies.append(PayloadGenerator.deposit(request_control_key=str(uuid4()).upper()))
        bodies.append(PayloadGenerator.deposit(depositor_document="12345678909"))
        bodies.append(PayloadGenerator.deposit(depositor_name=""))

        for body in bodies:
            status, response = deposit(account, body)

            assert status == 400, (body, response)
            assert response["code"] == "QIT000001"

        assert balance_of(account) == 0

    def test_unknown_account_is_404(self):
        for account_key in [str(uuid4()), "nao-e-uma-key"]:
            status, response = RequestGenerator.POST_deposit(account_key, PayloadGenerator.deposit())

            assert status == 404, (account_key, response)
            assert response["code"] == "QIT001010"

    def test_blocked_or_closed_account_refuses_deposit(self):
        account = ObjectGenerator.create_account()

        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
        assert status == 204, response

        status, response = deposit(account, PayloadGenerator.deposit(amount=1000))
        assert status == 409, response
        assert response["code"] == "QIT001011"

        status, response = RequestGenerator.POST_unblock(account["account_key"])
        assert status == 204, response

        status, response = deposit(account, PayloadGenerator.deposit(amount=1000))
        assert status == 201, response
        assert balance_of(account) == 1000

        closed_account = ObjectGenerator.create_account()
        status, response = RequestGenerator.DELETE_account(closed_account["account_key"], closed_account["account_token"])
        assert status == 204, response

        status, response = deposit(closed_account, PayloadGenerator.deposit(amount=1000))
        assert status == 409, response
        assert response["code"] == "QIT001011"
        assert balance_of(closed_account) == 0

    def test_repeated_request_returns_first_response(self):
        account = ObjectGenerator.create_account()
        payload = PayloadGenerator.deposit(amount=3000)

        first_status, first_response = deposit(account, payload)
        second_status, second_response = deposit(account, payload)

        assert first_status == 201, first_response
        assert second_status == 201, second_response
        assert second_response == first_response
        assert balance_of(account) == 3000

    def test_same_key_with_other_request_is_409(self):
        account = ObjectGenerator.create_account()
        other_account = ObjectGenerator.create_account()
        payload = PayloadGenerator.deposit(amount=3000)

        status, response = deposit(account, payload)
        assert status == 201, response

        for target, body in [(account, dict(payload, amount=3001)), (other_account, payload)]:
            status, response = deposit(target, body)

            assert status == 409, (body, response)
            assert response["code"] == "QIT001014"

        assert balance_of(account) == 3000
        assert balance_of(other_account) == 0

    def test_refused_request_does_not_keep_the_key(self):
        account = ObjectGenerator.create_account()
        request_control_key = str(uuid4())

        status, response = deposit(account, PayloadGenerator.deposit(depositor_document="123.456.789-00", request_control_key=request_control_key))
        assert status == 422, response

        status, response = deposit(account, PayloadGenerator.deposit(amount=700, request_control_key=request_control_key))
        assert status == 201, response
        assert balance_of(account) == 700

    def test_requires_internal_token(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()

        for internal_token in [None, "token_errado"]:
            status, response = RequestGenerator.POST_deposit(account["account_key"], PayloadGenerator.deposit(), internal_token=internal_token)

            assert status == 403, (internal_token, response)
            assert response["code"] == "QIT000002"

        status, response = deposit(account, PayloadGenerator.deposit(amount=100))
        assert status == 201, response
        assert balance_of(account) == 100

    def test_concurrent_same_key(self):
        account = ObjectGenerator.create_account()
        payload = PayloadGenerator.deposit(amount=4000)

        with ThreadPoolExecutor(max_workers=PARALLEL_REQUESTS) as executor:
            results = list(executor.map(lambda _index: deposit(account, payload), range(PARALLEL_REQUESTS)))

        assert [status for status, _response in results] == [201] * PARALLEL_REQUESTS, results
        assert len({response["transaction_key"] for _status, response in results}) == 1, results
        assert balance_of(account) == 4000
