import pytest

from tests.utils import ObjectGenerator, PayloadGenerator, RequestGenerator


@pytest.mark.parametrize("invalid", ["\u0000", "\ud800", "\udfff"], ids=["nul", "high-surrogate", "low-surrogate"])
@pytest.mark.parametrize("field", ["name", "email"])
def test_customer_invalid_text_is_refused_without_registration(field, invalid):
    payload = PayloadGenerator.customer()
    valid = payload[field]
    payload[field] = invalid + valid
    status, body = RequestGenerator.POST_customer(payload)
    assert status == 400, body
    assert body["code"] == "QIT000001"
    payload[field] = valid
    status, body = RequestGenerator.POST_customer(payload)
    assert status == 201, body


@pytest.mark.parametrize("invalid", ["\u0000", "\ud800", "\udfff"], ids=["nul", "high-surrogate", "low-surrogate"])
def test_category_and_deposit_invalid_text_leave_no_financial_effect(invalid):
    account = ObjectGenerator.create_account()
    key, token = account["account_key"], account["account_token"]
    status, body = RequestGenerator.POST_category(key, token, PayloadGenerator.category("objetivo" + invalid))
    assert status == 400, body
    assert body["code"] == "QIT000001"
    status, body = RequestGenerator.GET_categories(key, token)
    assert status == 200, body
    assert [category["name"] for category in body["data"]] == ["economias"]
    payload = PayloadGenerator.deposit(amount=100, depositor_name="depositante" + invalid)
    status, body = RequestGenerator.POST_deposit(key, payload)
    assert status == 400, body
    assert body["code"] == "QIT000001"
    status, body = RequestGenerator.GET_account(key, token)
    assert status == 200, body
    assert body["balance"] == 0
    payload["depositor_name"] = "José D'Ávila 💰"
    status, body = RequestGenerator.POST_deposit(key, payload)
    assert status == 201, body
    status, body = RequestGenerator.GET_entries(key, token)
    assert status == 200, body
    assert len(body["data"]) == 1
    assert body["data"][0]["counterparty"]["name"] == payload["depositor_name"]


def test_valid_unicode_round_trips_and_invalid_block_reason_preserves_state():
    name = "José D'Ávila 🏦"
    account = ObjectGenerator.create_account(ObjectGenerator.create_customer(name=name))
    key, token = account["account_key"], account["account_token"]
    status, body = RequestGenerator.GET_customer(account["customer_key"], token)
    assert status == 200, body
    assert body["name"] == name
    status, body = RequestGenerator.POST_category(key, token, PayloadGenerator.category(name))
    assert status == 201, body
    status, body = RequestGenerator.GET_category(key, token, body["category_key"])
    assert status == 200, body
    assert body["name"] == name
    for invalid in ["\u0000", "\ud800", "\udfff"]:
        status, body = RequestGenerator.POST_block(key, PayloadGenerator.block("MANUAL_REVIEW" + invalid))
        assert status == 400, body
        assert body["code"] == "QIT000001"
    status, body = RequestGenerator.GET_account(key, token)
    assert status == 200, body
    assert body["status"] == "ACTIVE"
    status, body = RequestGenerator.POST_block(key, PayloadGenerator.block())
    assert status == 204, body
