"""A paga B e B paga A ao mesmo tempo: POST /accounts/{account_key}/transfers (TST-08, MOV-05, MOV-11).

Cada transferência trava as duas contas antes de ler o saldo (MOV-05). Se
cada uma travasse primeiro a própria origem, A esperaria B e B esperaria
A: deadlock, e o PostgreSQL derrubaria uma delas. A API trava sempre na
ordem do id, a menor primeiro (MOV-11): uma espera a outra terminar, e as
duas passam. O mesmo vale para três contas pagando em roda.

Nenhuma conta aplica pontos: a tarifa é 1% (MOV-06) e o sorteio da
chance de não debitar nunca devolve (GAM-10).
"""

from concurrent.futures import ThreadPoolExecutor
from functools import partial
from threading import Barrier

from tests.utils import ObjectGenerator, PayloadGenerator, RequestGenerator


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


class TestCrossedTransfers:
    def test_a_pays_b_and_b_pays_a_at_once(self):
        account_a = ObjectGenerator.create_funded_account(100000)
        account_b = ObjectGenerator.create_funded_account(100000)

        for _ in range(ROUNDS):
            results = run_at_the_same_time([transfer_call(account_a, account_b, 10000), transfer_call(account_b, account_a, 3000)])

            assert [status for status, _ in results] == [201, 201], results

        # MOV-06, MOV-10: a tarifa de 10000 é 100; a de 3000, 30.
        assert balance_of(account_a) == 100000 - ROUNDS * 10100 + ROUNDS * 3000
        assert balance_of(account_b) == 100000 - ROUNDS * 3030 + ROUNDS * 10000
        assert entries_total(account_a) == balance_of(account_a)
        assert entries_total(account_b) == balance_of(account_b)

    def test_three_accounts_pay_in_a_circle_at_once(self):
        account_a = ObjectGenerator.create_funded_account(100000)
        account_b = ObjectGenerator.create_funded_account(100000)
        account_c = ObjectGenerator.create_funded_account(100000)

        for _ in range(ROUNDS):
            results = run_at_the_same_time([transfer_call(account_a, account_b, 1000), transfer_call(account_b, account_c, 2000), transfer_call(account_c, account_a, 4000)])

            assert [status for status, _ in results] == [201, 201, 201], results

        # MOV-06, MOV-10: a tarifa de 1000 é 10; a de 2000, 20; a de 4000, 40.
        assert balance_of(account_a) == 100000 - ROUNDS * 1010 + ROUNDS * 4000
        assert balance_of(account_b) == 100000 - ROUNDS * 2020 + ROUNDS * 1000
        assert balance_of(account_c) == 100000 - ROUNDS * 4040 + ROUNDS * 2000

        for account in [account_a, account_b, account_c]:
            assert entries_total(account) == balance_of(account)
