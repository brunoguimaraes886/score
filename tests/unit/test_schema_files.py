"""Confere os arquivos de src/schemas/ como texto: cada um é o contrato de entrada de uma rota.

O teste não importa nada de src/: abre o JSON do disco e compara com o que
o plano define. Que a API responde 400 para o corpo fora do schema, cada
rota prova no teste black box dela.
"""

import json
from pathlib import Path

import pytest


SCHEMA_DIR = Path(__file__).resolve().parents[2] / "src" / "schemas"

# Draft 4: nele, o tipo "integer" recusa 5050.0. A partir do draft 6, o
# jsonschema aceita número com ponto e parte decimal zero como inteiro (R6).
DRAFT_04 = "http://json-schema.org/draft-04/schema#"

CPF_PATTERN = "^[0-9]{3}\\.[0-9]{3}\\.[0-9]{3}-[0-9]{2}$"
CNPJ_PATTERN = "^[0-9]{2}\\.[0-9]{3}\\.[0-9]{3}/[0-9]{4}-[0-9]{2}$"
DATE_PATTERN = "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
UUID_PATTERN = "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"

# O maior valor que cabe num BIGINT do PostgreSQL (DAD-08).
BIGINT_MAX = 9223372036854775807

TEXT_FIELD = {"type": "string", "minLength": 1, "maxLength": 255}
DATE_FIELD = {"type": "string", "minLength": 10, "maxLength": 10, "pattern": DATE_PATTERN}
UUID_FIELD = {"type": "string", "minLength": 36, "maxLength": 36, "pattern": UUID_PATTERN}
MONEY_FIELD = {"type": "integer", "minimum": 1, "maximum": BIGINT_MAX}

# O formato de cada campo, igual em todo schema que o usa.
FIELD_RULES = {
    "name": TEXT_FIELD,
    "depositor_name": TEXT_FIELD,
    "document_number": {"type": "string", "minLength": 14, "maxLength": 14, "pattern": CPF_PATTERN},
    "depositor_document": {
        "type": "string",
        "anyOf": [
            {"minLength": 14, "maxLength": 14, "pattern": CPF_PATTERN},
            {"minLength": 18, "maxLength": 18, "pattern": CNPJ_PATTERN},
        ],
    },
    "email": {"type": "string", "maxLength": 255, "pattern": "^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$"},
    "birthdate": DATE_FIELD,
    "accounting_date": DATE_FIELD,
    "amount": MONEY_FIELD,
    "request_control_key": UUID_FIELD,
    "destination_account_key": UUID_FIELD,
    "category_key": UUID_FIELD,
    "limit": {"type": "string", "pattern": "^(100|[1-9][0-9]?)$"},
    "page": {"type": "string", "pattern": "^[0-9]{1,9}$"},
    "points": {"type": "integer", "minimum": 1},
    "benefit": {"type": "string", "enum": ["FEE", "CHANCE"]},
    "reason": {
        "type": "string",
        "enum": ["SUSPICIOUS_ACTIVITY", "JUDICIAL_ORDER", "CUSTOMER_REQUEST", "MANUAL_REVIEW"],
    },
}

# Um item por arquivo de src/schemas/: o title, os campos e os obrigatórios.
# Lista de obrigatórios vazia = o schema não tem a chave "required".
EXPECTED_SCHEMAS = {
    "post_customers.json": {
        "title": "PostCustomers",
        "fields": ["name", "document_number", "email", "birthdate"],
        "required": ["name", "document_number", "email", "birthdate"],
    },
    "post_deposits.json": {
        "title": "PostDeposits",
        "fields": ["depositor_name", "depositor_document", "amount", "request_control_key"],
        "required": ["depositor_name", "depositor_document", "amount", "request_control_key"],
    },
    "post_withdrawals.json": {
        "title": "PostWithdrawals",
        "fields": ["amount", "request_control_key"],
        "required": ["amount", "request_control_key"],
    },
}  # fim de EXPECTED_SCHEMAS

SCHEMA_NAMES = sorted(EXPECTED_SCHEMAS)


def load_schema(name):
    path = SCHEMA_DIR / name
    assert path.is_file(), f"Falta o schema {name} em src/schemas/"
    return json.loads(path.read_text(encoding="utf-8"))


def test_schema_folder_has_exactly_the_expected_files():
    found = sorted(path.name for path in SCHEMA_DIR.glob("*.json"))
    assert found == SCHEMA_NAMES


@pytest.mark.parametrize("name", SCHEMA_NAMES)
def test_schema_header(name):
    schema = load_schema(name)
    assert schema["$schema"] == DRAFT_04
    assert schema["title"] == EXPECTED_SCHEMAS[name]["title"]
    assert schema["type"] == "object"


@pytest.mark.parametrize("name", SCHEMA_NAMES)
def test_schema_is_closed(name):
    schema = load_schema(name)
    assert schema["additionalProperties"] is False


@pytest.mark.parametrize("name", SCHEMA_NAMES)
def test_schema_fields_and_required(name):
    schema = load_schema(name)
    expected = EXPECTED_SCHEMAS[name]
    assert sorted(schema["properties"]) == sorted(expected["fields"])

    if expected["required"]:
        assert sorted(schema["required"]) == sorted(expected["required"])
    else:
        assert "required" not in schema


@pytest.mark.parametrize("name", SCHEMA_NAMES)
def test_schema_field_formats(name):
    schema = load_schema(name)
    for field, rule in schema["properties"].items():
        assert field in FIELD_RULES, f"Campo {field} sem regra no teste"
        assert rule == FIELD_RULES[field], f"Formato errado em {name}: {field}"


@pytest.mark.parametrize("name", SCHEMA_NAMES)
def test_schema_has_no_float_type(name):
    load_schema(name)
    text = (SCHEMA_DIR / name).read_text(encoding="utf-8")
    assert '"number"' not in text
