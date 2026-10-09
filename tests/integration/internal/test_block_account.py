"""Bloquear e desbloquear conta pelas rotas internas."""

from uuid import uuid4

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator


BLOCK_REASONS = ["SUSPICIOUS_ACTIVITY", "JUDICIAL_ORDER", "CUSTOMER_REQUEST", "MANUAL_REVIEW"]


def account_status(account: dict) -> str:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response
    return response["status"]


def block(account: dict) -> None:
    status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
    assert status == 204, response
    assert response is None


class TestBlockAccount:
    def test_blocks_and_unblocks(self):
        account = ObjectGenerator.create_account()
        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block("JUDICIAL_ORDER"))
        assert status == 204, response
        assert response is None
        assert account_status(account) == "BLOCKED"
        status, response = RequestGenerator.POST_unblock(account["account_key"])
        assert status == 204, response
        assert response is None
        assert account_status(account) == "ACTIVE"

    def test_accepts_every_reason(self):
        for reason in BLOCK_REASONS:
            account = ObjectGenerator.create_account()
            status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block(reason))
            assert status == 204, (reason, response)
            assert account_status(account) == "BLOCKED"

    def test_block_requires_active_account(self):
        account = ObjectGenerator.create_account()
        block(account)
        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
        assert status == 409, response
        assert response["code"] == "QIT001011"
        assert account_status(account) == "BLOCKED"

    def test_unblock_requires_blocked_account(self):
        account = ObjectGenerator.create_account()
        status, response = RequestGenerator.POST_unblock(account["account_key"])
        assert status == 409, response
        assert response["code"] == "QIT001013"
        assert account_status(account) == "ACTIVE"

    def test_unknown_account_is_404(self):
        for account_key in [str(uuid4()), "nao-e-uma-key"]:
            status, response = RequestGenerator.POST_block(account_key, PayloadGenerator.block())
            assert status == 404, (account_key, response)
            assert response["code"] == "QIT001010"
            status, response = RequestGenerator.POST_unblock(account_key)
            assert status == 404, (account_key, response)
            assert response["code"] == "QIT001010"

    def test_requires_admin_token(self):
        DbUtils.rollback()
        blocked_account = ObjectGenerator.create_account()
        active_account = ObjectGenerator.create_account()
        block(blocked_account)
        for admin_token in [None, "token_errado"]:
            status, response = RequestGenerator.POST_block(active_account["account_key"], PayloadGenerator.block(), admin_token=admin_token)
            assert status == 403, (admin_token, response)
            assert response["code"] == "QIT000003"
            status, response = RequestGenerator.POST_unblock(blocked_account["account_key"], admin_token=admin_token)
            assert status == 403, (admin_token, response)
            assert response["code"] == "QIT000003"
        assert account_status(active_account) == "ACTIVE"
        assert account_status(blocked_account) == "BLOCKED"

    def test_refuses_body_out_of_schema(self):
        account = ObjectGenerator.create_account()
        payloads = [{"reason": "OUTRO_MOTIVO"}, {"reason": "manual_review"}, {"reason": "MANUAL_REVIEW", "extra": 1}, {}]
        for payload in payloads:
            status, response = RequestGenerator.POST_block(account["account_key"], payload)
            assert status == 400, (payload, response)
            assert response["code"] == "QIT000001"
        assert account_status(account) == "ACTIVE"

    def test_blocked_account_still_reads(self):
        account = ObjectGenerator.create_account()
        block(account)
        status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
        assert status == 200, response
        assert response["status"] == "BLOCKED"
        assert response["balance"] == 0
        status, response = RequestGenerator.GET_customer(account["customer_key"], account["account_token"])
        assert status == 200, response
        assert response["customer_key"] == account["customer_key"]
