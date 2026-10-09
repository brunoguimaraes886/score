"""Chance de não debitar: POST /accounts/{account_key}/transfers com pontos em chance (GAM-10, GAM-22, GAM-23, MOV-12, TST-06).

O sorteio usa o gerador do sistema operacional: por HTTP, o teste não
escolhe o resultado. Cada teste confere o que vale nos dois resultados
(TST-06): sem prêmio, a origem paga valor + tarifa; com prêmio, a conta do
banco devolve valor + tarifa num lançamento PRIZE, e a origem fica com o
saldo de antes. Nos dois, o destino recebe o valor e a origem ganha o
mesmo XP: o prêmio não dá XP. A prova com o resultado escolhido é a
conferência P1 do passo 9.8, com gerador falso.
"""

from tests.utils import ObjectGenerator, PayloadGenerator, RequestGenerator


# GAM-24: R$ 830.000,00 recebidos levam ao nível 10, com os 10 pontos livres.
LEVEL_TEN_AMOUNT = 83000000

# GAM-22: o maior valor que concorre ao sorteio; a tarifa dele, sem pontos em tarifa, é 100.
PRIZE_LIMIT = 10000
PRIZE_LIMIT_FEE = 100

# GAM-16: no nível 10 (n = 10), R$ 100,00 dão (100 / 4) · log10(100) = 50 XP.
PRIZE_LIMIT_XP = 50


def create_level_ten_account() -> dict:
    """Uma conta que recebeu R$ 830.000,00: nível 10, 10 pontos livres e saldo 83000000."""
    sender = ObjectGenerator.create_funded_account(LEVEL_TEN_AMOUNT + LEVEL_TEN_AMOUNT // 100)
    receiver = ObjectGenerator.create_account()

    payload = PayloadGenerator.transfer(receiver["account_key"], amount=LEVEL_TEN_AMOUNT)
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


def xp_of(account: dict) -> int:
    status, response = RequestGenerator.GET_gamification(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["xp"]


def origin_entries(account: dict, transaction_key: str) -> list:
    """(tipo, valor) de cada lançamento da operação na conta, na ordem em que foram gravados."""
    status, response = RequestGenerator.GET_transaction(account["account_key"], account["account_token"], transaction_key)
    assert status == 200, response

    return [(entry["entry_type"], entry["amount"]) for entry in response["entries"]]


def send_and_check(origin: dict, destination: dict, amount: int, fee: int) -> bool:
    """Transfere `amount` e confere os dois resultados possíveis do sorteio. Devolve True quando o prêmio saiu."""
    balance_before = balance_of(origin)
    destination_before = balance_of(destination)
    xp_before = xp_of(origin)

    payload = PayloadGenerator.transfer(destination["account_key"], amount=amount)
    status, response = RequestGenerator.POST_transfer(origin["account_key"], origin["account_token"], payload)
    assert status == 201, response

    entries = origin_entries(origin, response["transaction_key"])
    charged = [("AMOUNT", -amount), ("FEE", -fee)]
    returned = charged + [("PRIZE", amount + fee)]

    assert entries in [charged, returned], entries
    prize_won = entries == returned

    if prize_won:
        assert response["balance"] == balance_before
    else:
        assert response["balance"] == balance_before - amount - fee

    assert balance_of(origin) == response["balance"]
    assert balance_of(destination) == destination_before + amount
    assert xp_of(origin) - xp_before == PRIZE_LIMIT_XP * amount // PRIZE_LIMIT

    return prize_won


class TestChance:
    def test_transfer_up_to_the_limit_is_charged_or_returned_whole(self):
        origin = create_level_ten_account()
        destination = ObjectGenerator.create_account()

        gamification = apply_points(origin, "CHANCE", 10)
        assert (gamification["points_chance"], gamification["chance_percent"], gamification["fee_percent"]) == (10, "1", "1")

        for _ in range(5):
            send_and_check(origin, destination, PRIZE_LIMIT, PRIZE_LIMIT_FEE)

        assert balance_of(destination) == 5 * PRIZE_LIMIT

    def test_transfer_above_the_limit_is_always_charged(self):
        origin = create_level_ten_account()
        destination = ObjectGenerator.create_account()
        apply_points(origin, "CHANCE", 10)

        for _ in range(5):
            assert send_and_check(origin, destination, PRIZE_LIMIT + 1, PRIZE_LIMIT_FEE + 1) is False

    def test_without_chance_points_is_always_charged(self):
        origin = create_level_ten_account()
        destination = ObjectGenerator.create_account()

        for _ in range(5):
            assert send_and_check(origin, destination, PRIZE_LIMIT, PRIZE_LIMIT_FEE) is False

    def test_refused_transfer_never_reaches_the_draw(self):
        origin = create_level_ten_account()
        destination = ObjectGenerator.create_account()
        apply_points(origin, "CHANCE", 10)

        withdrawal = PayloadGenerator.withdrawal(amount=LEVEL_TEN_AMOUNT - PRIZE_LIMIT - PRIZE_LIMIT_FEE + 1)
        status, response = RequestGenerator.POST_withdrawal(origin["account_key"], origin["account_token"], withdrawal)
        assert status == 201, response
        assert balance_of(origin) == PRIZE_LIMIT + PRIZE_LIMIT_FEE - 1

        for _ in range(5):
            payload = PayloadGenerator.transfer(destination["account_key"], amount=PRIZE_LIMIT)
            status, response = RequestGenerator.POST_transfer(origin["account_key"], origin["account_token"], payload)
            assert status == 422, response
            assert response["code"] == "QIT001015"

        assert balance_of(origin) == PRIZE_LIMIT + PRIZE_LIMIT_FEE - 1
        assert balance_of(destination) == 0

    def test_repeated_transfer_returns_the_first_response(self):
        origin = create_level_ten_account()
        destination = ObjectGenerator.create_account()
        apply_points(origin, "CHANCE", 10)

        payload = PayloadGenerator.transfer(destination["account_key"], amount=PRIZE_LIMIT)
        status, first = RequestGenerator.POST_transfer(origin["account_key"], origin["account_token"], payload)
        assert status == 201, first

        xp_after_first = xp_of(origin)

        for _ in range(3):
            status, response = RequestGenerator.POST_transfer(origin["account_key"], origin["account_token"], payload)
            assert status == 201, response
            assert response == first

        assert balance_of(origin) == first["balance"]
        assert balance_of(destination) == PRIZE_LIMIT
        assert xp_of(origin) == xp_after_first
