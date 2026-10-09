"""Barreira contra chute dos tokens internos (PRD-10, PRD-04).

AUTH_FAILURE_LIMIT erros de INTERNAL-TOKEN ou ADMIN-TOKEN do mesmo IP
fazem toda requisição desse IP responder 429 QIT000429, antes de
conferir token. A contagem mora em request_log (PRD-04): cada teste
começa e termina com DbUtils.rollback(). Sem a limpeza do fim, o IP dos
testes ficaria barrado para o resto da suíte.

A janela de AUTH_FAILURE_WINDOW_MINUTES minutos não é testada aqui: o
teste teria de esperar a janela passar.
"""

from os import environ

from tests.utils import INTERNAL_TOKEN, DbUtils
from tests.utils.requisition import ClientRequisition


ADMIN_TOKEN = environ.get("ADMIN_TOKEN", "default_admin_token")
AUTH_FAILURE_LIMIT = int(environ.get("AUTH_FAILURE_LIMIT", "10"))

WRONG_TOKEN = "token_errado"
UNKNOWN_PATH = "/nao_existe"
INTERNAL_PATH = "/internal/nao_existe"
TOO_MANY_TRANSLATION = "Tentativas demais com token errado. Tente de novo mais tarde."


def fail_internal_token(times: int) -> None:
    for _ in range(times):
        response = ClientRequisition.send("GET", UNKNOWN_PATH, headers={"INTERNAL-TOKEN": WRONG_TOKEN})
        assert response.response_status == 403
        assert response.response_json["code"] == "QIT000002"


def fail_admin_token(times: int) -> None:
    for _ in range(times):
        response = ClientRequisition.send(
            "GET",
            INTERNAL_PATH,
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN, "ADMIN-TOKEN": WRONG_TOKEN},
        )
        assert response.response_status == 403
        assert response.response_json["code"] == "QIT000003"


def send_with_internal_token():
    return ClientRequisition.send("GET", UNKNOWN_PATH, headers={"INTERNAL-TOKEN": INTERNAL_TOKEN})


def assert_not_blocked() -> None:
    response = send_with_internal_token()
    assert response.response_status == 404
    assert response.response_json["code"] == "QIT000404"


def assert_blocked() -> None:
    response = send_with_internal_token()
    assert response.response_status == 429
    assert response.response_json["code"] == "QIT000429"
    assert response.response_json["translation"] == TOO_MANY_TRANSLATION


class TestAuthBarrier:
    def test_limit_of_internal_failures_blocks_the_ip(self):
        DbUtils.rollback()
        try:
            fail_internal_token(AUTH_FAILURE_LIMIT)

            assert_blocked()

            response = ClientRequisition.send("GET", UNKNOWN_PATH)
            assert response.response_status == 429
            assert response.response_json["code"] == "QIT000429"

            response = ClientRequisition.send(
                "POST",
                INTERNAL_PATH,
                headers={"INTERNAL-TOKEN": INTERNAL_TOKEN, "ADMIN-TOKEN": ADMIN_TOKEN},
            )
            assert response.response_status == 429
            assert response.response_json["code"] == "QIT000429"
        finally:
            DbUtils.rollback()

    def test_one_failure_below_the_limit_does_not_block(self):
        DbUtils.rollback()
        try:
            fail_internal_token(AUTH_FAILURE_LIMIT - 1)

            assert_not_blocked()

            fail_internal_token(1)

            assert_blocked()
        finally:
            DbUtils.rollback()

    def test_limit_of_admin_failures_blocks_the_ip(self):
        DbUtils.rollback()
        try:
            fail_admin_token(AUTH_FAILURE_LIMIT)

            assert_blocked()
        finally:
            DbUtils.rollback()

    def test_internal_and_admin_failures_add_up(self):
        DbUtils.rollback()
        try:
            fail_internal_token(AUTH_FAILURE_LIMIT // 2)
            fail_admin_token(AUTH_FAILURE_LIMIT - AUTH_FAILURE_LIMIT // 2)

            assert_blocked()
        finally:
            DbUtils.rollback()

    def test_successful_requests_do_not_count(self):
        DbUtils.rollback()
        try:
            for _ in range(2 * AUTH_FAILURE_LIMIT):
                assert_not_blocked()

            fail_internal_token(AUTH_FAILURE_LIMIT - 1)

            assert_not_blocked()

            fail_internal_token(1)

            assert_blocked()
        finally:
            DbUtils.rollback()

    def test_public_routes_skip_the_barrier(self):
        DbUtils.rollback()
        try:
            fail_internal_token(AUTH_FAILURE_LIMIT)

            response = ClientRequisition.send("GET", "/")
            assert response.response_status == 200

            response = ClientRequisition.send("GET", "/health_check")
            assert response.response_status == 204

            assert_blocked()
        finally:
            DbUtils.rollback()
