"""Barreira contra chute do token da conta (PRD-10, PRD-04)."""

from os import environ

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator


AUTH_FAILURE_LIMIT = int(environ.get("AUTH_FAILURE_LIMIT", "10"))
WRONG_TOKEN = "token_errado"
TOO_MANY_TRANSLATION = "Tentativas demais com token errado. Tente de novo mais tarde."


def fail_account_token(account: dict, times: int, account_token: str = WRONG_TOKEN) -> None:
    for _ in range(times):
        status, response = RequestGenerator.GET_account(account["account_key"], account_token)
        assert status == 404, response
        assert response["code"] == "QIT001010"


def assert_not_blocked(account: dict) -> None:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response


def assert_blocked(account: dict) -> None:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 429, response
    assert response["code"] == "QIT000429"
    assert response["translation"] == TOO_MANY_TRANSLATION


class TestAccountAuthBarrier:
    def test_limit_of_account_failures_blocks_the_account(self):
        DbUtils.rollback()
        try:
            account = ObjectGenerator.create_account()
            fail_account_token(account, AUTH_FAILURE_LIMIT)
            assert_blocked(account)
            status, response = RequestGenerator.DELETE_account(account["account_key"], account["account_token"])
            assert status == 429, response
            assert response["code"] == "QIT000429"
            status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
            assert status == 429, response
            assert response["code"] == "QIT000429"
        finally:
            DbUtils.rollback()

    def test_one_failure_below_the_limit_does_not_block(self):
        DbUtils.rollback()
        try:
            account = ObjectGenerator.create_account()
            fail_account_token(account, AUTH_FAILURE_LIMIT - 1)
            assert_not_blocked(account)
            fail_account_token(account, 1)
            assert_blocked(account)
        finally:
            DbUtils.rollback()

    def test_missing_token_counts_as_failure(self):
        DbUtils.rollback()
        try:
            account = ObjectGenerator.create_account()
            fail_account_token(account, AUTH_FAILURE_LIMIT, account_token=None)
            assert_blocked(account)
        finally:
            DbUtils.rollback()

    def test_barrier_is_per_account(self):
        DbUtils.rollback()
        try:
            blocked_account = ObjectGenerator.create_account()
            other_account = ObjectGenerator.create_account()
            fail_account_token(blocked_account, AUTH_FAILURE_LIMIT)
            assert_blocked(blocked_account)
            assert_not_blocked(other_account)
            status, response = RequestGenerator.POST_customer(PayloadGenerator.customer())
            assert status == 201, response
        finally:
            DbUtils.rollback()

    def test_successful_requests_do_not_count(self):
        DbUtils.rollback()
        try:
            account = ObjectGenerator.create_account()
            for _ in range(2 * AUTH_FAILURE_LIMIT):
                assert_not_blocked(account)
            fail_account_token(account, AUTH_FAILURE_LIMIT - 1)
            assert_not_blocked(account)
            fail_account_token(account, 1)
            assert_blocked(account)
        finally:
            DbUtils.rollback()
