import pytest

from tests.utils import ADMIN_TOKEN, DbUtils, INTERNAL_TOKEN, PayloadGenerator, RequestGenerator
from tests.utils.requisition import ClientRequisition


@pytest.mark.parametrize("body", [b'{"name":"\xff"}', b'[' * 2000 + b'0' + b']' * 2000, b'{"name":'],
                         ids=["invalid-utf8", "deep-json", "incomplete-json"])
def test_invalid_json_is_a_standard_400(body):
    response = ClientRequisition.send(
        "POST", "/customers", data=body,
        headers={"INTERNAL-TOKEN": INTERNAL_TOKEN, "Content-Type": "application/json", "X-Request-ID": "parsing-error"},
    )
    assert response.response_status == 400
    assert response.response_json["code"] == "QIT000001"
    assert set(response.response_json) == {"title", "description", "translation", "code"}
    assert response.response_json["title"] == "Bad Request"
    assert response.response_json["translation"] == "Payload Inválido"
    assert response.response.headers["X-Request-ID"] == "parsing-error"


def test_parsing_preserves_valid_registration_and_route_errors():
    status, body = RequestGenerator.POST_customer(PayloadGenerator.customer())
    assert status == 201, body
    for method, endpoint, status, code in [
        ("GET", "/unknown", 404, "QIT000404"),
        ("PUT", "/customers", 405, "QIT000405"),
    ]:
        response = ClientRequisition.send(method, endpoint, headers={"INTERNAL-TOKEN": INTERNAL_TOKEN})
        assert response.response_status == status
        assert response.response_json["code"] == code


def test_parsing_preserves_token_checks():
    DbUtils.rollback()
    for endpoint, headers, code in [
        ("/customers", {}, "QIT000002"),
        ("/internal/day_closings", {"INTERNAL-TOKEN": INTERNAL_TOKEN}, "QIT000003"),
    ]:
        response = ClientRequisition.send("POST", endpoint, data=b'{"name":', headers=headers)
        assert response.response_status == 403
        assert response.response_json["code"] == code
    response = ClientRequisition.send(
        "POST", "/internal/day_closings", data=b'{"name":',
        headers={"INTERNAL-TOKEN": INTERNAL_TOKEN, "ADMIN-TOKEN": ADMIN_TOKEN, "Content-Type": "application/json"},
    )
    assert response.response_status == 400
    assert response.response_json["code"] == "QIT000001"
