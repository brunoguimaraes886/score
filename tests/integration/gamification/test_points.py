"""Pontos: POST /accounts/{account_key}/point_applications e /point_resets (GAM-06, GAM-07, GAM-21, CLI-09, R8).

Cada nível dá 1 ponto livre. "Aplicar +Y" tira Y pontos dos livres e põe
no benefício FEE (tarifa menor) ou CHANCE (chance de não debitar);
faltou ponto livre → 422 QIT001027. "Zerar" devolve todos os pontos aos
livres. Conta bloqueada aplica e zera; encerrada → 409 QIT001011. A
resposta é a gamificação já atualizada. Os testes que erram o token
começam com DbUtils.rollback() (PRD-10).
"""

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator


LEVEL_ONE_AMOUNT = 400000
LEVEL_TWO_AMOUNT = 1700000


def create_account_with_levels(amount: int) -> dict:
    sender = ObjectGenerator.create_funded_account(amount + amount // 100)
    receiver = ObjectGenerator.create_account()
    payload = PayloadGenerator.transfer(receiver["account_key"], amount=amount)
    status, response = RequestGenerator.POST_transfer(sender["account_key"], sender["account_token"], payload)
    assert status == 201, response
    return receiver


def gamification_of(account: dict) -> dict:
    status, response = RequestGenerator.GET_gamification(account["account_key"], account["account_token"])
    assert status == 200, response
    return response


def points_of(gamification: dict) -> tuple:
    return (gamification["points_free"], gamification["points_fee"], gamification["points_chance"], gamification["fee_percent"], gamification["chance_percent"])


def apply_points(account: dict, benefit: str, points: int) -> tuple:
    payload = PayloadGenerator.point_application(benefit=benefit, points=points)
    return RequestGenerator.POST_point_application(account["account_key"], account["account_token"], payload)


def reset_points(account: dict) -> tuple:
    return RequestGenerator.POST_point_reset(account["account_key"], account["account_token"])


def assert_points(status: int, response: dict, account: dict, expected: tuple) -> None:
    assert status == 200, response
    assert points_of(response) == expected
    assert response == gamification_of(account)


class TestPoints:
    def test_applies_points_to_fee(self):
        account = create_account_with_levels(LEVEL_ONE_AMOUNT)
        status, response = apply_points(account, "FEE", 1)
        assert status == 200, response
        assert response == {
            "level": 1, "xp": 0, "xp_to_next_level": 4000, "points_free": 0,
            "points_fee": 1, "points_chance": 0, "fee_percent": "0.9", "chance_percent": "0",
            "rank": "DEFAULT", "cdi_percent": "100", "piggy_record": 0, "grace_until": None,
        }
        assert response == gamification_of(account)

    def test_applies_points_to_chance(self):
        account = create_account_with_levels(LEVEL_ONE_AMOUNT)
        status, response = apply_points(account, "CHANCE", 1)
        assert_points(status, response, account, (0, 0, 1, "1", "0.1"))

    def test_refuses_more_than_free_points(self):
        account = create_account_with_levels(LEVEL_ONE_AMOUNT)
        account_without_points = ObjectGenerator.create_account()
        for target, points in [(account, 2), (account_without_points, 1)]:
            status, response = apply_points(target, "FEE", points)
            assert status == 422, (points, response)
            assert response["code"] == "QIT001027"
        assert points_of(gamification_of(account)) == (1, 0, 0, "1", "0")
        assert points_of(gamification_of(account_without_points)) == (0, 0, 0, "1", "0")
        status, response = apply_points(account, "FEE", 1)
        assert_points(status, response, account, (0, 1, 0, "0.9", "0"))

    def test_applies_in_steps_and_resets(self):
        account = create_account_with_levels(LEVEL_TWO_AMOUNT)
        assert points_of(gamification_of(account)) == (2, 0, 0, "1", "0")
        status, response = apply_points(account, "FEE", 1)
        assert_points(status, response, account, (1, 1, 0, "0.9", "0"))
        status, response = apply_points(account, "CHANCE", 1)
        assert_points(status, response, account, (0, 1, 1, "0.9", "0.1"))
        status, response = apply_points(account, "FEE", 1)
        assert status == 422, response
        assert response["code"] == "QIT001027"
        for _repeat in range(2):
            status, response = reset_points(account)
            assert_points(status, response, account, (2, 0, 0, "1", "0"))
        status, response = apply_points(account, "FEE", 2)
        assert_points(status, response, account, (0, 2, 0, "0.8", "0"))

    def test_blocked_account_manages_points(self):
        account = create_account_with_levels(LEVEL_ONE_AMOUNT)
        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
        assert status == 204, response
        status, response = apply_points(account, "FEE", 1)
        assert_points(status, response, account, (0, 1, 0, "0.9", "0"))
        status, response = reset_points(account)
        assert_points(status, response, account, (1, 0, 0, "1", "0"))

    def test_closed_account_is_409(self):
        account = create_account_with_levels(LEVEL_ONE_AMOUNT)
        withdrawal = PayloadGenerator.withdrawal(amount=LEVEL_ONE_AMOUNT)
        status, response = RequestGenerator.POST_withdrawal(account["account_key"], account["account_token"], withdrawal)
        assert status == 201, response
        status, response = RequestGenerator.DELETE_account(account["account_key"], account["account_token"])
        assert status == 204, response
        for status, response in [apply_points(account, "FEE", 1), reset_points(account)]:
            assert status == 409, response
            assert response["code"] == "QIT001011"
        assert points_of(gamification_of(account)) == (1, 0, 0, "1", "0")

    def test_refuses_body_out_of_schema(self):
        account = create_account_with_levels(LEVEL_ONE_AMOUNT)
        bodies = [
            {"benefit": "fee", "points": 1}, {"benefit": "OTHER", "points": 1},
            {"benefit": "FEE", "points": 0}, {"benefit": "FEE", "points": -1},
            {"benefit": "FEE", "points": 1.5}, {"benefit": "FEE", "points": 1.0},
            {"benefit": "FEE", "points": "1"}, {"benefit": "FEE", "points": True},
            {"benefit": "FEE"}, {"points": 1}, {"benefit": "FEE", "points": 1, "extra": 1}, {},
        ]
        for body in bodies:
            status, response = RequestGenerator.POST_point_application(account["account_key"], account["account_token"], body)
            assert status == 400, (body, response)
            assert response["code"] == "QIT000001"
        assert points_of(gamification_of(account)) == (1, 0, 0, "1", "0")

    def test_other_account_token_is_404(self):
        DbUtils.rollback()
        account = create_account_with_levels(LEVEL_ONE_AMOUNT)
        other_account = ObjectGenerator.create_account()
        payload = PayloadGenerator.point_application(benefit="FEE", points=1)
        status, response = RequestGenerator.POST_point_application(account["account_key"], other_account["account_token"], payload)
        assert status == 404, response
        assert response["code"] == "QIT001010"
        status, response = RequestGenerator.POST_point_reset(account["account_key"], other_account["account_token"])
        assert status == 404, response
        assert response["code"] == "QIT001010"
        status, response = apply_points(account, "FEE", 1)
        assert_points(status, response, account, (0, 1, 0, "0.9", "0"))

    def test_missing_or_wrong_token_is_404(self):
        DbUtils.rollback()
        account = create_account_with_levels(LEVEL_ONE_AMOUNT)
        payload = PayloadGenerator.point_application(benefit="FEE", points=1)
        for account_token in [None, "token_errado"]:
            status, response = RequestGenerator.POST_point_application(account["account_key"], account_token, payload)
            assert status == 404, (account_token, response)
            assert response["code"] == "QIT001010"
            status, response = RequestGenerator.POST_point_reset(account["account_key"], account_token)
            assert status == 404, (account_token, response)
            assert response["code"] == "QIT001010"
        assert points_of(gamification_of(account)) == (1, 0, 0, "1", "0")
