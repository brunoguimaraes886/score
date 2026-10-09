"""Extrato: GET /accounts/{account_key}/entries (TST-03, MOV-04, MOV-09, MOV-14, MOV-17, MOV-18, DAD-07, DAD-13, R5, R8).

O extrato da conta principal, no envelope do base (`data`, `limit`,
`page`, `is_last_page`; `limit` padrão 10 e máximo 100; `page` a partir
de 0), mais recente primeiro, com desempate pelo lançamento mais novo.
A soma dos lançamentos é o saldo (DAD-07). Pedido recusado não deixa
lançamento (DAD-13). Os testes que erram o token ou que dependem do
relógio começam com DbUtils.rollback() (PRD-10, DIA-01).
"""

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RandomGenerator, RequestGenerator


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


def get_entries(account: dict, params: dict = None) -> tuple:
    return RequestGenerator.GET_entries(account["account_key"], account["account_token"], params)


def all_entries(account: dict) -> list:
    """Todas as páginas do extrato, com limit 100, da mais recente para a mais antiga."""
    entries = []
    page = 0

    while True:
        status, response = get_entries(account, {"limit": "100", "page": str(page)})
        assert status == 200, response
        entries.extend(response["data"])

        if response["is_last_page"]:
            return entries

        page = page + 1


def balance_of(account: dict) -> int:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["balance"]


def deposit(account: dict, amount: int) -> None:
    status, response = RequestGenerator.POST_deposit(account["account_key"], PayloadGenerator.deposit(amount=amount))
    assert status == 201, response


def transfer(origin: dict, destination: dict, amount: int) -> tuple:
    payload = PayloadGenerator.transfer(destination["account_key"], amount=amount)

    return RequestGenerator.POST_transfer(origin["account_key"], origin["account_token"], payload)


class TestEntries:
    def test_empty_statement(self):
        account = ObjectGenerator.create_account()

        status, response = get_entries(account)

        assert status == 200, response
        assert response == {"data": [], "limit": 10, "page": 0, "is_last_page": True}

    def test_pagination(self):
        account = ObjectGenerator.create_account()
        for amount in [100, 200, 300]:
            deposit(account, amount)

        status, response = get_entries(account, {"limit": "2", "page": "0"})
        assert status == 200, response
        assert (response["limit"], response["page"], response["is_last_page"]) == (2, 0, False)
        assert [entry["amount"] for entry in response["data"]] == [300, 200]

        status, response = get_entries(account, {"limit": "2", "page": "1"})
        assert status == 200, response
        assert (response["limit"], response["page"], response["is_last_page"]) == (2, 1, True)
        assert [entry["amount"] for entry in response["data"]] == [100]

        status, response = get_entries(account, {"limit": "2", "page": "2"})
        assert status == 200, response
        assert (response["data"], response["is_last_page"]) == ([], True)

    def test_default_and_maximum_limit(self):
        account = ObjectGenerator.create_account()
        for amount in range(1, 12):
            deposit(account, amount)

        status, response = get_entries(account)
        assert status == 200, response
        assert (len(response["data"]), response["limit"], response["page"], response["is_last_page"]) == (10, 10, 0, False)

        status, response = get_entries(account, {"limit": "100"})
        assert status == 200, response
        assert (len(response["data"]), response["limit"], response["is_last_page"]) == (11, 100, True)

    def test_most_recent_first_with_stable_tiebreak(self):
        origin = ObjectGenerator.create_funded_account(50000)
        destination = ObjectGenerator.create_account()

        status, response = transfer(origin, destination, 10000)
        assert status == 201, response

        entries = all_entries(origin)

        assert [(entry["transaction_type"], entry["entry_type"], entry["amount"], entry["balance_after"]) for entry in entries] == [
            ("TRANSFER", "FEE", -100, 39900),
            ("TRANSFER", "AMOUNT", -10000, 40000),
            ("DEPOSIT", "AMOUNT", 50000, 50000),
        ]
        assert entries[0]["transaction_key"] == entries[1]["transaction_key"] == response["transaction_key"]
        assert entries[0]["created_at"] == entries[1]["created_at"]
        assert entries[1]["created_at"] >= entries[2]["created_at"]
        assert all_entries(origin) == entries

    def test_shows_every_operation_with_counterparty_and_dates(self):
        origin_document = RandomGenerator.generate_cpf()
        origin = ObjectGenerator.create_account(ObjectGenerator.create_customer(name="Ana Lima", document_number=origin_document))
        destination_document = RandomGenerator.generate_cpf()
        destination = ObjectGenerator.create_account(ObjectGenerator.create_customer(name="Bruno Alves", document_number=destination_document))
        depositor_document = RandomGenerator.generate_cnpj()

        payload = PayloadGenerator.deposit(amount=50000, depositor_name="Carlos Souza", depositor_document=depositor_document)
        status, response = RequestGenerator.POST_deposit(origin["account_key"], payload)
        assert status == 201, response

        status, response = transfer(origin, destination, 10000)
        assert status == 201, response

        status, response = RequestGenerator.POST_withdrawal(origin["account_key"], origin["account_token"], PayloadGenerator.withdrawal(amount=900))
        assert status == 201, response

        origin_entries = all_entries(origin)
        assert [(entry["transaction_type"], entry["entry_type"], entry["amount"], entry["counterparty"]) for entry in origin_entries] == [
            ("WITHDRAWAL", "AMOUNT", -900, None),
            ("TRANSFER", "FEE", -100, {"type": "BANK"}),
            ("TRANSFER", "AMOUNT", -10000, {"type": "CUSTOMER", "name": "Bruno Alves", "document_number": "***" + destination_document[3:12] + "**"}),
            ("DEPOSIT", "AMOUNT", 50000, {"type": "DEPOSITOR", "name": "Carlos Souza", "document_number": "**" + depositor_document[2:11] + "****-**"}),
        ]

        destination_entries = all_entries(destination)
        assert [(entry["entry_type"], entry["amount"], entry["balance_after"], entry["counterparty"]) for entry in destination_entries] == [
            ("AMOUNT", 10000, 10000, {"type": "CUSTOMER", "name": "Ana Lima", "document_number": "***" + origin_document[3:12] + "**"}),
        ]

        for entry in origin_entries + destination_entries:
            assert entry["category"] is None
            assert len(entry["accounting_date"]) == 10
            assert entry["created_at"][10] == "T"
            assert type(entry["amount"]) is int
            assert type(entry["balance_after"]) is int

        assert_no_internal_id(origin_entries + destination_entries)

    def test_statement_reconciles_with_balance(self):
        first = ObjectGenerator.create_funded_account(30000)
        second = ObjectGenerator.create_funded_account(20000)

        for origin, destination, amount in [(first, second, 1234), (second, first, 999), (first, second, 1)]:
            status, response = transfer(origin, destination, amount)
            assert status == 201, response

        status, response = RequestGenerator.POST_withdrawal(first["account_key"], first["account_token"], PayloadGenerator.withdrawal(amount=777))
        assert status == 201, response

        for account in [first, second]:
            entries = all_entries(account)

            assert sum(entry["amount"] for entry in entries) == balance_of(account)
            assert entries[0]["balance_after"] == balance_of(account)

    def test_refused_requests_leave_no_entry(self):
        DbUtils.rollback()
        origin = ObjectGenerator.create_funded_account(100000)
        destination = ObjectGenerator.create_account()

        status, response = transfer(origin, destination, 200000)
        assert status == 422, response

        status, response = RequestGenerator.POST_withdrawal(origin["account_key"], origin["account_token"], PayloadGenerator.withdrawal(amount=200000))
        assert status == 422, response

        for _index in range(10):
            status, response = transfer(origin, destination, 100)
            assert status == 201, response

        status, response = transfer(origin, destination, 100)
        assert status == 422, response
        assert response["code"] == "QIT001019"

        entries = all_entries(origin)
        assert len(entries) == 1 + 10 * 2
        assert sum(entry["amount"] for entry in entries) == balance_of(origin) == 100000 - 10 * 101

    def test_refuses_query_out_of_schema(self):
        account = ObjectGenerator.create_account()

        for params in [{"limit": "0"}, {"limit": "-1"}, {"limit": "101"}, {"limit": "abc"}, {"page": "-1"}, {"page": "x"}, {"size": "10"}]:
            status, response = get_entries(account, params)

            assert status == 400, (params, response)
            assert response["code"] == "QIT000001"

    def test_other_account_token_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_funded_account(1000)
        other_account = ObjectGenerator.create_account()

        for account_token in [other_account["account_token"], None, "token_errado"]:
            status, response = RequestGenerator.GET_entries(account["account_key"], account_token)

            assert status == 404, (account_token, response)
            assert response["code"] == "QIT001010"

        status, response = get_entries(account)
        assert status == 200, response
        assert len(response["data"]) == 1
