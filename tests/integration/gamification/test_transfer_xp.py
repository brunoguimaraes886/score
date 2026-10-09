"""XP da transferência: POST /accounts/{account_key}/transfers e GET .../gamification (GAM-01, GAM-05, GAM-06, GAM-15 a GAM-18, GAM-24).

Quem envia e quem recebe ganham (x / 4) · log10(n · 10) de XP, com
x = valor em reais e n = o próximo nível de cada um; o XP é inteiro,
truncado. Cada nível custa 1.000 × n² e dá 1 ponto livre; ao subir, o
resto do valor rende com o n novo. Depósito, saque e pedido recusado não
dão XP; o pedido repetido não dá XP de novo.
"""

from tests.utils import ObjectGenerator, PayloadGenerator, RequestGenerator


# GAM-24: R$ 4.000,00 dão exatamente os 1.000 XP do nível 1 (n = 1).
LEVEL_ONE_AMOUNT = 400000

# R$ 830.000,00 passam dos 385.000 XP dos 10 níveis e sobram 1.500 XP no nível 10.
LEVEL_TEN_AMOUNT = 83000000


def gamification_of(account: dict) -> dict:
    status, response = RequestGenerator.GET_gamification(account["account_key"], account["account_token"])
    assert status == 200, response

    return response


def progress_of(account: dict) -> tuple:
    """(nível, XP, XP que falta, pontos livres) da conta."""
    gamification = gamification_of(account)

    return gamification["level"], gamification["xp"], gamification["xp_to_next_level"], gamification["points_free"]


def transfer(origin: dict, destination: dict, amount: int) -> tuple:
    payload = PayloadGenerator.transfer(destination["account_key"], amount=amount)

    return RequestGenerator.POST_transfer(origin["account_key"], origin["account_token"], payload)


def send(origin: dict, destination: dict, amount: int) -> None:
    status, response = transfer(origin, destination, amount)
    assert status == 201, response


def create_level_one_account() -> dict:
    """Uma conta que recebeu R$ 4.000,00: nível 1, XP 0, 1 ponto livre e saldo 400000."""
    sender = ObjectGenerator.create_funded_account(LEVEL_ONE_AMOUNT + LEVEL_ONE_AMOUNT // 100)
    receiver = ObjectGenerator.create_account()
    send(sender, receiver, LEVEL_ONE_AMOUNT)

    return receiver


class TestTransferXp:
    def test_both_sides_gain_xp(self):
        origin = ObjectGenerator.create_funded_account(10100)
        destination = ObjectGenerator.create_account()

        send(origin, destination, 10000)

        assert progress_of(origin) == (0, 25, 975, 0)
        assert progress_of(destination) == (0, 25, 975, 0)

    def test_xp_is_truncated(self):
        origin = ObjectGenerator.create_funded_account(2000)
        destination = ObjectGenerator.create_account()

        send(origin, destination, 399)
        assert progress_of(origin) == (0, 0, 1000, 0)
        assert progress_of(destination) == (0, 0, 1000, 0)

        send(origin, destination, 1234)
        assert progress_of(origin) == (0, 3, 997, 0)
        assert progress_of(destination) == (0, 3, 997, 0)

    def test_each_side_uses_its_own_n(self):
        receiver = create_level_one_account()
        assert progress_of(receiver) == (1, 0, 4000, 1)

        sender = ObjectGenerator.create_funded_account(10100)
        send(sender, receiver, 10000)

        assert progress_of(sender) == (0, 25, 975, 0)
        assert progress_of(receiver) == (1, 32, 3968, 1)

    def test_level_up_carries_the_rest(self):
        origin = ObjectGenerator.create_funded_account(396000 + 3960 + 10000 + 100)
        first_destination = ObjectGenerator.create_account()
        second_destination = ObjectGenerator.create_account()

        send(origin, first_destination, 396000)
        assert progress_of(origin) == (0, 990, 10, 0)

        send(origin, second_destination, 10000)

        assert progress_of(origin) == (1, 19, 3981, 1)
        assert progress_of(first_destination) == (0, 990, 10, 0)
        assert progress_of(second_destination) == (0, 25, 975, 0)

    def test_reaches_level_ten_without_xp_cap(self):
        origin = ObjectGenerator.create_funded_account(LEVEL_TEN_AMOUNT + LEVEL_TEN_AMOUNT // 100)
        destination = ObjectGenerator.create_account()

        send(origin, destination, LEVEL_TEN_AMOUNT)

        assert progress_of(origin) == (10, 1500, None, 10)
        assert progress_of(destination) == (10, 1500, None, 10)

        send(destination, origin, 40000)

        assert progress_of(destination) == (10, 1700, None, 10)
        assert progress_of(origin) == (10, 1700, None, 10)

    def test_only_transfers_give_xp(self):
        account = ObjectGenerator.create_funded_account(100000)
        destination = ObjectGenerator.create_account()

        withdrawal = PayloadGenerator.withdrawal(amount=50000)
        status, response = RequestGenerator.POST_withdrawal(account["account_key"], account["account_token"], withdrawal)
        assert status == 201, response
        assert progress_of(account) == (0, 0, 1000, 0)

        send(account, destination, 10000)
        assert progress_of(account) == (0, 25, 975, 0)

    def test_refused_transfer_gives_no_xp(self):
        origin = ObjectGenerator.create_funded_account(10099)
        destination = ObjectGenerator.create_account()

        status, response = transfer(origin, destination, 10000)
        assert status == 422, response
        assert response["code"] == "QIT001015"
        assert progress_of(origin) == (0, 0, 1000, 0)
        assert progress_of(destination) == (0, 0, 1000, 0)

        send(origin, destination, 9000)
        assert progress_of(origin) == (0, 22, 978, 0)
        assert progress_of(destination) == (0, 22, 978, 0)

    def test_repeated_transfer_gives_xp_once(self):
        origin = ObjectGenerator.create_funded_account(20200)
        destination = ObjectGenerator.create_account()
        payload = PayloadGenerator.transfer(destination["account_key"], amount=10000)

        first_status, first_response = RequestGenerator.POST_transfer(origin["account_key"], origin["account_token"], payload)
        second_status, second_response = RequestGenerator.POST_transfer(origin["account_key"], origin["account_token"], payload)

        assert (first_status, second_status) == (201, 201), (first_response, second_response)
        assert second_response == first_response
        assert progress_of(origin) == (0, 25, 975, 0)
        assert progress_of(destination) == (0, 25, 975, 0)

    def test_new_account_after_closing_starts_from_zero(self):
        old_account = create_level_one_account()

        status, response = RequestGenerator.POST_withdrawal(
            old_account["account_key"], old_account["account_token"], PayloadGenerator.withdrawal(amount=LEVEL_ONE_AMOUNT)
        )
        assert status == 201, response

        status, response = RequestGenerator.DELETE_account(old_account["account_key"], old_account["account_token"])
        assert status == 204, response

        status, response = RequestGenerator.POST_account(old_account["customer_key"])
        assert status == 201, response
        new_account = {"account_key": response["account_key"], "account_token": response["account_token"]}

        assert progress_of(new_account) == (0, 0, 1000, 0)
        assert progress_of(old_account) == (1, 0, 4000, 1)
