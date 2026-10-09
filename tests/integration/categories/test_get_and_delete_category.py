"""Consultar e excluir categoria: GET e DELETE /accounts/{account_key}/categories/{category_key} (COF-04, COF-18, API-15, CLI-05, CLI-09, R4, R5, R8).

A consulta devolve a categoria ativa ou excluída; a excluída sai com
status DELETED. Excluir só muda o estado e grava o evento: a categoria
some da lista, e o nome pode ser usado de novo. A "economias" nunca é
excluída. Conta bloqueada exclui; encerrada só lê. Os testes que erram o
token começam com DbUtils.rollback() (PRD-10).
"""

from uuid import uuid4

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator


CATEGORY_FIELDS = ["balance", "category_key", "created_at", "is_default", "name", "status"]


def create_category(account: dict, name: str) -> str:
    status, response = RequestGenerator.POST_category(account["account_key"], account["account_token"], PayloadGenerator.category(name=name))
    assert status == 201, response

    return response["category_key"]


def get_category(account: dict, category_key: str) -> tuple:
    return RequestGenerator.GET_category(account["account_key"], account["account_token"], category_key)


def delete_category(account: dict, category_key: str) -> tuple:
    return RequestGenerator.DELETE_category(account["account_key"], account["account_token"], category_key)


def active_names(account: dict) -> list:
    status, response = RequestGenerator.GET_categories(account["account_key"], account["account_token"])
    assert status == 200, response

    return [category["name"] for category in response["data"]]


def default_category_key(account: dict) -> str:
    status, response = RequestGenerator.GET_categories(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["data"][0]["category_key"]


def status_of(account: dict, category_key: str) -> str:
    status, response = get_category(account, category_key)
    assert status == 200, response

    return response["status"]


class TestGetAndDeleteCategory:
    def test_gets_active_category(self):
        account = ObjectGenerator.create_account()
        category_key = create_category(account, "carro")

        status, response = get_category(account, category_key)

        assert status == 200, response
        assert sorted(response) == CATEGORY_FIELDS
        assert (response["category_key"], response["name"], response["is_default"], response["status"], response["balance"]) == (category_key, "carro", False, "ACTIVE", 0)

        status, response = get_category(account, default_category_key(account))
        assert status == 200, response
        assert (response["name"], response["is_default"], response["status"]) == ("economias", True, "ACTIVE")

    def test_deletes_empty_category(self):
        account = ObjectGenerator.create_account()
        category_key = create_category(account, "carro")

        status, response = delete_category(account, category_key)
        assert status == 204, response
        assert response is None

        status, response = get_category(account, category_key)
        assert status == 200, response
        assert (response["name"], response["status"], response["balance"]) == ("carro", "DELETED", 0)
        assert active_names(account) == ["economias"]

        status, response = delete_category(account, category_key)
        assert status == 409, response
        assert response["code"] == "QIT001022"

    def test_name_can_be_used_again_after_delete(self):
        account = ObjectGenerator.create_account()
        old_key = create_category(account, "carro")

        status, response = delete_category(account, old_key)
        assert status == 204, response

        new_key = create_category(account, "carro")

        assert new_key != old_key
        assert active_names(account) == ["economias", "carro"]
        assert status_of(account, old_key) == "DELETED"
        assert status_of(account, new_key) == "ACTIVE"

    def test_default_category_cannot_be_deleted(self):
        account = ObjectGenerator.create_account()
        category_key = default_category_key(account)

        status, response = delete_category(account, category_key)
        assert status == 409, response
        assert response["code"] == "QIT001025"

        assert status_of(account, category_key) == "ACTIVE"
        assert active_names(account) == ["economias"]

    def test_unknown_category_is_404(self):
        account = ObjectGenerator.create_account()
        other_account = ObjectGenerator.create_account()
        other_key = create_category(other_account, "carro")

        for category_key in [str(uuid4()), "nao-e-uma-key", other_key]:
            for send in [get_category, delete_category]:
                status, response = send(account, category_key)
                assert status == 404, (category_key, response)
                assert response["code"] == "QIT001021"

        assert status_of(other_account, other_key) == "ACTIVE"

    def test_blocked_account_deletes(self):
        account = ObjectGenerator.create_account()
        category_key = create_category(account, "reserva")

        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
        assert status == 204, response

        status, response = delete_category(account, category_key)
        assert status == 204, response
        assert status_of(account, category_key) == "DELETED"

    def test_closed_account_refuses_deleting_but_reads(self):
        account = ObjectGenerator.create_account()
        category_key = create_category(account, "carro")

        status, response = RequestGenerator.DELETE_account(account["account_key"], account["account_token"])
        assert status == 204, response

        status, response = delete_category(account, category_key)
        assert status == 409, response
        assert response["code"] == "QIT001011"

        assert status_of(account, category_key) == "ACTIVE"

    def test_other_account_token_is_404(self):
        DbUtils.rollback()
        account_a = ObjectGenerator.create_account()
        account_b = ObjectGenerator.create_account()
        category_key = create_category(account_a, "carro")

        for send in [RequestGenerator.GET_category, RequestGenerator.DELETE_category]:
            status, response = send(account_a["account_key"], account_b["account_token"], category_key)
            assert status == 404, response
            assert response["code"] == "QIT001010"

        assert status_of(account_a, category_key) == "ACTIVE"

    def test_missing_or_wrong_token_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()
        category_key = create_category(account, "carro")

        for account_token in [None, "token_errado"]:
            for send in [RequestGenerator.GET_category, RequestGenerator.DELETE_category]:
                status, response = send(account["account_key"], account_token, category_key)
                assert status == 404, response
                assert response["code"] == "QIT001010"

        assert status_of(account, category_key) == "ACTIVE"
