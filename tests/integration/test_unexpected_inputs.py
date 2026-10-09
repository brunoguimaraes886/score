from uuid import uuid4

from tests.utils import ADMIN_TOKEN, DbUtils, INTERNAL_TOKEN, ObjectGenerator, PayloadGenerator, RequestGenerator
from tests.utils.requisition import ClientRequisition


def headers(account):
    return {"INTERNAL-TOKEN": INTERNAL_TOKEN, "ADMIN-TOKEN": ADMIN_TOKEN, "ACCOUNT-TOKEN": account["account_token"]}


def expect_error(response, status, code):
    assert response.response_status == status, response.response_json
    assert response.response_json["code"] == code


class TestUnexpectedInputs:
    def test_routes_without_body_reject_even_empty_json(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()
        key, token = account["account_key"], account["account_token"]
        category = RequestGenerator.GET_categories(key, token)[1]["data"][0]["category_key"]
        routes = [("GET", f"/accounts/{key}"), ("GET", "/"), ("GET", "/health_check"),
                  ("GET", f"/customers/{account['customer_key']}"),
                  ("GET", f"/accounts/{key}/entries"), ("GET", f"/accounts/{key}/piggy_bank_entries"),
                  ("GET", f"/accounts/{key}/gamification"), ("GET", f"/accounts/{key}/categories"),
                  ("GET", f"/accounts/{key}/categories/{category}"),
                  ("DELETE", f"/accounts/{key}"), ("DELETE", f"/accounts/{key}/categories/{category}"),
                  ("POST", f"/accounts/{key}/point_resets"),
                  ("POST", f"/customers/{account['customer_key']}/accounts"),
                  ("POST", f"/internal/accounts/{key}/unblocks")]
        for method, path in routes:
            expect_error(ClientRequisition.send(method, path, payload={}, headers=headers(account)), 400, "QIT000001")
        assert RequestGenerator.GET_account(key, token)[1]["status"] == "ACTIVE"

    def test_routes_without_query_reject_any_parameter(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()
        key, token = account["account_key"], account["account_token"]
        destination = ObjectGenerator.create_account()
        routes = [("GET", f"/accounts/{key}", None), ("GET", "/health_check", None),
                  ("POST", f"/accounts/{key}/deposits", PayloadGenerator.deposit(amount=1)),
                  ("POST", f"/accounts/{key}/withdrawals", PayloadGenerator.withdrawal(amount=1)),
                  ("POST", f"/accounts/{key}/transfers", PayloadGenerator.transfer(destination["account_key"], amount=1)),
                  ("POST", f"/accounts/{key}/savings", PayloadGenerator.saving(amount=1)),
                  ("POST", f"/accounts/{key}/redemptions", PayloadGenerator.redemption(amount=1)),
                  ("POST", f"/accounts/{key}/categories", PayloadGenerator.category())]
        for method, path, payload in routes:
            expect_error(ClientRequisition.send(method, path, payload=payload, query_params={"unexpected": "1"}, headers=headers(account)), 400, "QIT000001")
        assert RequestGenerator.GET_account(key, token)[1]["balance"] == 0

    def test_authentication_and_unknown_route_or_method_keep_precedence(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()
        key = account["account_key"]
        bad_headers = headers(account)
        bad_headers["INTERNAL-TOKEN"] = "wrong"
        expect_error(ClientRequisition.send("GET", f"/accounts/{key}", payload={}, headers=bad_headers), 403, "QIT000002")
        bad_headers = headers(account)
        bad_headers["ACCOUNT-TOKEN"] = "wrong"
        expect_error(ClientRequisition.send("GET", f"/accounts/{key}", payload={}, headers=bad_headers), 404, "QIT001010")
        expect_error(ClientRequisition.send("GET", f"/accounts/{uuid4()}", payload={}, headers=headers(account)), 404, "QIT001010")
        expect_error(ClientRequisition.send("GET", "/unknown-route", payload={}, headers=headers(account)), 404, "QIT000404")
        expect_error(ClientRequisition.send("PUT", f"/accounts/{key}", payload={}, headers=headers(account)), 405, "QIT000405")
