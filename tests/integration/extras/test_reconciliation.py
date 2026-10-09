"""Reconciliação: em cada conta criada no teste, a soma do extrato é o saldo (TST-08, DAD-07, MOV-19, COF-05).

O saldo mora em dois lugares (DAD-07): na coluna balance da conta, que sai
em GET /accounts/{account_key}, e nos lançamentos, que saem no extrato. O
teste soma o amount de todos os lançamentos, página por página, e compara
com o saldo: o da conta principal com GET .../entries e o do cofrinho com
GET .../piggy_bank_entries. O saldo do cofrinho também é a soma dos saldos
das categorias (COF-05).

Com as operações uma depois da outra, o teste confere também cada linha:
do lançamento mais antigo para o mais novo, o balance_after é a soma
acumulada (MOV-19). Com as operações ao mesmo tempo, confere só o total.

O primeiro teste fecha o dia (rendimento e, no resgate, IOF e IR): começa
com DbUtils.rollback() (o relógio volta a 2026-06-01, DIA-01) e programa
o CDI de 1% no Mockserver.

Nenhuma conta aplica pontos: a tarifa é 1% (MOV-06) e o sorteio da
chance de não debitar nunca devolve (GAM-10).
"""

from concurrent.futures import ThreadPoolExecutor
from functools import partial
from threading import Barrier

from tests.utils import DbUtils, MockGenerator, ObjectGenerator, PayloadGenerator, RandomGenerator, RequestGenerator


FIRST_DAY = "2026-06-01"
ONE_PERCENT = "1.000000"

# MOV-08: não há valor máximo; este valor passa no schema e nenhuma conta do teste tem saldo para ele.
TOO_MUCH = 1000000000

ROUNDS = 3
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


def expect(result: tuple, status: int) -> dict:
    """Confere o status de uma resposta (status, corpo) e devolve o corpo."""
    assert result[0] == status, result

    return result[1]


def balances_of(account: dict) -> tuple:
    """(saldo da conta, saldo do cofrinho)."""
    response = expect(RequestGenerator.GET_account(account["account_key"], account["account_token"]), 200)

    return response["balance"], response["piggy_bank_balance"]


def all_entries(route, account: dict) -> list:
    """Todos os lançamentos de um extrato, do mais recente para o mais antigo, página por página.

    `route` é RequestGenerator.GET_entries (conta principal) ou
    RequestGenerator.GET_piggy_bank_entries (cofrinho).
    """
    entries = []
    page = 0

    while True:
        response = expect(route(account["account_key"], account["account_token"], {"limit": "100", "page": str(page)}), 200)

        entries.extend(response["data"])

        if response["is_last_page"]:
            return entries

        page += 1


def categories_total(account: dict) -> int:
    """A soma dos saldos das categorias ativas do cofrinho."""
    response = expect(RequestGenerator.GET_categories(account["account_key"], account["account_token"], {"limit": "100"}), 200)
    assert response["is_last_page"] is True, response

    return sum(category["balance"] for category in response["data"])


def assert_running_balance(entries: list, balance: int) -> None:
    """Do lançamento mais antigo para o mais novo, o balance_after de cada um é a soma dos amount até ele; a soma final é o saldo (MOV-19)."""
    running = 0

    for entry in reversed(entries):
        running += entry["amount"]
        assert entry["balance_after"] == running, entry

    assert running == balance


def reconcile(account: dict, check_each_line: bool) -> None:
    """A soma do extrato é o saldo, na conta principal e no cofrinho; o cofrinho é a soma das categorias (DAD-07, COF-05)."""
    balance, piggy_bank_balance = balances_of(account)
    entries = all_entries(RequestGenerator.GET_entries, account)
    piggy_bank_entries = all_entries(RequestGenerator.GET_piggy_bank_entries, account)

    assert sum(entry["amount"] for entry in entries) == balance
    assert sum(entry["amount"] for entry in piggy_bank_entries) == piggy_bank_balance
    assert categories_total(account) == piggy_bank_balance

    if check_each_line:
        assert_running_balance(entries, balance)
        assert_running_balance(piggy_bank_entries, piggy_bank_balance)


class TestReconciliation:
    def test_entries_add_up_to_the_balance_after_every_kind_of_operation(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(FIRST_DAY, ONE_PERCENT)

        account_a = ObjectGenerator.create_funded_account(300000)
        account_b = ObjectGenerator.create_funded_account(50000)
        key_a, token_a = account_a["account_key"], account_a["account_token"]
        key_b, token_b = account_b["account_key"], account_b["account_token"]

        expect(RequestGenerator.POST_deposit(key_a, PayloadGenerator.deposit(amount=20000, depositor_document=RandomGenerator.generate_cnpj())), 201)
        expect(RequestGenerator.POST_transfer(key_a, token_a, PayloadGenerator.transfer(key_b, amount=12345)), 201)
        expect(RequestGenerator.POST_transfer(key_b, token_b, PayloadGenerator.transfer(key_a, amount=2000)), 201)

        withdrawal = PayloadGenerator.withdrawal(amount=5000)
        first_withdrawal = expect(RequestGenerator.POST_withdrawal(key_a, token_a, withdrawal), 201)
        assert expect(RequestGenerator.POST_withdrawal(key_a, token_a, withdrawal), 201) == first_withdrawal

        expect(RequestGenerator.POST_saving(key_a, token_a, PayloadGenerator.saving(amount=100000)), 201)
        category_key = expect(RequestGenerator.POST_category(key_a, token_a, PayloadGenerator.category()), 201)["category_key"]
        expect(RequestGenerator.POST_saving(key_a, token_a, PayloadGenerator.saving(amount=30000, category_key=category_key)), 201)

        # MOV-06, MOV-10: a tarifa de 12345 é 124 (123,45 para cima); a de 2000, 20.
        assert balances_of(account_a) == (174531, 130000)
        assert balances_of(account_b) == (60325, 0)

        assert expect(RequestGenerator.POST_transfer(key_a, token_a, PayloadGenerator.transfer(key_b, amount=TOO_MUCH)), 422)["code"] == "QIT001015"
        assert expect(RequestGenerator.POST_withdrawal(key_b, token_b, PayloadGenerator.withdrawal(amount=TOO_MUCH)), 422)["code"] == "QIT001015"
        assert expect(RequestGenerator.POST_redemption(key_a, token_a, PayloadGenerator.redemption(amount=TOO_MUCH, category_key=category_key)), 422)["code"] == "QIT001023"
        assert balances_of(account_a) == (174531, 130000)
        assert balances_of(account_b) == (60325, 0)

        assert expect(RequestGenerator.POST_day_closing(PayloadGenerator.day_closing(FIRST_DAY)), 200)["closed_date"] == FIRST_DAY

        balance, piggy_bank_balance = balances_of(account_a)
        assert balance == 174531
        assert piggy_bank_balance > 130000
        assert "YIELD" in [entry["transaction_type"] for entry in all_entries(RequestGenerator.GET_piggy_bank_entries, account_a)]

        for redemption in [PayloadGenerator.redemption(amount=50000), PayloadGenerator.redemption(amount=10000, category_key=category_key)]:
            response = expect(RequestGenerator.POST_redemption(key_a, token_a, redemption), 201)

            assert response["gross_amount"] == redemption["amount"]
            assert response["net_amount"] == response["gross_amount"] - response["iof"] - response["ir"]
            assert response["balance"] == balance + response["net_amount"]
            assert response["piggy_bank_balance"] == piggy_bank_balance - response["gross_amount"]

            balance, piggy_bank_balance = response["balance"], response["piggy_bank_balance"]

        assert balances_of(account_a) == (balance, piggy_bank_balance)

        reconcile(account_a, check_each_line=True)
        reconcile(account_b, check_each_line=True)
        MockGenerator.clear_cdi(FIRST_DAY)

    def test_entries_add_up_to_the_balance_after_concurrent_operations(self):
        account_a = ObjectGenerator.create_funded_account(100000)
        account_b = ObjectGenerator.create_funded_account(100000)
        account_c = ObjectGenerator.create_funded_account(100000)
        key_a, token_a = account_a["account_key"], account_a["account_token"]
        key_b, token_b = account_b["account_key"], account_b["account_token"]
        key_c, token_c = account_c["account_key"], account_c["account_token"]

        for _ in range(ROUNDS):
            calls = []
            calls.append(partial(RequestGenerator.POST_transfer, key_a, token_a, PayloadGenerator.transfer(key_b, amount=1000)))
            calls.append(partial(RequestGenerator.POST_transfer, key_b, token_b, PayloadGenerator.transfer(key_c, amount=2000)))
            calls.append(partial(RequestGenerator.POST_transfer, key_c, token_c, PayloadGenerator.transfer(key_a, amount=3000)))
            calls.append(partial(RequestGenerator.POST_deposit, key_a, PayloadGenerator.deposit(amount=500)))
            calls.append(partial(RequestGenerator.POST_withdrawal, key_b, token_b, PayloadGenerator.withdrawal(amount=700)))
            calls.append(partial(RequestGenerator.POST_saving, key_c, token_c, PayloadGenerator.saving(amount=400)))

            results = run_at_the_same_time(calls)

            assert [status for status, _ in results] == [201, 201, 201, 201, 201, 201], results

        # MOV-06, MOV-10: a tarifa de 1000 é 10; a de 2000, 20; a de 3000, 30.
        assert balances_of(account_a) == (100000 - ROUNDS * 1010 + ROUNDS * 3000 + ROUNDS * 500, 0)
        assert balances_of(account_b) == (100000 - ROUNDS * 2020 + ROUNDS * 1000 - ROUNDS * 700, 0)
        assert balances_of(account_c) == (100000 - ROUNDS * 3030 + ROUNDS * 2000 - ROUNDS * 400, ROUNDS * 400)

        for account in [account_a, account_b, account_c]:
            reconcile(account, check_each_line=False)
