"""Cadastro de cliente: POST /customers (CLI-02, CLI-03, TST-03, API-03, API-04).

O controller confere, nesta ordem: CPF válido (422 QIT001003), CPF único
(409 QIT001004), e-mail único (409 QIT001005), data que existe (422
QIT001007) e idade mínima de 18 anos (422 QIT001006). O formato de cada
campo é do schema post_customers.json (400 QIT000001).
"""

import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

from tests.utils import DbUtils, PayloadGenerator, RandomGenerator, RequestGenerator


UUID_V4 = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
PARALLEL_REQUESTS = 8
INVALID_CPF = "111.222.333-44"
DUPLICATED_DOCUMENT_TRANSLATION = "Já existe um cadastro com este CPF."
UNDERAGE_TRANSLATION = "É preciso ter pelo menos 18 anos."


def birthdate_for_age(age_in_years: int) -> str:
    """A data de nascimento de quem faz essa idade hoje; num 29/02, a de 28/02."""
    today = date.today()

    if today.month == 2 and today.day == 29:
        return date(today.year - age_in_years, 2, 28).isoformat()

    return date(today.year - age_in_years, today.month, today.day).isoformat()


def birthdate_turning_age_in_two_days(age_in_years: int) -> str:
    """A data de nascimento de quem faz essa idade daqui a dois dias.

    Dois dias, e não um: o container da API roda em UTC e pode estar um
    dia à frente da máquina que roda os testes. Um 29/02 vira 01/03.
    """
    birthday = date.today() + timedelta(days=2)

    if birthday.month == 2 and birthday.day == 29:
        birthday = birthday + timedelta(days=1)

    return date(birthday.year - age_in_years, birthday.month, birthday.day).isoformat()


def assert_no_internal_id(body: dict) -> None:
    """R5: nenhum campo id nem terminado em _id na resposta."""
    for field in body:
        assert field != "id", field
        assert not field.endswith("_id"), field


def post_customers_in_parallel(payloads: list) -> list:
    with ThreadPoolExecutor(max_workers=len(payloads)) as executor:
        return list(executor.map(RequestGenerator.POST_customer, payloads))


def assert_one_created_and_the_rest_refused(results: list, error_code: str) -> None:
    statuses = sorted(status for status, _response in results)
    assert statuses == [201] + [409] * (len(results) - 1), results

    codes = [response["code"] for status, response in results if status == 409]
    assert codes == [error_code] * (len(results) - 1), codes


class TestCreateCustomer:
    def test_creates_customer(self):
        payload = PayloadGenerator.customer()
        status, response = RequestGenerator.POST_customer(payload)
        assert status == 201, response
        assert list(response) == ["customer_key"]
        assert UUID_V4.match(response["customer_key"])
        assert_no_internal_id(response)

    def test_refuses_invalid_document_number(self):
        for document_number in [INVALID_CPF, "111.111.111-11"]:
            payload = PayloadGenerator.customer(document_number=document_number)
            status, response = RequestGenerator.POST_customer(payload)
            assert status == 422, (document_number, response)
            assert response["code"] == "QIT001003"

    def test_refuses_duplicated_document_number(self):
        first = PayloadGenerator.customer()
        status, response = RequestGenerator.POST_customer(first)
        assert status == 201, response
        second = PayloadGenerator.customer(document_number=first["document_number"])
        status, response = RequestGenerator.POST_customer(second)
        assert status == 409, response
        assert response["code"] == "QIT001004"
        assert response["translation"] == DUPLICATED_DOCUMENT_TRANSLATION

    def test_refuses_duplicated_email(self):
        first = PayloadGenerator.customer()
        status, response = RequestGenerator.POST_customer(first)
        assert status == 201, response
        second = PayloadGenerator.customer(email=first["email"])
        status, response = RequestGenerator.POST_customer(second)
        assert status == 409, response
        assert response["code"] == "QIT001005"

    def test_refuses_underage(self):
        for birthdate in [birthdate_for_age(17), birthdate_turning_age_in_two_days(18)]:
            payload = PayloadGenerator.customer(birthdate=birthdate)
            status, response = RequestGenerator.POST_customer(payload)
            assert status == 422, (birthdate, response)
            assert response["code"] == "QIT001006"
            assert response["translation"] == UNDERAGE_TRANSLATION

    def test_accepts_minimum_age_and_has_no_maximum(self):
        for birthdate in [birthdate_for_age(18), "1900-01-01"]:
            payload = PayloadGenerator.customer(birthdate=birthdate)
            status, response = RequestGenerator.POST_customer(payload)
            assert status == 201, (birthdate, response)

    def test_refuses_impossible_birthdate(self):
        for birthdate in ["2025-02-30", "9999-99-99"]:
            payload = PayloadGenerator.customer(birthdate=birthdate)
            status, response = RequestGenerator.POST_customer(payload)
            assert status == 422, (birthdate, response)
            assert response["code"] == "QIT001007"

    def test_checks_rules_in_order(self):
        existing = PayloadGenerator.customer()
        status, response = RequestGenerator.POST_customer(existing)
        assert status == 201, response
        underage = birthdate_for_age(17)
        cases = [
            (PayloadGenerator.customer(document_number=INVALID_CPF, email=existing["email"], birthdate=underage), "QIT001003"),
            (PayloadGenerator.customer(document_number=existing["document_number"], email=existing["email"], birthdate=underage), "QIT001004"),
            (PayloadGenerator.customer(email=existing["email"], birthdate="2025-02-30"), "QIT001005"),
        ]
        for payload, error_code in cases:
            status, response = RequestGenerator.POST_customer(payload)
            assert response["code"] == error_code, (payload, response)

    def test_refuses_body_out_of_schema(self):
        payloads = []
        payload = PayloadGenerator.customer()
        payload["extra"] = 1
        payloads.append(payload)
        for field in ["name", "document_number", "email", "birthdate"]:
            payload = PayloadGenerator.customer()
            del payload[field]
            payloads.append(payload)
        wrong_values = [("name", 123), ("name", ""), ("document_number", "12345678909"), ("email", "ana.lima"), ("birthdate", "17/05/1990")]
        for field, wrong_value in wrong_values:
            payload = PayloadGenerator.customer()
            payload[field] = wrong_value
            payloads.append(payload)
        payloads.append({})
        for payload in payloads:
            status, response = RequestGenerator.POST_customer(payload)
            assert status == 400, (payload, response)
            assert response["code"] == "QIT000001"

    def test_requires_internal_token(self):
        DbUtils.rollback()
        status, response = RequestGenerator.POST_customer(PayloadGenerator.customer())
        assert status == 201, response
        for internal_token in [None, "token_errado"]:
            status, response = RequestGenerator.POST_customer(PayloadGenerator.customer(), internal_token=internal_token)
            assert status == 403, (internal_token, response)
            assert response["code"] == "QIT000002"

    def test_concurrent_same_document_number(self):
        document_number = RandomGenerator.generate_cpf()
        payloads = [PayloadGenerator.customer(document_number=document_number) for _ in range(PARALLEL_REQUESTS)]
        results = post_customers_in_parallel(payloads)
        assert_one_created_and_the_rest_refused(results, "QIT001004")

    def test_concurrent_same_email(self):
        email = PayloadGenerator.customer()["email"]
        payloads = [PayloadGenerator.customer(email=email) for _ in range(PARALLEL_REQUESTS)]
        results = post_customers_in_parallel(payloads)
        assert_one_created_and_the_rest_refused(results, "QIT001005")
