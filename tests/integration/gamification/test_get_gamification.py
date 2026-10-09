"""Gamificação da conta: GET /accounts/{account_key}/gamification (API-14, GAM-01, GAM-02, CLI-05, R5, R8).

Só o dono vê: XP, nível e XP que falta; pontos livres, em tarifa e em
chance; tarifa e chance atuais; ranque, % do CDI, recorde do cofrinho e
fim da carência. Conta bloqueada ou encerrada continua lendo. Os testes
que erram o token começam com DbUtils.rollback() (PRD-10).
"""

from uuid import uuid4

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator


NEW_ACCOUNT_GAMIFICATION = {
    "level": 0,
    "xp": 0,
    "xp_to_next_level": 1000,
    "points_free": 0,
    "points_fee": 0,
    "points_chance": 0,
    "fee_percent": "1",
    "chance_percent": "0",
    "rank": "DEFAULT",
    "cdi_percent": "100",
    "piggy_record": 0,
    "grace_until": None,
}
INTEGER_FIELDS = ["level", "xp", "xp_to_next_level", "points_free", "points_fee", "points_chance", "piggy_record"]


def assert_no_internal_id(body) -> None:
    """R5: nenhum campo id nem terminado em _id, em nenhum nível da resposta."""
    if isinstance(body, dict):
        for field, value in body.items():
            assert field != "id", field
            assert not field.endswith("_id"), field
            assert_no_internal_id(value)

    if isinstance(body, list):
        for item in body:
            assert_no_internal_id(item)


def get_gamification(account: dict) -> tuple:
    return RequestGenerator.GET_gamification(account["account_key"], account["account_token"])


def assert_owner_reads(account: dict) -> None:
    status, response = get_gamification(account)
    assert status == 200, response


def assert_account_not_found(status: int, response: dict) -> None:
    assert status == 404, response
    assert response["code"] == "QIT001010"


class TestGetGamification:
    def test_new_account_starts_at_zero(self):
        account = ObjectGenerator.create_account()

        status, response = get_gamification(account)

        assert status == 200, response
        assert response == NEW_ACCOUNT_GAMIFICATION
        for field in INTEGER_FIELDS:
            assert type(response[field]) is int, field
        assert_no_internal_id(response)

    def test_blocked_and_closed_accounts_still_read(self):
        blocked_account = ObjectGenerator.create_account()
        status, response = RequestGenerator.POST_block(blocked_account["account_key"], PayloadGenerator.block())
        assert status == 204, response

        closed_account = ObjectGenerator.create_account()
        status, response = RequestGenerator.DELETE_account(closed_account["account_key"], closed_account["account_token"])
        assert status == 204, response

        for account in [blocked_account, closed_account]:
            status, response = get_gamification(account)

            assert status == 200, response
            assert response == NEW_ACCOUNT_GAMIFICATION

    def test_other_account_token_is_404(self):
        DbUtils.rollback()
        first = ObjectGenerator.create_account()
        second = ObjectGenerator.create_account()

        status, response = RequestGenerator.GET_gamification(first["account_key"], second["account_token"])
        assert_account_not_found(status, response)

        status, response = RequestGenerator.GET_gamification(second["account_key"], first["account_token"])
        assert_account_not_found(status, response)

        assert_owner_reads(first)

    def test_missing_or_wrong_token_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()

        for account_token in [None, "token_errado"]:
            status, response = RequestGenerator.GET_gamification(account["account_key"], account_token)
            assert_account_not_found(status, response)

        assert_owner_reads(account)

    def test_unknown_account_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()

        for account_key in [str(uuid4()), "nao-e-uma-key"]:
            status, response = RequestGenerator.GET_gamification(account_key, account["account_token"])
            assert_account_not_found(status, response)

        assert_owner_reads(account)

    def test_requires_internal_token(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()

        assert_owner_reads(account)

        status, response = RequestGenerator.GET_gamification(account["account_key"], account["account_token"], internal_token=None)

        assert status == 403, response
        assert response["code"] == "QIT000002"
