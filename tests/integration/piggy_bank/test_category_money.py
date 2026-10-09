"""Guardar e resgatar por categoria: POST .../savings e .../redemptions com category_key (COF-03, COF-04, COF-06, COF-07, COF-12, COF-19, API-15, R8).

Cada categoria tem os seus lotes: o resgate sai só da categoria
escolhida, do lote mais antigo dela, mesmo que o cofrinho todo tenha mais
dinheiro. Não existe mover dinheiro entre categorias. Categoria excluída
não guarda nem resgata (409); categoria de outro cofrinho responde como se
não existisse (404). Categoria com dinheiro não é excluída; zerada, pode
ser.
"""

from datetime import date, timedelta
from uuid import uuid4

from tests.utils import DbUtils, MockGenerator, ObjectGenerator, PayloadGenerator, RequestGenerator


ONE_PERCENT = "1.000000"
FIRST_DAY = date(2026, 6, 1)


def day(offset: int) -> str:
    """2026-06-01 + offset dias, em texto: o relógio começa em 2026-06-01 depois do DbUtils.rollback() (DIA-04)."""
    return (FIRST_DAY + timedelta(days=offset)).isoformat()


def create_category(account: dict, name: str) -> str:
    status, response = RequestGenerator.POST_category(account["account_key"], account["account_token"], PayloadGenerator.category(name=name))
    assert status == 201, response

    return response["category_key"]


def save(account: dict, amount: int, category_key: str = None) -> tuple:
    payload = PayloadGenerator.saving(amount=amount, category_key=category_key)

    return RequestGenerator.POST_saving(account["account_key"], account["account_token"], payload)


def redeem(account: dict, amount: int, category_key: str = None) -> tuple:
    payload = PayloadGenerator.redemption(amount=amount, category_key=category_key)

    return RequestGenerator.POST_redemption(account["account_key"], account["account_token"], payload)


def category_balances(account: dict) -> list:
    """(nome, saldo) das categorias ativas, na ordem em que foram criadas."""
    status, response = RequestGenerator.GET_categories(account["account_key"], account["account_token"])
    assert status == 200, response

    return [(category["name"], category["balance"]) for category in response["data"]]


def balances_of(account: dict) -> tuple:
    """(saldo da conta, saldo do cofrinho)."""
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["balance"], response["piggy_bank_balance"]


class TestCategoryMoney:
    def test_saves_and_redeems_in_a_created_category(self):
        account = ObjectGenerator.create_funded_account(100000)
        carro = create_category(account, "carro")

        status, response = save(account, 30000, carro)
        assert status == 201, response
        assert (response["balance"], response["piggy_bank_balance"]) == (70000, 30000)
        assert category_balances(account) == [("economias", 0), ("carro", 30000)]

        status, response = redeem(account, 30000, carro)
        assert status == 201, response
        assert (response["gross_amount"], response["net_amount"]) == (30000, 30000)
        assert balances_of(account) == (100000, 0)

        assert category_balances(account) == [("economias", 0), ("carro", 0)]

        status, response = RequestGenerator.GET_piggy_bank_entries(account["account_key"], account["account_token"], {"category_key": carro})
        assert status == 200, response
        assert [(entry["transaction_type"], entry["amount"], entry["category"]["name"]) for entry in response["data"]] == [
            ("REDEEM", -30000, "carro"),
            ("SAVE", 30000, "carro"),
        ]

    def test_redemption_comes_only_from_the_chosen_category(self):
        account = ObjectGenerator.create_funded_account(100000)
        carro = create_category(account, "carro")

        status, response = save(account, 30000)
        assert status == 201, response
        status, response = save(account, 10000, carro)
        assert status == 201, response

        status, response = redeem(account, 10001, carro)
        assert status == 422, response
        assert response["code"] == "QIT001023"
        assert category_balances(account) == [("economias", 30000), ("carro", 10000)]

        status, response = redeem(account, 10000, carro)
        assert status == 201, response
        assert category_balances(account) == [("economias", 30000), ("carro", 0)]
        assert balances_of(account) == (70000, 30000)

    def test_each_category_has_its_own_lots_and_taxes(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0), ONE_PERCENT)
        account = ObjectGenerator.create_funded_account(40000)
        carro = create_category(account, "carro")

        status, response = save(account, 30000)
        assert status == 201, response
        status, response = save(account, 10000, carro)
        assert status == 201, response

        status, response = RequestGenerator.POST_day_closing(PayloadGenerator.day_closing(day(0)))
        assert status == 200, response
        assert category_balances(account) == [("economias", 30300), ("carro", 10100)]

        status, response = redeem(account, 10100, carro)
        assert status == 201, response
        assert (response["gross_amount"], response["iof"], response["ir"], response["net_amount"]) == (10100, 96, 1, 10003)
        assert category_balances(account) == [("economias", 30300), ("carro", 0)]
        assert balances_of(account) == (10003, 30300)
        MockGenerator.clear_cdi(day(0))

    def test_deleted_category_refuses_saving_and_redemption(self):
        account = ObjectGenerator.create_funded_account(10000)
        carro = create_category(account, "carro")

        status, response = save(account, 1000, carro)
        assert status == 201, response
        status, response = redeem(account, 1000, carro)
        assert status == 201, response

        status, response = RequestGenerator.DELETE_category(account["account_key"], account["account_token"], carro)
        assert status == 204, response

        for send in [save, redeem]:
            status, response = send(account, 1000, carro)
            assert status == 409, response
            assert response["code"] == "QIT001022"

        status, response = RequestGenerator.GET_piggy_bank_entries(account["account_key"], account["account_token"], {"category_key": carro})
        assert status == 200, response
        assert len(response["data"]) == 2
        assert balances_of(account) == (10000, 0)

    def test_category_of_another_piggy_bank_is_404(self):
        account = ObjectGenerator.create_funded_account(10000)
        other_account = ObjectGenerator.create_account()
        own_key = create_category(account, "carro")
        other_key = create_category(other_account, "carro")

        status, response = save(account, 1000, own_key)
        assert status == 201, response

        for category_key in [other_key, str(uuid4())]:
            for send in [save, redeem]:
                status, response = send(account, 1000, category_key)
                assert status == 404, (category_key, response)
                assert response["code"] == "QIT001021"

            status, response = RequestGenerator.GET_piggy_bank_entries(account["account_key"], account["account_token"], {"category_key": category_key})
            assert status == 404, response
            assert response["code"] == "QIT001021"

        assert balances_of(account) == (9000, 1000)
        assert category_balances(other_account) == [("economias", 0), ("carro", 0)]

    def test_category_with_money_cannot_be_deleted(self):
        account = ObjectGenerator.create_funded_account(10000)
        carro = create_category(account, "carro")

        status, response = save(account, 1000, carro)
        assert status == 201, response

        status, response = RequestGenerator.DELETE_category(account["account_key"], account["account_token"], carro)
        assert status == 409, response
        assert response["code"] == "QIT001026"
        assert category_balances(account) == [("economias", 0), ("carro", 1000)]

        status, response = redeem(account, 1000, carro)
        assert status == 201, response

        status, response = RequestGenerator.DELETE_category(account["account_key"], account["account_token"], carro)
        assert status == 204, response
        assert category_balances(account) == [("economias", 0)]
