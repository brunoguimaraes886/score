"""Duas transferências ao mesmo tempo quando o saldo cobre só uma: POST /accounts/{account_key}/transfers (TST-08, MOV-01, MOV-02, MOV-05).

As requisições saem juntas de threads que esperam numa barreira. A API
trava a conta de origem antes de ler o saldo (MOV-05): a segunda espera a
primeira gravar, lê o saldo novo e é barrada com 422 QIT001015 (MOV-01).
Sem a trava, as duas leriam o mesmo saldo e as duas passariam.

Nenhuma conta aplica pontos: a tarifa é 1% (MOV-06) e o sorteio da
chance de não debitar nunca devolve (GAM-10).
"""

from concurrent.futures import ThreadPoolExecutor
from functools import partial
from threading import Barrier

from tests.utils import ObjectGenerator, PayloadGenerator, RequestGenerator


# MOV-06, MOV-10: a tarifa de 10000 é 100.
AMOUNT = 10000
FEE = 100

ROUNDS = 5
BARRIER_TIMEOUT_SECONDS = 30


def run_at_the_same_time(calls: list) -> list:
    """Roda cada função de `calls` numa thread e devolve os resultados, na ordem de `calls`.

    As threads esperam juntas na barreira e saem dela ao mesmo tempo: as
    requisições chegam juntas à API, e quem decide a ordem são as travas
    do banco.
    """
    barrier = Barrier(len(calls), timeout=BARRIER_TIMEOUT_SECONDS)

    def wait_and_call(call):
        barrier.wait()

        return call()

    with ThreadPoolExecutor(max_workers=len(calls)) as executor:
        futures = [executor.submit(wait_and_call, call) for call in calls]

        return [future.result() for future in futures]


def balance_of(account: dict) -> int:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["balance"]


def entries_total(account: dict) -> int:
    """A soma do amount de todos os lançamentos do extrato da conta, página por página."""
    total = 0
    page = 0

    while True:
        status, response = RequestGenerator.GET_entries(account["account_key"], account["account_token"], {"limit": "100", "page": str(page)})
        assert status == 200, response

        total += sum(entry["amount"] for entry in response["data"])

        if response["is_last_page"]:
            return total

        page += 1


def transfer_call(origin: dict, destination: dict, amount: int):
    """A chamada de uma transferência com request_control_key nova, pronta para rodar numa thread."""
    payload = PayloadGenerator.transfer(destination["account_key"], amount=amount)

    return partial(RequestGenerator.POST_transfer, origin["account_key"], origin["account_token"], payload)


class TestConcurrentTransfers:
    def test_two_transfers_when_the_balance_covers_one(self):
        for _ in range(ROUNDS):
            origin = ObjectGenerator.create_funded_account(AMOUNT + FEE)
            first_destination = ObjectGenerator.create_account()
            second_destination = ObjectGenerator.create_account()

            results = run_at_the_same_time([transfer_call(origin, first_destination, AMOUNT), transfer_call(origin, second_destination, AMOUNT)])

            assert sorted(status for status, _ in results) == [201, 422], results

            for status, response in results:
                if status == 201:
                    assert response["balance"] == 0, response
                else:
                    assert response["code"] == "QIT001015", response

            assert balance_of(origin) == 0
            assert sorted([balance_of(first_destination), balance_of(second_destination)]) == [0, AMOUNT]
            assert entries_total(origin) == 0

    def test_six_transfers_at_once_when_the_balance_covers_three(self):
        origin = ObjectGenerator.create_funded_account(3 * (AMOUNT + FEE))
        destination = ObjectGenerator.create_account()

        results = run_at_the_same_time([transfer_call(origin, destination, AMOUNT) for _ in range(6)])

        assert sorted(status for status, _ in results) == [201, 201, 201, 422, 422, 422], results
        assert sorted(response["balance"] for status, response in results if status == 201) == [0, AMOUNT + FEE, 2 * (AMOUNT + FEE)]
        assert [response["code"] for status, response in results if status == 422] == ["QIT001015", "QIT001015", "QIT001015"]

        assert balance_of(origin) == 0
        assert balance_of(destination) == 3 * AMOUNT
        assert entries_total(origin) == 0
        assert entries_total(destination) == 3 * AMOUNT
