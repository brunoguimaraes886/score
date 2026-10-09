"""Limite diário e bloqueio automático (CLI-08, DAD-13): POST /accounts/{account_key}/transfers.

Até 10 transferências enviadas no mesmo dia contábil passam. A 11ª, que
passaria em todas as outras regras, é recusada com 422 QIT001019 e
bloqueia a conta na mesma requisição; a 12ª já encontra a conta
bloqueada (409 QIT001011). Só o banco desbloqueia (rota interna), e a
contagem recomeça no desbloqueio. Transferência recebida e pedido
recusado não contam.

Todos os testes começam com DbUtils.rollback(): o limite conta pelo dia
do relógio do banco, que é um só para a suíte inteira (DIA-01).
"""

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator


DAILY_TRANSFER_LIMIT = 10


def account_of(account: dict) -> dict:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response

    return response


def transfer(origin: dict, destination: dict, amount: int = 100) -> tuple:
    payload = PayloadGenerator.transfer(destination["account_key"], amount=amount)

    return RequestGenerator.POST_transfer(origin["account_key"], origin["account_token"], payload)


def send_transfers(origin: dict, destination: dict, count: int, amount: int = 100) -> None:
    for index in range(count):
        status, response = transfer(origin, destination, amount=amount)
        assert status == 201, (index, response)


def assert_limit_reached(status: int, response: dict) -> None:
    assert status == 422, response
    assert response["code"] == "QIT001019"


class TestDailyTransferLimit:
    def test_eleventh_transfer_is_refused_and_blocks_the_account(self):
        DbUtils.rollback()
        origin = ObjectGenerator.create_funded_account(100000)
        destination = ObjectGenerator.create_account()

        send_transfers(origin, destination, DAILY_TRANSFER_LIMIT)
        assert account_of(origin)["status"] == "ACTIVE"

        status, response = transfer(origin, destination)
        assert_limit_reached(status, response)

        origin_account = account_of(origin)
        assert origin_account["status"] == "BLOCKED"
        assert origin_account["balance"] == 100000 - DAILY_TRANSFER_LIMIT * 101
        assert account_of(destination)["balance"] == DAILY_TRANSFER_LIMIT * 100

        status, response = transfer(origin, destination)
        assert status == 409, response
        assert response["code"] == "QIT001011"

    def test_unblock_restarts_the_count(self):
        DbUtils.rollback()
        origin = ObjectGenerator.create_funded_account(100000)
        destination = ObjectGenerator.create_account()

        send_transfers(origin, destination, DAILY_TRANSFER_LIMIT)
        status, response = transfer(origin, destination)
        assert_limit_reached(status, response)

        status, response = RequestGenerator.POST_unblock(origin["account_key"])
        assert status == 204, response

        send_transfers(origin, destination, DAILY_TRANSFER_LIMIT)
        assert account_of(origin)["status"] == "ACTIVE"

        status, response = transfer(origin, destination)
        assert_limit_reached(status, response)
        assert account_of(origin)["status"] == "BLOCKED"

    def test_refused_transfers_do_not_count(self):
        DbUtils.rollback()
        origin = ObjectGenerator.create_funded_account(DAILY_TRANSFER_LIMIT * 101 + 101)
        destination = ObjectGenerator.create_account()

        for _index in range(DAILY_TRANSFER_LIMIT + 1):
            status, response = transfer(origin, destination, amount=1000000)
            assert status == 422, response
            assert response["code"] == "QIT001015"

        send_transfers(origin, destination, DAILY_TRANSFER_LIMIT)
        assert account_of(origin)["status"] == "ACTIVE"

        status, response = transfer(origin, destination)
        assert_limit_reached(status, response)

        origin_account = account_of(origin)
        assert origin_account["status"] == "BLOCKED"
        assert origin_account["balance"] == 101

    def test_eleventh_without_balance_is_insufficient_balance(self):
        DbUtils.rollback()
        origin = ObjectGenerator.create_funded_account(DAILY_TRANSFER_LIMIT * 101 + 101)
        destination = ObjectGenerator.create_account()

        send_transfers(origin, destination, DAILY_TRANSFER_LIMIT)

        status, response = transfer(origin, destination, amount=1000)
        assert status == 422, response
        assert response["code"] == "QIT001015"
        assert account_of(origin)["status"] == "ACTIVE"

        status, response = transfer(origin, destination)
        assert_limit_reached(status, response)

        origin_account = account_of(origin)
        assert origin_account["status"] == "BLOCKED"
        assert origin_account["balance"] == 101

    def test_received_transfers_do_not_count(self):
        DbUtils.rollback()
        first_sender = ObjectGenerator.create_funded_account(100000)
        second_sender = ObjectGenerator.create_funded_account(100000)
        receiver = ObjectGenerator.create_account()

        send_transfers(first_sender, receiver, 6, amount=1000)
        send_transfers(second_sender, receiver, 5, amount=1000)

        send_transfers(receiver, first_sender, DAILY_TRANSFER_LIMIT)
        assert account_of(receiver)["status"] == "ACTIVE"

        status, response = transfer(receiver, first_sender)
        assert_limit_reached(status, response)
        assert account_of(receiver)["status"] == "BLOCKED"
