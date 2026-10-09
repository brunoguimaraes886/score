"""Tarifa menor com pontos: POST /accounts/{account_key}/transfers (GAM-09, MOV-02, MOV-10, DAD-16).

Cada ponto em tarifa tira 0,1 p.p. do 1% (arredondado para cima ao
centavo); ponto em chance não muda a tarifa; com os 10 pontos em tarifa,
a tarifa é 0% e a transferência não tem lançamento FEE. O saldo precisa
cobrir valor + a tarifa já reduzida.
"""

from tests.utils import ObjectGenerator, PayloadGenerator, RequestGenerator


LEVEL_ONE_AMOUNT = 400000
LEVEL_TWO_AMOUNT = 1700000
LEVEL_TEN_AMOUNT = 83000000


def create_account_with_levels(amount: int) -> dict:
    sender = ObjectGenerator.create_funded_account(amount + amount // 100)
    receiver = ObjectGenerator.create_account()
    payload = PayloadGenerator.transfer(receiver["account_key"], amount=amount)
    status, response = RequestGenerator.POST_transfer(sender["account_key"], sender["account_token"], payload)
    assert status == 201, response
    return receiver


def apply_points(account: dict, benefit: str, points: int) -> dict:
    payload = PayloadGenerator.point_application(benefit=benefit, points=points)
    status, response = RequestGenerator.POST_point_application(account["account_key"], account["account_token"], payload)
    assert status == 200, response
    return response


def balance_of(account: dict) -> int:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response
    return response["balance"]


def transfer(origin: dict, destination: dict, amount: int) -> tuple:
    payload = PayloadGenerator.transfer(destination["account_key"], amount=amount)
    return RequestGenerator.POST_transfer(origin["account_key"], origin["account_token"], payload)


def fee_paid(origin: dict, destination: dict, amount: int) -> int:
    balance_before = balance_of(origin)
    status, response = transfer(origin, destination, amount)
    assert status == 201, response
    status, operation = RequestGenerator.GET_transaction(origin["account_key"], origin["account_token"], response["transaction_key"])
    assert status == 200, operation
    fee = balance_before - amount - response["balance"]
    entries = [(entry["entry_type"], entry["amount"]) for entry in operation["entries"]]
    if fee == 0:
        assert entries == [("AMOUNT", -amount)], entries
    else:
        assert entries == [("AMOUNT", -amount), ("FEE", -fee)], entries
    return fee


class TestFeeWithPoints:
    def test_each_fee_point_lowers_the_fee(self):
        account = create_account_with_levels(LEVEL_ONE_AMOUNT)
        destination = ObjectGenerator.create_account()
        gamification = apply_points(account, "FEE", 1)
        assert gamification["fee_percent"] == "0.9"
        assert fee_paid(account, destination, 10000) == 90
        assert fee_paid(account, destination, 1234) == 12
        assert balance_of(destination) == 10000 + 1234

    def test_only_fee_points_lower_the_fee(self):
        account = create_account_with_levels(LEVEL_TWO_AMOUNT)
        destination = ObjectGenerator.create_account()
        apply_points(account, "FEE", 1)
        assert fee_paid(account, destination, 10000) == 90
        status, response = RequestGenerator.POST_point_reset(account["account_key"], account["account_token"])
        assert status == 200, response
        assert fee_paid(account, destination, 10000) == 100
        apply_points(account, "CHANCE", 2)
        assert fee_paid(account, destination, 10000) == 100

    def test_ten_fee_points_make_the_fee_zero_without_entry(self):
        account = create_account_with_levels(LEVEL_TEN_AMOUNT)
        destination = ObjectGenerator.create_account()
        gamification = apply_points(account, "FEE", 10)
        assert (gamification["points_free"], gamification["points_fee"], gamification["fee_percent"]) == (0, 10, "0")
        assert fee_paid(account, destination, 10000) == 0
        assert balance_of(account) == LEVEL_TEN_AMOUNT - 10000
        assert balance_of(destination) == 10000

    def test_balance_must_cover_amount_plus_reduced_fee(self):
        account = create_account_with_levels(LEVEL_ONE_AMOUNT)
        destination = ObjectGenerator.create_account()
        apply_points(account, "FEE", 1)
        withdrawal = PayloadGenerator.withdrawal(amount=LEVEL_ONE_AMOUNT - 10089)
        status, response = RequestGenerator.POST_withdrawal(account["account_key"], account["account_token"], withdrawal)
        assert status == 201, response
        status, response = transfer(account, destination, 10000)
        assert status == 422, response
        assert response["code"] == "QIT001015"
        status, response = RequestGenerator.POST_deposit(account["account_key"], PayloadGenerator.deposit(amount=1))
        assert status == 201, response
        status, response = transfer(account, destination, 10000)
        assert status == 201, response
        assert response["balance"] == 0
        assert balance_of(destination) == 10000
