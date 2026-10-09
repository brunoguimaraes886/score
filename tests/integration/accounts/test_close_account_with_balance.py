"""Encerrar só com saldo zero: DELETE /accounts/{account_key} (CLI-06, CLI-05, CLI-09).

Conta ACTIVE com saldo diferente de zero não encerra (409 QIT001012);
o estado vem antes do saldo: bloqueada responde 409 QIT001011. Depois de
zerar e encerrar, a conta não envia nem recebe dinheiro. O cofrinho
zerado entra no passo 7.15.
"""

from tests.utils import ObjectGenerator, PayloadGenerator, RequestGenerator


def account_of(account: dict) -> dict:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response

    return response


def close(account: dict) -> tuple:
    return RequestGenerator.DELETE_account(account["account_key"], account["account_token"])


class TestCloseAccountWithBalance:
    def test_refuses_closing_with_balance(self):
        account = ObjectGenerator.create_funded_account(100)

        status, response = close(account)
        assert status == 409, response
        assert response["code"] == "QIT001012"
        assert (account_of(account)["status"], account_of(account)["balance"]) == ("ACTIVE", 100)

        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
        assert status == 204, response

        status, response = close(account)
        assert status == 409, response
        assert response["code"] == "QIT001011"

        status, response = RequestGenerator.POST_unblock(account["account_key"])
        assert status == 204, response
        assert account_of(account)["status"] == "ACTIVE"

    def test_closes_after_the_balance_reaches_zero(self):
        account = ObjectGenerator.create_funded_account(5000)
        sender = ObjectGenerator.create_funded_account(10000)

        status, response = close(account)
        assert status == 409, response
        assert response["code"] == "QIT001012"

        status, response = RequestGenerator.POST_withdrawal(account["account_key"], account["account_token"], PayloadGenerator.withdrawal(amount=5000))
        assert status == 201, response

        status, response = close(account)
        assert status == 204, response
        assert (account_of(account)["status"], account_of(account)["balance"]) == ("CLOSED", 0)

        status, response = RequestGenerator.POST_deposit(account["account_key"], PayloadGenerator.deposit(amount=100))
        assert status == 409, response
        assert response["code"] == "QIT001011"

        payload = PayloadGenerator.transfer(account["account_key"], amount=100)
        status, response = RequestGenerator.POST_transfer(sender["account_key"], sender["account_token"], payload)
        assert status == 409, response
        assert response["code"] == "QIT001018"

        assert account_of(account)["balance"] == 0
        assert account_of(sender)["balance"] == 10000
