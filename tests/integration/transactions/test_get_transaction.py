"""Consulta da operação: GET /accounts/{account_key}/transactions/{transaction_key} (MOV-07, MOV-09, MOV-17, MOV-18, DAD-17, PRD-12, R5, R8).

O dono vê a operação e os lançamentos dela na conta dele, com a outra
ponta de cada um: na transferência, o outro cliente com o CPF mascarado;
no depósito, quem depositou; na tarifa, o banco; no saque, nada.
Operação de outra conta responde como se não existisse. Os testes que
erram o token começam com DbUtils.rollback() (PRD-10).
"""

import re
from uuid import uuid4

from tests.utils import INTERNAL_TOKEN, DbUtils, ObjectGenerator, PayloadGenerator, RandomGenerator, RequestGenerator
from tests.utils.requisition import ClientRequisition


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


def masked_cpf(document_number: str) -> str:
    return "***" + document_number[3:12] + "**"


def create_named_account(name: str, document_number: str) -> dict:
    customer_key = ObjectGenerator.create_customer(name=name, document_number=document_number)

    return ObjectGenerator.create_account(customer_key)


def get_transaction(account: dict, transaction_key: str) -> tuple:
    return RequestGenerator.GET_transaction(account["account_key"], account["account_token"], transaction_key)


def assert_transaction(response: dict, transaction_key: str, transaction_type: str) -> None:
    assert sorted(response) == ["accounting_date", "created_at", "entries", "transaction_key", "type"]
    assert response["transaction_key"] == transaction_key
    assert response["type"] == transaction_type
    assert DATE.match(response["accounting_date"])
    assert DATETIME.match(response["created_at"])

    for entry in response["entries"]:
        assert sorted(entry) == ENTRY_FIELDS
        assert entry["transaction_key"] == transaction_key
        assert entry["transaction_type"] == transaction_type
        assert entry["accounting_date"] == response["accounting_date"]
        assert DATETIME.match(entry["created_at"])
        assert entry["category"] is None
        assert type(entry["amount"]) is int

    assert_no_internal_id(response)


class TestGetTransaction:
    def test_gets_transfer_from_the_origin(self):
        origin = ObjectGenerator.create_funded_account(50000)
        destination_document = RandomGenerator.generate_cpf()
        destination = create_named_account("Bruno Alves", destination_document)

        status, response = RequestGenerator.POST_transfer(
            origin["account_key"], origin["account_token"], PayloadGenerator.transfer(destination["account_key"], amount=10000)
        )
        assert status == 201, response
        transaction_key = response["transaction_key"]

        status, response = get_transaction(origin, transaction_key)

        assert status == 200, response
        assert_transaction(response, transaction_key, "TRANSFER")
        assert [(entry["entry_type"], entry["amount"], entry["balance_after"]) for entry in response["entries"]] == [
            ("AMOUNT", -10000, 40000),
            ("FEE", -100, 39900),
        ]
        assert response["entries"][0]["counterparty"] == {
            "type": "CUSTOMER",
            "name": "Bruno Alves",
            "document_number": masked_cpf(destination_document),
        }
        assert response["entries"][1]["counterparty"] == {"type": "BANK"}

    def test_gets_transfer_from_the_destination(self):
        origin_document = RandomGenerator.generate_cpf()
        origin = create_named_account("Ana Lima", origin_document)
        status, response = RequestGenerator.POST_deposit(origin["account_key"], PayloadGenerator.deposit(amount=50000))
        assert status == 201, response
        destination = ObjectGenerator.create_account()

        status, response = RequestGenerator.POST_transfer(
            origin["account_key"], origin["account_token"], PayloadGenerator.transfer(destination["account_key"], amount=10000)
        )
        assert status == 201, response
        transaction_key = response["transaction_key"]

        status, response = get_transaction(destination, transaction_key)

        assert status == 200, response
        assert_transaction(response, transaction_key, "TRANSFER")
        assert len(response["entries"]) == 1
        entry = response["entries"][0]
        assert (entry["entry_type"], entry["amount"], entry["balance_after"]) == ("AMOUNT", 10000, 10000)
        assert entry["counterparty"] == {"type": "CUSTOMER", "name": "Ana Lima", "document_number": masked_cpf(origin_document)}

    def test_gets_deposit_with_masked_depositor(self):
        account = ObjectGenerator.create_account()
        cnpj = RandomGenerator.generate_cnpj()
        cpf = RandomGenerator.generate_cpf()

        expected = []
        for depositor_document, masked in [(cnpj, "**" + cnpj[2:11] + "****-**"), (cpf, masked_cpf(cpf))]:
            payload = PayloadGenerator.deposit(amount=5050, depositor_name="Carlos Souza", depositor_document=depositor_document)
            status, response = RequestGenerator.POST_deposit(account["account_key"], payload)
            assert status == 201, response
            expected.append((response["transaction_key"], masked))

        for index, (transaction_key, masked) in enumerate(expected):
            status, response = get_transaction(account, transaction_key)

            assert status == 200, response
            assert_transaction(response, transaction_key, "DEPOSIT")
            assert len(response["entries"]) == 1
            entry = response["entries"][0]
            assert (entry["entry_type"], entry["amount"], entry["balance_after"]) == ("AMOUNT", 5050, 5050 * (index + 1))
            assert entry["counterparty"] == {"type": "DEPOSITOR", "name": "Carlos Souza", "document_number": masked}

    def test_gets_withdrawal_without_counterparty(self):
        account = ObjectGenerator.create_funded_account(10000)

        status, response = RequestGenerator.POST_withdrawal(account["account_key"], account["account_token"], PayloadGenerator.withdrawal(amount=2500))
        assert status == 201, response
        transaction_key = response["transaction_key"]

        status, response = get_transaction(account, transaction_key)

        assert status == 200, response
        assert_transaction(response, transaction_key, "WITHDRAWAL")
        assert len(response["entries"]) == 1
        entry = response["entries"][0]
        assert (entry["entry_type"], entry["amount"], entry["balance_after"], entry["counterparty"]) == ("AMOUNT", -2500, 7500, None)

    def test_transaction_of_other_account_is_404(self):
        origin = ObjectGenerator.create_funded_account(10000)
        destination = ObjectGenerator.create_account()
        stranger = ObjectGenerator.create_account()

        status, response = RequestGenerator.POST_transfer(
            origin["account_key"], origin["account_token"], PayloadGenerator.transfer(destination["account_key"], amount=1000)
        )
        assert status == 201, response

        for transaction_key in [response["transaction_key"], str(uuid4()), "nao-e-uma-key"]:
            status, response = get_transaction(stranger, transaction_key)

            assert status == 404, (transaction_key, response)
            assert response["code"] == "QIT001020"

    def test_other_account_token_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_funded_account(10000)
        other_account = ObjectGenerator.create_account()

        status, response = RequestGenerator.POST_withdrawal(account["account_key"], account["account_token"], PayloadGenerator.withdrawal(amount=100))
        assert status == 201, response
        transaction_key = response["transaction_key"]

        for account_token in [other_account["account_token"], None, "token_errado"]:
            status, response = RequestGenerator.GET_transaction(account["account_key"], account_token, transaction_key)

            assert status == 404, (account_token, response)
            assert response["code"] == "QIT001010"

        status, response = get_transaction(account, transaction_key)
        assert status == 200, response

    def test_put_patch_and_delete_are_405(self):
        account = ObjectGenerator.create_funded_account(10000)

        status, response = RequestGenerator.POST_withdrawal(account["account_key"], account["account_token"], PayloadGenerator.withdrawal(amount=100))
        assert status == 201, response
        transaction_key = response["transaction_key"]

        status, before = get_transaction(account, transaction_key)
        assert status == 200, before

        endpoint = f"/accounts/{account['account_key']}/transactions/{transaction_key}"
        headers = {"INTERNAL-TOKEN": INTERNAL_TOKEN, "ACCOUNT-TOKEN": account["account_token"]}

        for method in ["PUT", "PATCH", "DELETE"]:
            response = ClientRequisition.send(method, endpoint, payload={"amount": 1}, headers=headers)

            assert response.response_status == 405, (method, response.response_json)
            assert response.response_json["code"] == "QIT000405"

        status, after = get_transaction(account, transaction_key)
        assert status == 200, after
        assert after == before
