"""Token de administração nas rotas /internal (PRD-07, PRD-13, API-13).

Todo teste daqui erra um token de propósito e por isso começa com
DbUtils.rollback(): a barreira contra chute de token (PRD-10) conta os
erros de token do IP em request_log.
"""

from os import environ

from tests.utils import INTERNAL_TOKEN, DbUtils
from tests.utils.requisition import ClientRequisition


ADMIN_TOKEN = environ.get("ADMIN_TOKEN", "default_admin_token")

# Caminho sob /internal que nunca vira rota: com os dois tokens certos, a
# resposta é o 404 do caminho que não existe.
INTERNAL_PATH = "/internal/nao_existe"

FORBIDDEN_ADMIN_TRANSLATION = "Requisição precisa do token de administração"


class TestAdminToken:
    def test_internal_path_without_admin_token(self):
        DbUtils.rollback()

        response = ClientRequisition.send("POST", INTERNAL_PATH)
        assert response.response_status == 403
        assert response.response_json["code"] == "QIT000002"

        response = ClientRequisition.send("POST", INTERNAL_PATH, headers={"ADMIN-TOKEN": ADMIN_TOKEN})
        assert response.response_status == 403
        assert response.response_json["code"] == "QIT000002"

        response = ClientRequisition.send("POST", INTERNAL_PATH, headers={"INTERNAL-TOKEN": INTERNAL_TOKEN})
        assert response.response_status == 403
        assert response.response_json["code"] == "QIT000003"
        assert response.response_json["translation"] == FORBIDDEN_ADMIN_TRANSLATION

    def test_internal_path_with_wrong_admin_token(self):
        DbUtils.rollback()

        response = ClientRequisition.send(
            "POST",
            INTERNAL_PATH,
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN, "ADMIN-TOKEN": "token_errado"},
        )
        assert response.response_status == 403
        assert response.response_json["code"] == "QIT000003"

        response = ClientRequisition.send(
            "POST",
            INTERNAL_PATH,
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN, "ADMIN-TOKEN": INTERNAL_TOKEN},
        )
        assert response.response_status == 403
        assert response.response_json["code"] == "QIT000003"

    def test_internal_path_with_both_tokens(self):
        DbUtils.rollback()

        response = ClientRequisition.send("POST", INTERNAL_PATH, headers={"INTERNAL-TOKEN": INTERNAL_TOKEN})
        assert response.response_status == 403
        assert response.response_json["code"] == "QIT000003"

        response = ClientRequisition.send(
            "POST",
            INTERNAL_PATH,
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN, "ADMIN-TOKEN": ADMIN_TOKEN},
        )
        assert response.response_status == 404
        assert response.response_json["code"] == "QIT000404"

    def test_admin_token_only_under_internal_prefix(self):
        DbUtils.rollback()

        for path in ["/internal", "/internal/"]:
            response = ClientRequisition.send("GET", path, headers={"INTERNAL-TOKEN": INTERNAL_TOKEN})
            assert response.response_status == 403
            assert response.response_json["code"] == "QIT000003"

        for path in ["/internalx", "/nao_existe/internal"]:
            response = ClientRequisition.send("GET", path, headers={"INTERNAL-TOKEN": INTERNAL_TOKEN})
            assert response.response_status == 404
            assert response.response_json["code"] == "QIT000404"
