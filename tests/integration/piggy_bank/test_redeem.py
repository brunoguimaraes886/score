"""Resgatar do cofrinho: POST /accounts/{account_key}/redemptions (COF-06, COF-07, COF-08, COF-10, COF-24, GAM-04, GAM-19, MOV-12, CLI-09, R8).

O dinheiro sai da categoria "economias" (do lote mais antigo) e volta para
a conta. A resposta mostra o bruto e o líquido; o IOF e o IR são 0 até o
passo 9.2. Resgate maior que a categoria → 422 QIT001023. O ranque não cai
e o recorde não muda. Os testes que erram o token começam com
DbUtils.rollback() (PRD-10).
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


def assert_saved(account: dict, amount: int) -> None:
    status, response = RequestGenerator.POST_saving(account["account_key"], account["account_token"], PayloadGenerator.saving(amount=amount))
    assert status == 201, response


def redeem(account: dict, payload: dict) -> tuple:
    return RequestGenerator.POST_redemption(account["account_key"], account["account_token"], payload)


def assert_redeemed(account: dict, amount: int) -> dict:
    status, response = redeem(account, PayloadGenerator.redemption(amount=amount))
    assert status == 201, response

    return response


class TestRedeem:
    def test_redeems_into_account(self):
        account = ObjectGenerator.create_funded_account(100000)
        assert_saved(account, 30000)

        status, response = redeem(account, PayloadGenerator.redemption(amount=10000))

        assert status == 201, response
        assert len(response["transaction_key"]) == 36
        assert response == {
            "transaction_key": response["transaction_key"],
            "balance": 80000,
            "piggy_bank_balance": 20000,
            "gross_amount": 10000,
            "iof": 0,
            "ir": 0,
            "net_amount": 10000,
        }
        for field in ["balance", "piggy_bank_balance", "gross_amount", "iof", "ir", "net_amount"]:
            assert type(response[field]) is int, field

        assert balances_of(account) == (80000, 20000)

    def test_refuses_more_than_category_balance(self):
        account = ObjectGenerator.create_funded_account(100000)
        assert_saved(account, 20000)

        status, response = redeem(account, PayloadGenerator.redemption(amount=20001))
        assert status == 422, response
        assert response["code"] == "QIT001023"
        assert balances_of(account) == (80000, 20000)

        assert_redeemed(account, 20000)
        assert balances_of(account) == (100000, 0)

    def test_refuses_redemption_from_empty_piggy_bank(self):
        account = ObjectGenerator.create_funded_account(100000)

        status, response = redeem(account, PayloadGenerator.redemption(amount=1))
        assert status == 422, response
        assert response["code"] == "QIT001023"
        assert balances_of(account) == (100000, 0)

    def test_saving_again_after_redeeming_gives_no_xp(self):
        account = ObjectGenerator.create_funded_account(20000)

        assert_saved(account, 10000)
        assert record_progress_of(account) == (0, 100, 10000)

        assert_redeemed(account, 10000)
        assert record_progress_of(account) == (0, 100, 10000)

        assert_saved(account, 10000)
        assert record_progress_of(account) == (0, 100, 10000)

        assert_saved(account, 100)
        assert record_progress_of(account) == (0, 101, 10100)

    def test_rank_does_not_fall_when_redeeming(self):
        account = ObjectGenerator.create_funded_account(300000)
        assert_saved(account, 200000)
        assert gamification_of(account)["rank"] == "BRONZE"

        assert_redeemed(account, 1000)

        gamification = gamification_of(account)
        assert (gamification["rank"], gamification["grace_until"]) == ("BRONZE", None)
        assert balances_of(account) == (101000, 199000)

    def test_repeated_request_returns_first_response(self):
        account = ObjectGenerator.create_funded_account(100000)
        assert_saved(account, 50000)
        payload = PayloadGenerator.redemption(amount=10000)

        first_status, first_response = redeem(account, payload)
        assert first_status == 201, first_response

        status, response = redeem(account, payload)
        assert (status, response) == (first_status, first_response)
        assert balances_of(account) == (60000, 40000)

        assert_redeemed(account, 5000)

        status, response = redeem(account, payload)
        assert (status, response) == (first_status, first_response)
        assert balances_of(account) == (65000, 35000)

        # A repetição simultânea deve passar mesmo quando a primeira esgota o saldo.
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier

        raced = ObjectGenerator.create_funded_account(1000)
        assert_saved(raced, 1000)
        raced_payload = PayloadGenerator.redemption(amount=1000)
        gate = Barrier(2)

        def send_same(_index):
            gate.wait(timeout=5)
            return redeem(raced, raced_payload)

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(send_same, range(2)))

        assert results[0][0] == 201, results
        assert results == [results[0], results[0]], results
        assert balances_of(raced) == (1000, 0)

    def test_same_key_with_other_request_is_409(self):
        account = ObjectGenerator.create_funded_account(100000)
        saving = PayloadGenerator.saving(amount=50000)
        status, response = RequestGenerator.POST_saving(account["account_key"], account["account_token"], saving)
        assert status == 201, response

        status, response = redeem(account, PayloadGenerator.redemption(amount=50000, request_control_key=saving["request_control_key"]))
        assert status == 409, response
        assert response["code"] == "QIT001014"

        payload = PayloadGenerator.redemption(amount=10000)
        status, response = redeem(account, payload)
        assert status == 201, response

        status, response = redeem(account, PayloadGenerator.redemption(amount=20000, request_control_key=payload["request_control_key"]))
        assert status == 409, response
        assert response["code"] == "QIT001014"

        assert balances_of(account) == (60000, 40000)

    def test_unknown_category_is_404(self):
        account = ObjectGenerator.create_funded_account(10000)
        assert_saved(account, 5000)

        status, response = redeem(account, PayloadGenerator.redemption(amount=1000, category_key=str(uuid4())))
        assert status == 404, response
        assert response["code"] == "QIT001021"
        assert balances_of(account) == (5000, 5000)

        assert_redeemed(account, 1000)
        assert balances_of(account) == (6000, 4000)

    def test_blocked_or_closed_account_refuses_redemption(self):
        account = ObjectGenerator.create_funded_account(10000)
        assert_saved(account, 5000)

        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
        assert status == 204, response

        status, response = redeem(account, PayloadGenerator.redemption(amount=1000))
        assert status == 409, response
        assert response["code"] == "QIT001011"
        assert balances_of(account) == (5000, 5000)

        status, response = RequestGenerator.POST_unblock(account["account_key"])
        assert status == 204, response

        assert_redeemed(account, 1000)
        assert balances_of(account) == (6000, 4000)

        closed_account = ObjectGenerator.create_account()
        status, response = RequestGenerator.DELETE_account(closed_account["account_key"], closed_account["account_token"])
        assert status == 204, response

        status, response = redeem(closed_account, PayloadGenerator.redemption(amount=1))
        assert status == 409, response
        assert response["code"] == "QIT001011"

    def test_other_account_token_is_404(self):
        DbUtils.rollback()
        account_a = ObjectGenerator.create_funded_account(10000)
        account_b = ObjectGenerator.create_funded_account(10000)
        assert_saved(account_a, 5000)
        assert_saved(account_b, 5000)

        status, response = RequestGenerator.POST_redemption(account_a["account_key"], account_b["account_token"], PayloadGenerator.redemption())
        assert status == 404, response
        assert response["code"] == "QIT001010"

        status, response = RequestGenerator.POST_redemption(account_b["account_key"], account_a["account_token"], PayloadGenerator.redemption())
        assert status == 404, response
        assert response["code"] == "QIT001010"

        assert balances_of(account_a) == (5000, 5000)
        assert balances_of(account_b) == (5000, 5000)

        assert_redeemed(account_a, 1000)

    def test_missing_or_wrong_token_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_funded_account(10000)
        assert_saved(account, 5000)

        for account_token in [None, "token_errado"]:
            status, response = RequestGenerator.POST_redemption(account["account_key"], account_token, PayloadGenerator.redemption())
            assert status == 404, (account_token, response)
            assert response["code"] == "QIT001010"

        status, response = RequestGenerator.POST_redemption(str(uuid4()), account["account_token"], PayloadGenerator.redemption())
        assert status == 404, response
        assert response["code"] == "QIT001010"

        assert balances_of(account) == (5000, 5000)
        assert_redeemed(account, 1000)

    def test_refuses_body_out_of_schema(self):
        account = ObjectGenerator.create_funded_account(10000)
        assert_saved(account, 5000)
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
            status, response = redeem(account, payload)
            assert status == 400, (payload, response)
            assert response["code"] == "QIT000001"

        assert balances_of(account) == (5000, 5000)
