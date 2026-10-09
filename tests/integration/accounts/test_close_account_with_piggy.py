"""Encerrar só com o cofrinho zerado: DELETE /accounts/{account_key} (CLI-06, CLI-05, CLI-09).

Conta ACTIVE com saldo zero e dinheiro no cofrinho não encerra (409
QIT001012). Depois de resgatar, sacar e encerrar, a conta não guarda nem
resgata (409 QIT001011).
"""

from tests.utils import ObjectGenerator, PayloadGenerator, RequestGenerator


def balances_of(account: dict) -> tuple:
    """(estado, saldo da conta, saldo do cofrinho)."""
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response
    return response["status"], response["balance"], response["piggy_bank_balance"]


def close(account: dict) -> tuple:
    return RequestGenerator.DELETE_account(account["account_key"], account["account_token"])


def save(account: dict, amount: int) -> tuple:
    return RequestGenerator.POST_saving(account["account_key"], account["account_token"], PayloadGenerator.saving(amount=amount))


def redeem(account: dict, amount: int) -> tuple:
    return RequestGenerator.POST_redemption(account["account_key"], account["account_token"], PayloadGenerator.redemption(amount=amount))


class TestCloseAccountWithPiggy:
    def test_refuses_closing_with_money_in_the_piggy_bank(self):
        account = ObjectGenerator.create_funded_account(1000)
        status, response = save(account, 1000)
        assert status == 201, response
        assert balances_of(account) == ("ACTIVE", 0, 1000)
        status, response = close(account)
        assert status == 409, response
        assert response["code"] == "QIT001012"
        assert balances_of(account) == ("ACTIVE", 0, 1000)

    def test_closes_after_the_piggy_bank_reaches_zero(self):
        account = ObjectGenerator.create_funded_account(1000)
        status, response = save(account, 400)
        assert status == 201, response
        status, response = close(account)
        assert status == 409, response
        assert response["code"] == "QIT001012"
        status, response = redeem(account, 400)
        assert status == 201, response
        status, response = close(account)
        assert status == 409, response
        assert response["code"] == "QIT001012"
        status, response = RequestGenerator.POST_withdrawal(account["account_key"], account["account_token"], PayloadGenerator.withdrawal(amount=1000))
        assert status == 201, response
        status, response = close(account)
        assert status == 204, response
        assert balances_of(account) == ("CLOSED", 0, 0)
        status, response = save(account, 1)
        assert status == 409, response
        assert response["code"] == "QIT001011"
        status, response = redeem(account, 1)
        assert status == 409, response
        assert response["code"] == "QIT001011"
