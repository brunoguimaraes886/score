"""Programa o Mockserver, que faz o papel do Banco Central nos testes (ARQ-05, ARQ-07, TST-01).

O Mockserver sobe com 10 anos de CDI real (mockserver/cdi_expectations.json).
Cada teste que fecha um dia programa a taxa desse dia por aqui: a
expectativa do teste tem prioridade maior que a do arquivo e um id fixo
por data, e programar a mesma data de novo troca a anterior.
"""

import json
import time
from os import environ

from requests import request
from requests.exceptions import ConnectionError as RequestsConnectionError, Timeout as RequestsTimeout


MOCKSERVER_URL = environ.get("MOCKSERVER_URL", "http://127.0.0.1:1080")

# O mesmo caminho que o BcbConnector chama (COF-17).
CDI_SERIES_PATH = "/dados/serie/bcdata.sgs.12/dados"

# As expectativas do arquivo têm prioridade 0: a do teste ganha.
TEST_PRIORITY = 10

# Limite de espera real, incluindo o tempo das chamadas HTTP.
READY_TIMEOUT_SECONDS = 60
REQUEST_TIMEOUT_SECONDS = 10

MOCKSERVER_OFFLINE = (
    "Não consegui falar com o Mockserver em {base_url}.\n"
    "Ele precisa estar de pé pros testes da virada. Suba com:  docker compose up -d --build --wait"
)


def _brazilian_date(accounting_date: str) -> str:
    """"2026-06-01" → "01/06/2026", o formato da série do Banco Central."""
    year, month, day = accounting_date.split("-")

    return f"{day}/{month}/{year}"


def _expectation_id(accounting_date: str) -> str:
    return f"cdi-test-{accounting_date}"


def _send(path: str, payload: dict):
    """PUT no Mockserver; espera ele subir, uma tentativa por segundo."""
    deadline = time.monotonic() + READY_TIMEOUT_SECONDS
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        try:
            return request("PUT", f"{MOCKSERVER_URL}{path}", json=payload, timeout=min(REQUEST_TIMEOUT_SECONDS, remaining))
        except (RequestsConnectionError, RequestsTimeout):
            remaining = deadline - time.monotonic()
            if remaining > 0:
                time.sleep(min(1, remaining))

    raise RuntimeError(MOCKSERVER_OFFLINE.format(base_url=MOCKSERVER_URL))


def _put_expectation(accounting_date: str, body: list, delay_seconds: int = None) -> None:
    day = _brazilian_date(accounting_date)

    http_response = {
        "statusCode": 200,
        "headers": {"Content-Type": ["application/json"]},
        "body": json.dumps(body),
    }

    if delay_seconds is not None:
        http_response["delay"] = {"timeUnit": "SECONDS", "value": delay_seconds}

    expectation = {
        "id": _expectation_id(accounting_date),
        "priority": TEST_PRIORITY,
        "httpRequest": {
            "method": "GET",
            "path": CDI_SERIES_PATH,
            "queryStringParameters": {
                "formato": ["json"],
                "dataInicial": [day],
                "dataFinal": [day],
            },
        },
        "httpResponse": http_response,
        "times": {"unlimited": True},
    }

    response = _send("/mockserver/expectation", expectation)
    assert response.status_code == 201, response.text


class MockGenerator:
    """Um método por situação do Banco Central que os testes da virada precisam (COF-16, COF-17, COF-20)."""

    @staticmethod
    def set_cdi_rate(accounting_date: str, cdi_rate: str = None) -> None:
        """A taxa do CDI do dia (AAAA-MM-DD), em texto e em % ao dia ("0.054266"). None: o dia não tem taxa (COF-16)."""
        body = []
        if cdi_rate is not None:
            body = [{"data": _brazilian_date(accounting_date), "valor": cdi_rate}]

        _put_expectation(accounting_date, body)

    @staticmethod
    def set_cdi_delay(accounting_date: str, delay_seconds: int, cdi_rate: str = "0.054266") -> None:
        """A taxa do dia chega só depois de delay_seconds: acima do BCB_API_TIMEOUT (5), a API desiste (COF-20)."""
        body = [{"data": _brazilian_date(accounting_date), "valor": cdi_rate}]

        _put_expectation(accounting_date, body, delay_seconds)

    @staticmethod
    def clear_cdi(accounting_date: str) -> None:
        """Apaga a expectativa do teste para a data: volta a valer a do arquivo."""
        response = _send("/mockserver/clear?type=EXPECTATIONS", {"id": _expectation_id(accounting_date)})
        assert response.status_code in [200, 400], response.text
