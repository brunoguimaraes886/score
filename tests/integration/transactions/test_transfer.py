"""Transferência: POST /accounts/{account_key}/transfers (TST-03, MOV-01 a MOV-03, MOV-05, MOV-06, MOV-08 a MOV-12, DAD-16, CLI-09, R8).

A conta da URL envia e paga a tarifa de 1%, arredondada para cima ao
centavo; o destino recebe exatamente o valor. O saldo precisa cobrir
valor + tarifa, e nunca fica negativo. A resposta traz a key da operação
e o saldo novo da origem. Os testes que erram o token começam com
DbUtils.rollback() (PRD-10).
"""

import re
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator


UUID_V4 = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
PARALLEL_REQUESTS = 8


def balance_of(account: dict) -> int:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response
    assert type(response["balance"]) is int, response

    return response["balance"]


def transfer(origin: dict, payload: dict) -> tuple:
    """Transfere a partir da origem, com o token dela."""
    return RequestGenerator.POST_transfer(origin["account_key"], origin["account_token"], payload)


def assert_balances(origin: dict, destination: dict, origin_balance: int, destination_balance: int) -> None:
    assert balance_of(origin) == origin_balance
    assert balance_of(destination) == destination_balance


class TestTransfer:
    def test_transfers_with_fee(self):
        origin = ObjectGenerator.create_funded_account(50000)
        destination = ObjectGenerator.create_account()

        status, response = transfer(origin, PayloadGenerator.transfer(destination["account_key"], amount=10000))

        assert status == 201, response
        assert sorted(response) == ["balance", "transaction_key"]
        assert UUID_V4.match(response["transaction_key"])
        assert type(response["balance"]) is int
        assert response["balance"] == 39900
        assert_balances(origin, destination, 39900, 10000)

    def test_fee_rounds_up_to_the_cent(self):
        origin = ObjectGenerator.create_funded_account(100000)
        destination = ObjectGenerator.create_account()

        status, response = transfer(origin, PayloadGenerator.transfer(destination["account_key"], amount=1234))
        assert status == 201, response
        assert response["balance"] == 100000 - 1234 - 13

        status, response = transfer(origin, PayloadGenerator.transfer(destination["account_key"], amount=1))
        assert status == 201, response
        assert response["balance"] == 100000 - 1234 - 13 - 1 - 1

        assert_balances(origin, destination, 98751, 1235)

    def test_balance_exactly_covers_amount_plus_fee(self):
        origin = ObjectGenerator.create_funded_account(10100)
        destination = ObjectGenerator.create_account()

        status, response = transfer(origin, PayloadGenerator.transfer(destination["account_key"], amount=10000))

        assert status == 201, response
        assert response["balance"] == 0
        assert_balances(origin, destination, 0, 10000)

    def test_refuses_insufficient_balance(self):
        origin = ObjectGenerator.create_funded_account(10099)
        destination = ObjectGenerator.create_account()

        for amount in [10000, 20000]:
            status, response = transfer(origin, PayloadGenerator.transfer(destination["account_key"], amount=amount))

            assert status == 422, (amount, response)
            assert response["code"] == "QIT001015"

        assert_balances(origin, destination, 10099, 0)

    def test_refuses_same_account(self):
        origin = ObjectGenerator.create_funded_account(10000)

        status, response = transfer(origin, PayloadGenerator.transfer(origin["account_key"], amount=1000))

        assert status == 422, response
        assert response["code"] == "QIT001016"
        assert balance_of(origin) == 10000

    def test_unknown_destination_is_404(self):
        origin = ObjectGenerator.create_funded_account(10000)

        status, response = transfer(origin, PayloadGenerator.transfer(str(uuid4()), amount=1000))

        assert status == 404, response
        assert response["code"] == "QIT001017"
        assert balance_of(origin) == 10000

    def test_inactive_origin_is_409(self):
        origin = ObjectGenerator.create_funded_account(10000)
        destination = ObjectGenerator.create_account()

        status, response = RequestGenerator.POST_block(origin["account_key"], PayloadGenerator.block())
        assert status == 204, response

        status, response = transfer(origin, PayloadGenerator.transfer(destination["account_key"], amount=1000))
        assert status == 409, response
        assert response["code"] == "QIT001011"
        assert_balances(origin, destination, 10000, 0)

        status, response = RequestGenerator.POST_unblock(origin["account_key"])
        assert status == 204, response

        status, response = transfer(origin, PayloadGenerator.transfer(destination["account_key"], amount=1000))
        assert status == 201, response

        closed_origin = ObjectGenerator.create_account()
        status, response = RequestGenerator.DELETE_account(closed_origin["account_key"], closed_origin["account_token"])
        assert status == 204, response

        status, response = transfer(closed_origin, PayloadGenerator.transfer(destination["account_key"], amount=1))
        assert status == 409, response
        assert response["code"] == "QIT001011"

    def test_inactive_destination_is_409(self):
        origin = ObjectGenerator.create_funded_account(10000)
        destination = ObjectGenerator.create_account()

        status, response = RequestGenerator.POST_block(destination["account_key"], PayloadGenerator.block())
        assert status == 204, response

        status, response = transfer(origin, PayloadGenerator.transfer(destination["account_key"], amount=1000))
        assert status == 409, response
        assert response["code"] == "QIT001018"
        assert_balances(origin, destination, 10000, 0)

        status, response = RequestGenerator.POST_unblock(destination["account_key"])
        assert status == 204, response

        status, response = transfer(origin, PayloadGenerator.transfer(destination["account_key"], amount=1000))
        assert status == 201, response

        closed_destination = ObjectGenerator.create_account()
        status, response = RequestGenerator.DELETE_account(closed_destination["account_key"], closed_destination["account_token"])
        assert status == 204, response

        status, response = transfer(origin, PayloadGenerator.transfer(closed_destination["account_key"], amount=1000))
        assert status == 409, response
        assert response["code"] == "QIT001018"
        assert balance_of(origin) == 10000 - 1000 - 10

    def test_refuses_body_out_of_schema(self):
        origin = ObjectGenerator.create_funded_account(10000)
        destination = ObjectGenerator.create_account()
        destination_key = destination["account_key"]
        bodies = []

        for amount in [0, -1, 10.5, 1000.0, "1000", True]:
            bodies.append(PayloadGenerator.transfer(destination_key, amount=amount))

        for field in ["destination_account_key", "amount", "request_control_key"]:
            body = PayloadGenerator.transfer(destination_key)
            del body[field]
            bodies.append(body)

        bodies.append(dict(PayloadGenerator.transfer(destination_key), extra=1))
        bodies.append(PayloadGenerator.transfer(destination_key.upper()))
        bodies.append(PayloadGenerator.transfer("nao-e-uma-key"))

        for body in bodies:
            status, response = transfer(origin, body)

            assert status == 400, (body, response)
            assert response["code"] == "QIT000001"

        assert_balances(origin, destination, 10000, 0)

    def test_other_account_token_is_404(self):
        DbUtils.rollback()
        origin = ObjectGenerator.create_funded_account(10000)
        destination = ObjectGenerator.create_account()
        payload = PayloadGenerator.transfer(destination["account_key"], amount=1000)

        status, response = RequestGenerator.POST_transfer(origin["account_key"], destination["account_token"], payload)
        assert status == 404, response
        assert response["code"] == "QIT001010"
        assert_balances(origin, destination, 10000, 0)

        status, response = transfer(origin, payload)
        assert status == 201, response

    def test_missing_or_wrong_token_is_404(self):
        DbUtils.rollback()
        origin = ObjectGenerator.create_funded_account(10000)
        destination = ObjectGenerator.create_account()

        for account_token in [None, "token_errado"]:
            payload = PayloadGenerator.transfer(destination["account_key"], amount=1000)
            status, response = RequestGenerator.POST_transfer(origin["account_key"], account_token, payload)

            assert status == 404, (account_token, response)
            assert response["code"] == "QIT001010"

        assert_balances(origin, destination, 10000, 0)

    def test_repeated_request_returns_first_response(self):
        origin = ObjectGenerator.create_funded_account(10000)
        destination = ObjectGenerator.create_account()
        payload = PayloadGenerator.transfer(destination["account_key"], amount=1000)

        first_status, first_response = transfer(origin, payload)
        assert first_status == 201, first_response
        assert first_response["balance"] == 8990

        status, response = transfer(origin, PayloadGenerator.transfer(destination["account_key"], amount=2000))
        assert status == 201, response

        second_status, second_response = transfer(origin, payload)
        assert second_status == 201, second_response
        assert second_response == first_response

        assert_balances(origin, destination, 10000 - 1010 - 2020, 3000)

        # A repetição simultânea deve passar mesmo quando a primeira esgota o saldo.
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier

        raced = ObjectGenerator.create_funded_account(1010)
        destination = ObjectGenerator.create_account()
        raced_payload = PayloadGenerator.transfer(destination["account_key"], amount=1000)
        gate = Barrier(2)

        def send_same(_index):
            gate.wait(timeout=5)
            return transfer(raced, raced_payload)

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(send_same, range(2)))

        assert results[0][0] == 201, results
        assert results == [results[0], results[0]], results
        assert balance_of(raced) == 0

    def test_same_key_with_other_request_is_409(self):
        origin = ObjectGenerator.create_funded_account(10000)
        destination = ObjectGenerator.create_account()
        other_destination = ObjectGenerator.create_account()
        payload = PayloadGenerator.transfer(destination["account_key"], amount=1000)

        status, response = transfer(origin, payload)
        assert status == 201, response

        for body in [dict(payload, amount=1001), dict(payload, destination_account_key=other_destination["account_key"])]:
            status, response = transfer(origin, body)

            assert status == 409, (body, response)
            assert response["code"] == "QIT001014"

        assert_balances(origin, destination, 8990, 1000)
        assert balance_of(other_destination) == 0

    def test_concurrent_transfers_never_go_negative(self):
        origin = ObjectGenerator.create_funded_account(20200)
        destination = ObjectGenerator.create_account()
        payloads = [PayloadGenerator.transfer(destination["account_key"], amount=10000) for _index in range(PARALLEL_REQUESTS)]

        with ThreadPoolExecutor(max_workers=PARALLEL_REQUESTS) as executor:
            results = list(executor.map(lambda payload: transfer(origin, payload), payloads))

        statuses = sorted(status for status, _response in results)
        assert statuses == [201] * 2 + [422] * (PARALLEL_REQUESTS - 2), results
        assert_balances(origin, destination, 0, 20000)

    def test_crossed_transfers_do_not_deadlock(self):
        first = ObjectGenerator.create_funded_account(100000)
        second = ObjectGenerator.create_funded_account(100000)
        half = PARALLEL_REQUESTS // 2

        requests = []
        for _index in range(half):
            requests.append((first, PayloadGenerator.transfer(second["account_key"], amount=1000)))
            requests.append((second, PayloadGenerator.transfer(first["account_key"], amount=1000)))

        with ThreadPoolExecutor(max_workers=PARALLEL_REQUESTS) as executor:
            results = list(executor.map(lambda request: transfer(request[0], request[1]), requests))

        assert [status for status, _response in results] == [201] * PARALLEL_REQUESTS, results
        assert_balances(first, second, 100000 - half * 10, 100000 - half * 10)
