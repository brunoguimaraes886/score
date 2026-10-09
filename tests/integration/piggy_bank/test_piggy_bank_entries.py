"""Extrato do cofrinho e as duas pontas de guardar e resgatar (COF-05, COF-08, MOV-04, MOV-14, MOV-17, MOV-18, DAD-07, R5, R8).

GET /accounts/{account_key}/piggy_bank_entries: o extrato do cofrinho, no
envelope e na ordem do extrato da conta, com a categoria de cada
lançamento e a outra ponta (a conta principal). No extrato da conta e na
consulta da operação, a outra ponta de guardar e resgatar é o cofrinho e a
categoria. Os testes que erram o token começam com DbUtils.rollback()
(PRD-10).
"""

import re
from uuid import uuid4

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator


DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
DATETIME = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}")
ENTRY_FIELDS = sorted([
    "entry_key", "transaction_key", "transaction_type", "entry_type", "amount",
    "balance_after", "category", "counterparty", "accounting_date", "created_at",
])


def assert_no_internal_id(body) -> None:
    """R5: nenhum campo id nem terminado em _id, em nenhum nível da resposta."""
    if isinstance(body, dict):
        for field, value in body.items():
            assert field != "id", field
            assert not field.endswith("_id"), field
            assert_no_internal_id(value)

    if isinstance(body, list):
        for item in body:
            assert_no_internal_id(item)


def piggy_bank_entries(account: dict, params: dict = None) -> dict:
    status, response = RequestGenerator.GET_piggy_bank_entries(account["account_key"], account["account_token"], params)
    assert status == 200, response

    return response


def account_entries(account: dict) -> dict:
    status, response = RequestGenerator.GET_entries(account["account_key"], account["account_token"])
    assert status == 200, response

    return response


def piggy_bank_balance_of(account: dict) -> int:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["piggy_bank_balance"]


def save(account: dict, amount: int, category_key: str = None) -> str:
    payload = PayloadGenerator.saving(amount=amount, category_key=category_key)
    status, response = RequestGenerator.POST_saving(account["account_key"], account["account_token"], payload)
    assert status == 201, response

    return response["transaction_key"]


def redeem(account: dict, amount: int, category_key: str = None) -> str:
    payload = PayloadGenerator.redemption(amount=amount, category_key=category_key)
    status, response = RequestGenerator.POST_redemption(account["account_key"], account["account_token"], payload)
    assert status == 201, response

    return response["transaction_key"]


def default_category_key(account: dict) -> str:
    """A key da "economias", lida no extrato do cofrinho (a rota das categorias nasce na fase 9). A conta já guardou."""
    return piggy_bank_entries(account)["data"][0]["category"]["category_key"]


class TestPiggyBankEntries:
    def test_empty_piggy_bank_statement(self):
        account = ObjectGenerator.create_account()

        status, response = RequestGenerator.GET_piggy_bank_entries(account["account_key"], account["account_token"])

        assert status == 200, response
        assert response == {"data": [], "limit": 10, "page": 0, "is_last_page": True}

    def test_shows_saving_and_redemption_on_both_sides(self):
        account = ObjectGenerator.create_funded_account(100000)
        saving_key = save(account, 30000)
        redemption_key = redeem(account, 10000)

        statement = piggy_bank_entries(account)
        assert_no_internal_id(statement)
        assert (statement["limit"], statement["page"], statement["is_last_page"]) == (10, 0, True)

        redemption_entry, saving_entry = statement["data"]
        category = saving_entry["category"]
        assert sorted(category) == ["category_key", "name"]
        assert category["name"] == "economias"
        assert len(category["category_key"]) == 36

        for entry in statement["data"]:
            assert sorted(entry) == ENTRY_FIELDS
            assert entry["entry_type"] == "AMOUNT"
            assert entry["category"] == category
            assert entry["counterparty"] == {"type": "ACCOUNT"}
            assert DATE.match(entry["accounting_date"])
            assert DATETIME.match(entry["created_at"])
            assert type(entry["amount"]) is int
            assert type(entry["balance_after"]) is int

        assert (redemption_entry["transaction_key"], redemption_entry["transaction_type"], redemption_entry["amount"], redemption_entry["balance_after"]) == (redemption_key, "REDEEM", -10000, 20000)
        assert (saving_entry["transaction_key"], saving_entry["transaction_type"], saving_entry["amount"], saving_entry["balance_after"]) == (saving_key, "SAVE", 30000, 30000)
        assert sum(entry["amount"] for entry in statement["data"]) == piggy_bank_balance_of(account) == 20000

        statement = account_entries(account)
        assert_no_internal_id(statement)
        piggy_bank_counterparty = {"type": "PIGGY_BANK", "category_key": category["category_key"], "name": "economias"}

        redemption_entry, saving_entry, deposit_entry = statement["data"]
        assert (redemption_entry["transaction_type"], redemption_entry["amount"], redemption_entry["balance_after"]) == ("REDEEM", 10000, 80000)
        assert (redemption_entry["category"], redemption_entry["counterparty"]) == (None, piggy_bank_counterparty)
        assert (saving_entry["transaction_type"], saving_entry["amount"], saving_entry["balance_after"]) == ("SAVE", -30000, 70000)
        assert (saving_entry["category"], saving_entry["counterparty"]) == (None, piggy_bank_counterparty)
        assert deposit_entry["transaction_type"] == "DEPOSIT"

    def test_pagination(self):
        account = ObjectGenerator.create_funded_account(100000)
        for amount in [100, 200, 300]:
            save(account, amount)

        first_page = piggy_bank_entries(account, {"limit": "2", "page": "0"})
        assert [entry["amount"] for entry in first_page["data"]] == [300, 200]
        assert (first_page["limit"], first_page["page"], first_page["is_last_page"]) == (2, 0, False)

        second_page = piggy_bank_entries(account, {"limit": "2", "page": "1"})
        assert [entry["amount"] for entry in second_page["data"]] == [100]
        assert (second_page["limit"], second_page["page"], second_page["is_last_page"]) == (2, 1, True)

    def test_filters_by_the_default_category(self):
        account = ObjectGenerator.create_funded_account(100000)
        save(account, 1000)
        save(account, 2000)

        filtered = piggy_bank_entries(account, {"category_key": default_category_key(account)})

        assert [entry["amount"] for entry in filtered["data"]] == [2000, 1000]
        assert filtered["is_last_page"] is True

    def test_unknown_category_is_404(self):
        account = ObjectGenerator.create_funded_account(10000)
        save(account, 1000)

        status, response = RequestGenerator.GET_piggy_bank_entries(account["account_key"], account["account_token"], {"category_key": str(uuid4())})
        assert status == 404, response
        assert response["code"] == "QIT001021"

        assert len(piggy_bank_entries(account)["data"]) == 1

    def test_saves_and_redeems_with_the_default_category_key(self):
        account = ObjectGenerator.create_funded_account(10000)
        save(account, 1000)
        category_key = default_category_key(account)

        save(account, 500, category_key)
        assert piggy_bank_balance_of(account) == 1500

        redeem(account, 700, category_key)
        assert piggy_bank_balance_of(account) == 800

        assert [entry["category"]["category_key"] for entry in piggy_bank_entries(account)["data"]] == [category_key, category_key, category_key]

    def test_gets_saving_and_redemption_transactions(self):
        account = ObjectGenerator.create_funded_account(100000)
        saving_key = save(account, 30000)
        redemption_key = redeem(account, 10000)
        category_key = default_category_key(account)
        category = {"category_key": category_key, "name": "economias"}
        piggy_bank_counterparty = {"type": "PIGGY_BANK", "category_key": category_key, "name": "economias"}

        status, saving = RequestGenerator.GET_transaction(account["account_key"], account["account_token"], saving_key)
        assert status == 200, saving
        assert_no_internal_id(saving)
        assert saving["type"] == "SAVE"
        assert "gross_amount" not in saving
        assert [(entry["amount"], entry["balance_after"], entry["category"], entry["counterparty"]) for entry in saving["entries"]] == [
            (-30000, 70000, None, piggy_bank_counterparty),
            (30000, 30000, category, {"type": "ACCOUNT"}),
        ]

        status, redemption = RequestGenerator.GET_transaction(account["account_key"], account["account_token"], redemption_key)
        assert status == 200, redemption
        assert_no_internal_id(redemption)
        assert redemption["type"] == "REDEEM"
        assert (redemption["gross_amount"], redemption["iof"], redemption["ir"], redemption["net_amount"]) == (10000, 0, 0, 10000)
        assert [(entry["amount"], entry["balance_after"], entry["category"], entry["counterparty"]) for entry in redemption["entries"]] == [
            (-10000, 20000, category, {"type": "ACCOUNT"}),
            (10000, 80000, None, piggy_bank_counterparty),
        ]

    def test_refuses_query_out_of_schema(self):
        account = ObjectGenerator.create_account()

        for params in [{"limit": "0"}, {"limit": "101"}, {"limit": "abc"}, {"page": "-1"}, {"category_key": "economias"}, {"size": "10"}]:
            status, response = RequestGenerator.GET_piggy_bank_entries(account["account_key"], account["account_token"], params)
            assert status == 400, (params, response)
            assert response["code"] == "QIT000001"

    def test_other_account_token_is_404(self):
        DbUtils.rollback()
        account_a = ObjectGenerator.create_account()
        account_b = ObjectGenerator.create_account()

        status, response = RequestGenerator.GET_piggy_bank_entries(account_a["account_key"], account_b["account_token"])
        assert status == 404, response
        assert response["code"] == "QIT001010"

        status, response = RequestGenerator.GET_piggy_bank_entries(account_b["account_key"], account_a["account_token"])
        assert status == 404, response
        assert response["code"] == "QIT001010"

        piggy_bank_entries(account_a)

    def test_missing_or_wrong_token_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()

        for account_token in [None, "token_errado"]:
            status, response = RequestGenerator.GET_piggy_bank_entries(account["account_key"], account_token)
            assert status == 404, (account_token, response)
            assert response["code"] == "QIT001010"

        status, response = RequestGenerator.GET_piggy_bank_entries(str(uuid4()), account["account_token"])
        assert status == 404, response
        assert response["code"] == "QIT001010"

        piggy_bank_entries(account)
