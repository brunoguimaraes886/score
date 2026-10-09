"""Criar e listar categorias: POST e GET /accounts/{account_key}/categories (COF-03, COF-05, COF-18, CLI-05, CLI-09, MOV-04, API-03, R5, R8).

O cofrinho nasce com a "economias"; o dono cria as suas. O nome não se
repete entre as categorias ativas do mesmo cofrinho. A lista traz só as
ativas, com o saldo de cada uma, na ordem em que foram criadas, no
envelope do extrato. Conta bloqueada cria; encerrada só lê. Os testes que
erram o token começam com DbUtils.rollback() (PRD-10).
"""

from uuid import uuid4

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator


CATEGORY_FIELDS = ["balance", "category_key", "created_at", "is_default", "name", "status"]


def create_category(account: dict, name: str) -> tuple:
    return RequestGenerator.POST_category(account["account_key"], account["account_token"], PayloadGenerator.category(name=name))


def list_categories(account: dict, params: dict = None) -> dict:
    status, response = RequestGenerator.GET_categories(account["account_key"], account["account_token"], params)
    assert status == 200, response

    return response


def names_and_balances(page: dict) -> list:
    return [(category["name"], category["balance"]) for category in page["data"]]


class TestCreateAndListCategories:
    def test_new_account_lists_only_economias(self):
        account = ObjectGenerator.create_account()

        page = list_categories(account)

        assert (page["limit"], page["page"], page["is_last_page"]) == (10, 0, True)
        assert len(page["data"]) == 1

        economias = page["data"][0]
        assert sorted(economias) == CATEGORY_FIELDS
        assert (economias["name"], economias["is_default"], economias["status"], economias["balance"]) == ("economias", True, "ACTIVE", 0)
        assert len(economias["category_key"]) == 36
        assert type(economias["balance"]) is int

    def test_creates_category(self):
        account = ObjectGenerator.create_account()

        status, response = create_category(account, "carro")

        assert status == 201, response
        assert list(response) == ["category_key"]
        assert len(response["category_key"]) == 36

        page = list_categories(account)
        assert names_and_balances(page) == [("economias", 0), ("carro", 0)]

        carro = page["data"][1]
        assert (carro["category_key"], carro["is_default"], carro["status"]) == (response["category_key"], False, "ACTIVE")

    def test_lists_the_balance_of_each_category(self):
        account = ObjectGenerator.create_funded_account(50000)
        status, response = create_category(account, "viagem")
        assert status == 201, response

        status, response = RequestGenerator.POST_saving(account["account_key"], account["account_token"], PayloadGenerator.saving(amount=30000))
        assert status == 201, response

        assert names_and_balances(list_categories(account)) == [("economias", 30000), ("viagem", 0)]

    def test_duplicated_active_name_is_409(self):
        account = ObjectGenerator.create_account()
        other_account = ObjectGenerator.create_account()

        status, response = create_category(account, "carro")
        assert status == 201, response

        for name in ["carro", "economias"]:
            status, response = create_category(account, name)
            assert status == 409, (name, response)
            assert response["code"] == "QIT001024"

        assert names_and_balances(list_categories(account)) == [("economias", 0), ("carro", 0)]

        status, response = create_category(other_account, "carro")
        assert status == 201, response

    def test_blocked_account_creates_and_lists(self):
        account = ObjectGenerator.create_account()

        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
        assert status == 204, response

        status, response = create_category(account, "reserva")
        assert status == 201, response

        assert names_and_balances(list_categories(account)) == [("economias", 0), ("reserva", 0)]

    def test_closed_account_refuses_creating_but_lists(self):
        account = ObjectGenerator.create_account()

        status, response = RequestGenerator.DELETE_account(account["account_key"], account["account_token"])
        assert status == 204, response

        status, response = create_category(account, "carro")
        assert status == 409, response
        assert response["code"] == "QIT001011"

        assert names_and_balances(list_categories(account)) == [("economias", 0)]

    def test_pagination(self):
        account = ObjectGenerator.create_account()
        names = [f"c{number:02d}" for number in range(1, 12)]

        for name in names:
            status, response = create_category(account, name)
            assert status == 201, response

        first = list_categories(account, {"limit": "5", "page": "0"})
        second = list_categories(account, {"limit": "5", "page": "1"})
        third = list_categories(account, {"limit": "5", "page": "2"})

        assert [category["name"] for category in first["data"]] == ["economias"] + names[:4]
        assert [category["name"] for category in second["data"]] == names[4:9]
        assert [category["name"] for category in third["data"]] == names[9:]
        assert (first["is_last_page"], second["is_last_page"], third["is_last_page"]) == (False, False, True)
        assert (third["limit"], third["page"]) == (5, 2)

    def test_refuses_body_and_query_out_of_schema(self):
        account = ObjectGenerator.create_account()

        for payload in [{}, {"name": ""}, {"name": 1}, {"name": "x" * 256}, {"name": "carro", "is_default": True}]:
            status, response = RequestGenerator.POST_category(account["account_key"], account["account_token"], payload)
            assert status == 400, (payload, response)
            assert response["code"] == "QIT000001"

        for params in [{"limit": "0"}, {"limit": "101"}, {"limit": "abc"}, {"page": "-1"}, {"status": "DELETED"}]:
            status, response = RequestGenerator.GET_categories(account["account_key"], account["account_token"], params)
            assert status == 400, (params, response)
            assert response["code"] == "QIT000001"

        assert names_and_balances(list_categories(account)) == [("economias", 0)]

    def test_other_account_token_is_404(self):
        DbUtils.rollback()
        account_a = ObjectGenerator.create_account()
        account_b = ObjectGenerator.create_account()

        status, response = RequestGenerator.POST_category(account_a["account_key"], account_b["account_token"], PayloadGenerator.category(name="carro"))
        assert status == 404, response
        assert response["code"] == "QIT001010"

        status, response = RequestGenerator.GET_categories(account_a["account_key"], account_b["account_token"])
        assert status == 404, response
        assert response["code"] == "QIT001010"

        assert names_and_balances(list_categories(account_a)) == [("economias", 0)]

    def test_missing_or_wrong_token_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()

        for account_token in [None, "token_errado"]:
            status, response = RequestGenerator.GET_categories(account["account_key"], account_token)
            assert status == 404, response
            assert response["code"] == "QIT001010"

        status, response = RequestGenerator.POST_category(str(uuid4()), account["account_token"], PayloadGenerator.category())
        assert status == 404, response
        assert response["code"] == "QIT001010"
