"""Guardar no cofrinho: POST /accounts/{account_key}/savings (COF-03, COF-10, COF-11, GAM-04, GAM-19, GAM-25, MOV-09, MOV-12, CLI-09, R8).

O dinheiro sai da conta e entra na categoria "economias" do cofrinho, sem
tarifa. O ranque sobe na hora; passar do recorde do cofrinho dá n XP por
real inteiro. Os testes que erram o token começam com DbUtils.rollback()
(PRD-10).
"""

from uuid import uuid4

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator


def balances_of(account: dict) -> tuple:
    """(saldo da conta, saldo do cofrinho)."""
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["balance"], response["piggy_bank_balance"]


def gamification_of(account: dict) -> dict:
    status, response = RequestGenerator.GET_gamification(account["account_key"], account["account_token"])
    assert status == 200, response

    return response


def record_progress_of(account: dict) -> tuple:
    """(nível, XP, recorde do cofrinho)."""
    gamification = gamification_of(account)

    return gamification["level"], gamification["xp"], gamification["piggy_record"]


def save(account: dict, payload: dict) -> tuple:
    return RequestGenerator.POST_saving(account["account_key"], account["account_token"], payload)


def assert_saved(account: dict, amount: int) -> dict:
    status, response = save(account, PayloadGenerator.saving(amount=amount))
    assert status == 201, response

    return response


class TestSave:
    def test_saves_into_default_category(self):
        account = ObjectGenerator.create_funded_account(100000)

        status, response = save(account, PayloadGenerator.saving(amount=30000))

        assert status == 201, response
        assert sorted(response) == ["balance", "piggy_bank_balance", "transaction_key"]
        assert len(response["transaction_key"]) == 36
        assert (response["balance"], response["piggy_bank_balance"]) == (70000, 30000)
        assert type(response["balance"]) is int
        assert type(response["piggy_bank_balance"]) is int
        assert balances_of(account) == (70000, 30000)

    def test_saves_the_whole_balance_and_refuses_more(self):
        account = ObjectGenerator.create_funded_account(1000)
        payload = PayloadGenerator.saving(amount=1001)

        status, response = save(account, payload)
        assert status == 422, response
        assert response["code"] == "QIT001015"
        assert balances_of(account) == (1000, 0)

        payload["amount"] = 1000
        status, response = save(account, payload)
        assert status == 201, response
        assert balances_of(account) == (0, 1000)

        status, response = save(account, PayloadGenerator.saving(amount=1))
        assert status == 422, response
        assert response["code"] == "QIT001015"
        assert balances_of(account) == (0, 1000)

    def test_repeated_request_returns_first_response(self):
        account = ObjectGenerator.create_funded_account(100000)
        payload = PayloadGenerator.saving(amount=30000)

        first_status, first_response = save(account, payload)
        assert first_status == 201, first_response

        status, response = save(account, payload)
        assert (status, response) == (first_status, first_response)
        assert balances_of(account) == (70000, 30000)

        assert_saved(account, 10000)

        status, response = save(account, payload)
        assert (status, response) == (first_status, first_response)
        assert balances_of(account) == (60000, 40000)

        # A repetição simultânea deve passar mesmo quando a primeira esgota o saldo.
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier

        raced = ObjectGenerator.create_funded_account(1000)
        raced_payload = PayloadGenerator.saving(amount=1000)
        gate = Barrier(2)

        def send_same(_index):
            gate.wait(timeout=5)
            return save(raced, raced_payload)

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(send_same, range(2)))

        assert results[0][0] == 201, results
        assert results == [results[0], results[0]], results
        assert balances_of(raced) == (0, 1000)

    def test_same_key_with_other_request_is_409(self):
        account = ObjectGenerator.create_funded_account(100000)
        payload = PayloadGenerator.saving(amount=30000)

        status, response = save(account, payload)
        assert status == 201, response

        other_payload = PayloadGenerator.saving(amount=20000, request_control_key=payload["request_control_key"])
        status, response = save(account, other_payload)
        assert status == 409, response
        assert response["code"] == "QIT001014"

        withdrawal = PayloadGenerator.withdrawal(amount=30000, request_control_key=payload["request_control_key"])
        status, response = RequestGenerator.POST_withdrawal(account["account_key"], account["account_token"], withdrawal)
        assert status == 409, response
        assert response["code"] == "QIT001014"

        assert balances_of(account) == (70000, 30000)

    def test_unknown_category_is_404(self):
        account = ObjectGenerator.create_funded_account(10000)

        status, response = save(account, PayloadGenerator.saving(amount=1000, category_key=str(uuid4())))
        assert status == 404, response
        assert response["code"] == "QIT001021"
        assert balances_of(account) == (10000, 0)

        assert_saved(account, 1000)
        assert balances_of(account) == (9000, 1000)

    def test_blocked_or_closed_account_refuses_saving(self):
        account = ObjectGenerator.create_funded_account(10000)

        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
        assert status == 204, response

        status, response = save(account, PayloadGenerator.saving(amount=1000))
        assert status == 409, response
        assert response["code"] == "QIT001011"
        assert balances_of(account) == (10000, 0)

        status, response = RequestGenerator.POST_unblock(account["account_key"])
        assert status == 204, response

        assert_saved(account, 1000)
        assert balances_of(account) == (9000, 1000)

        closed_account = ObjectGenerator.create_account()
        status, response = RequestGenerator.DELETE_account(closed_account["account_key"], closed_account["account_token"])
        assert status == 204, response

        status, response = save(closed_account, PayloadGenerator.saving(amount=1))
        assert status == 409, response
        assert response["code"] == "QIT001011"

    def test_rank_goes_up_when_saving(self):
        account = ObjectGenerator.create_funded_account(600000)

        assert_saved(account, 199999)
        gamification = gamification_of(account)
        assert (gamification["rank"], gamification["cdi_percent"]) == ("DEFAULT", "100")

        assert_saved(account, 1)
        gamification = gamification_of(account)
        assert (gamification["rank"], gamification["cdi_percent"], gamification["grace_until"]) == ("BRONZE", "102.5", None)

        assert_saved(account, 300000)
        gamification = gamification_of(account)
        assert (gamification["rank"], gamification["cdi_percent"]) == ("SILVER", "105")

        assert balances_of(account) == (100000, 500000)

    def test_saving_gives_record_xp(self):
        account = ObjectGenerator.create_funded_account(20000)
        assert record_progress_of(account) == (0, 0, 0)

        assert_saved(account, 10000)
        assert record_progress_of(account) == (0, 100, 10000)

        assert_saved(account, 50)
        assert record_progress_of(account) == (0, 100, 10050)

        assert_saved(account, 50)
        assert record_progress_of(account) == (0, 101, 10100)

    def test_other_account_token_is_404(self):
        DbUtils.rollback()
        account_a = ObjectGenerator.create_funded_account(10000)
        account_b = ObjectGenerator.create_funded_account(10000)

        status, response = RequestGenerator.POST_saving(account_a["account_key"], account_b["account_token"], PayloadGenerator.saving())
        assert status == 404, response
        assert response["code"] == "QIT001010"

        status, response = RequestGenerator.POST_saving(account_b["account_key"], account_a["account_token"], PayloadGenerator.saving())
        assert status == 404, response
        assert response["code"] == "QIT001010"

        assert balances_of(account_a) == (10000, 0)
        assert balances_of(account_b) == (10000, 0)

        assert_saved(account_a, 1000)

    def test_missing_or_wrong_token_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_funded_account(10000)

        for account_token in [None, "token_errado"]:
            status, response = RequestGenerator.POST_saving(account["account_key"], account_token, PayloadGenerator.saving())
            assert status == 404, (account_token, response)
            assert response["code"] == "QIT001010"

        status, response = RequestGenerator.POST_saving(str(uuid4()), account["account_token"], PayloadGenerator.saving())
        assert status == 404, response
        assert response["code"] == "QIT001010"

        assert balances_of(account) == (10000, 0)
        assert_saved(account, 1000)

    def test_refuses_body_out_of_schema(self):
        account = ObjectGenerator.create_funded_account(10000)
        request_control_key = str(uuid4())
        payloads = [
            {"amount": 0, "request_control_key": request_control_key},
            {"amount": -1, "request_control_key": request_control_key},
            {"amount": 1.5, "request_control_key": request_control_key},
            {"amount": "100", "request_control_key": request_control_key},
            {"request_control_key": request_control_key},
            {"amount": 100},
            {"amount": 100, "request_control_key": "nao-e-uma-key"},
            {"amount": 100, "request_control_key": request_control_key, "category_key": "economias"},
            {"amount": 100, "request_control_key": request_control_key, "extra": 1},
        ]

        for payload in payloads:
            status, response = save(account, payload)
            assert status == 400, (payload, response)
            assert response["code"] == "QIT000001"

        assert balances_of(account) == (10000, 0)
