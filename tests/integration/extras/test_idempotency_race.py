"""A mesma request_control_key duas vezes ao mesmo tempo (TST-08, MOV-12, MOV-19).

As duas requisições saem juntas. As duas podem passar pela procura da
chave antes de qualquer uma gravar. Depois da trava, a segunda reconsulta
a chave antes de conferir estado ou saldo. O UNIQUE e o tratamento de
IntegrityError continuam protegendo colisões que cheguem à gravação; a
barreira HTTP não garante que esse caminho específico seja percorrido.

Mesmo pedido: uma operação só e as duas respostas iguais. A mesma chave
com outro corpo: uma passa e a outra recebe 409 QIT001014 (MOV-12). Vale
para as cinco operações com chave: depósito, saque, transferência,
guardar e resgatar.

Nenhuma conta aplica pontos: a tarifa é 1% (MOV-06) e o sorteio da
chance de não debitar nunca devolve (GAM-10).
"""

from concurrent.futures import ThreadPoolExecutor
from functools import partial
from threading import Barrier
from uuid import uuid4

from tests.utils import DbUtils, MockGenerator, ObjectGenerator, PayloadGenerator, RequestGenerator


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


def balances_of(account: dict) -> tuple:
    """(saldo da conta, saldo do cofrinho)."""
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["balance"], response["piggy_bank_balance"]


def all_entries(account: dict) -> list:
    """Todos os lançamentos do extrato da conta principal, página por página."""
    entries = []
    page = 0

    while True:
        status, response = RequestGenerator.GET_entries(account["account_key"], account["account_token"], {"limit": "100", "page": str(page)})
        assert status == 200, response

        entries.extend(response["data"])

        if response["is_last_page"]:
            return entries

        page += 1


def operation_count(account: dict, transaction_type: str) -> int:
    """Quantas operações do tipo têm lançamento no extrato da conta principal."""
    return len({entry["transaction_key"] for entry in all_entries(account) if entry["transaction_type"] == transaction_type})


def same_request_twice_at_once(call) -> tuple:
    """Manda o mesmo pedido duas vezes ao mesmo tempo; confere que as duas respostas são 201 e iguais, e devolve a resposta."""
    (first_status, first), (second_status, second) = run_at_the_same_time([call, call])

    assert (first_status, second_status) == (201, 201), (first, second)
    assert first == second

    return first


class TestIdempotencyRace:
    def test_same_transfer_twice_at_once_moves_money_once(self):
        for _ in range(ROUNDS):
            origin = ObjectGenerator.create_funded_account(10100)
            destination = ObjectGenerator.create_account()
            payload = PayloadGenerator.transfer(destination["account_key"], amount=10000)
            response = same_request_twice_at_once(partial(RequestGenerator.POST_transfer, origin["account_key"], origin["account_token"], payload))

            assert response["balance"] == 0
            assert balances_of(origin) == (0, 0)
            assert balances_of(destination) == (10000, 0)
            assert operation_count(origin, "TRANSFER") == 1
            assert operation_count(destination, "TRANSFER") == 1
            for account in [origin, destination]:
                status, gamification = RequestGenerator.GET_gamification(account["account_key"], account["account_token"])
                assert status == 200, gamification
                assert gamification["xp"] == 25

    def test_same_key_with_another_body_at_once_is_409(self):
        for operation, transaction_type in [("deposit", "DEPOSIT"), ("withdrawal", "WITHDRAWAL"),
                                            ("transfer", "TRANSFER"), ("saving", "SAVE"), ("redemption", "REDEEM")]:
            for _ in range(ROUNDS):
                account = ObjectGenerator.create_funded_account(9000)
                destination = ObjectGenerator.create_account()
                key, token = account["account_key"], account["account_token"]
                if operation == "redemption":
                    assert RequestGenerator.POST_saving(key, token, PayloadGenerator.saving(amount=9000))[0] == 201
                control_key = str(uuid4())
                payloads = []
                for amount in [1000, 2000]:
                    kwargs = {"amount": amount, "request_control_key": control_key}
                    if operation == "transfer":
                        kwargs["destination_account_key"] = destination["account_key"]
                    payloads.append(getattr(PayloadGenerator, operation)(**kwargs))
                method = getattr(RequestGenerator, "POST_" + operation)
                args = [key] if operation == "deposit" else [key, token]
                count_before = operation_count(account, transaction_type)
                results = run_at_the_same_time([partial(method, *args, payload) for payload in payloads])
                assert sorted(status for status, _ in results) == [201, 409], results
                winner_index = next(i for i, (status, _) in enumerate(results) if status == 201)
                winner = results[winner_index][1]
                loser = results[1 - winner_index][1]
                amount = payloads[winner_index]["amount"]
                assert loser["code"] == "QIT001014", loser
                expected = {"deposit": (9000 + amount, 0), "withdrawal": (9000 - amount, 0),
                            "transfer": (9000 - amount - amount // 100, 0),
                            "saving": (9000 - amount, amount), "redemption": (amount, 9000 - amount)}[operation]
                assert balances_of(account) == expected
                if operation == "deposit":
                    assert set(winner) == {"transaction_key"}
                else:
                    assert winner["balance"] == expected[0]
                assert operation_count(account, transaction_type) == count_before + 1
                if operation == "transfer":
                    assert balances_of(destination) == (amount, 0)
                    assert operation_count(destination, "TRANSFER") == 1

    def test_same_deposit_twice_at_once_credits_once(self):
        account = ObjectGenerator.create_account()

        for round_number in range(1, ROUNDS + 1):
            payload = PayloadGenerator.deposit(amount=5000)
            same_request_twice_at_once(partial(RequestGenerator.POST_deposit, account["account_key"], payload))

            assert balances_of(account) == (round_number * 5000, 0)

        assert operation_count(account, "DEPOSIT") == ROUNDS

    def test_same_withdrawal_twice_at_once_debits_once(self):
        for _ in range(ROUNDS):
            account = ObjectGenerator.create_funded_account(7000)
            payload = PayloadGenerator.withdrawal(amount=7000)
            response = same_request_twice_at_once(partial(RequestGenerator.POST_withdrawal, account["account_key"], account["account_token"], payload))
            assert response["balance"] == 0
            assert balances_of(account) == (0, 0)
            assert operation_count(account, "WITHDRAWAL") == 1

    def test_same_saving_twice_at_once_saves_once(self):
        for _ in range(ROUNDS):
            account = ObjectGenerator.create_funded_account(6000)
            payload = PayloadGenerator.saving(amount=6000)
            response = same_request_twice_at_once(partial(RequestGenerator.POST_saving, account["account_key"], account["account_token"], payload))
            assert (response["balance"], response["piggy_bank_balance"]) == (0, 6000)
            assert balances_of(account) == (0, 6000)
            assert operation_count(account, "SAVE") == 1

    def test_same_redemption_twice_at_once_redeems_once(self):
        for _ in range(ROUNDS):
            account = ObjectGenerator.create_funded_account(4000)
            status, response = RequestGenerator.POST_saving(account["account_key"], account["account_token"], PayloadGenerator.saving(amount=4000))
            assert status == 201, response
            payload = PayloadGenerator.redemption(amount=4000)
            response = same_request_twice_at_once(partial(RequestGenerator.POST_redemption, account["account_key"], account["account_token"], payload))
            assert (response["balance"], response["piggy_bank_balance"]) == (4000, 0)
            assert balances_of(account) == (4000, 0)
            assert operation_count(account, "REDEEM") == 1

    def test_zero_net_taxed_redemption_repeats_original_balance(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate("2026-06-01", "1.000000")
        account = ObjectGenerator.create_funded_account(100000)
        key, token = account["account_key"], account["account_token"]
        assert RequestGenerator.POST_saving(key, token, PayloadGenerator.saving(amount=100000))[0] == 201
        assert RequestGenerator.POST_day_closing(PayloadGenerator.day_closing("2026-06-01"))[0] == 200
        payload = PayloadGenerator.redemption(amount=1)
        response = same_request_twice_at_once(partial(RequestGenerator.POST_redemption, key, token, payload))
        assert (response["iof"], response["ir"], response["net_amount"], response["balance"]) == (1, 0, 0, 0)
        assert balances_of(account) == (0, 100999)
        assert RequestGenerator.POST_deposit(key, PayloadGenerator.deposit(amount=7))[0] == 201
        assert RequestGenerator.POST_redemption(key, token, payload) == (201, response)
        assert balances_of(account) == (7, 100999)
        status, page = RequestGenerator.GET_piggy_bank_entries(key, token, {"limit": "100"})
        assert status == 200, page
        assert len([e for e in page["data"] if e["transaction_type"] == "REDEEM"]) == 1
        MockGenerator.clear_cdi("2026-06-01")
