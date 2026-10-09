"""Virada do dia: POST /internal/day_closings (DIA-01, DIA-02, DIA-05, COF-16, COF-20, CLI-08, PRD-13).

O relógio do banco é um só para a suíte: todo teste daqui começa com
DbUtils.rollback(), que o põe de volta em 2026-06-01 (DIA-04), e programa
no Mockserver a taxa de cada dia que fecha (MockGenerator). O dia do
relógio é lido por fora: a data contábil de um depósito feito agora.
"""

from tests.utils import DbUtils, MockGenerator, ObjectGenerator, PayloadGenerator, RequestGenerator


CDI = "0.054266"


def close_day(accounting_date: str) -> tuple:
    return RequestGenerator.POST_day_closing(PayloadGenerator.day_closing(accounting_date))


def bank_date() -> str:
    """O dia do relógio do banco, visto por fora: a data contábil de um depósito feito agora (DIA-01, DAD-17)."""
    account = ObjectGenerator.create_account()

    status, response = RequestGenerator.POST_deposit(account["account_key"], PayloadGenerator.deposit(amount=100))
    assert status == 201, response

    status, response = RequestGenerator.GET_transaction(account["account_key"], account["account_token"], response["transaction_key"])
    assert status == 200, response

    return response["accounting_date"]


def account_status(account: dict) -> str:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["status"]


def transfer(origin: dict, destination: dict, amount: int) -> tuple:
    payload = PayloadGenerator.transfer(destination["account_key"], amount=amount)

    return RequestGenerator.POST_transfer(origin["account_key"], origin["account_token"], payload)


class TestDayClosing:
    def test_closes_the_day_and_advances_the_clock(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate("2026-06-01", CDI)
        assert bank_date() == "2026-06-01"

        status, response = close_day("2026-06-01")

        assert status == 200, response
        assert response == {"closed_date": "2026-06-01", "accounting_date": "2026-06-02"}
        assert bank_date() == "2026-06-02"
        MockGenerator.clear_cdi("2026-06-01")

    def test_same_day_twice_is_409(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate("2026-06-01", CDI)
        MockGenerator.set_cdi_rate("2026-06-02", CDI)

        status, response = close_day("2026-06-01")
        assert status == 200, response

        status, response = close_day("2026-06-01")
        assert status == 409, response
        assert response["code"] == "QIT001028"
        assert bank_date() == "2026-06-02"

        status, response = close_day("2026-06-02")
        assert status == 200, response
        assert response == {"closed_date": "2026-06-02", "accounting_date": "2026-06-03"}
        MockGenerator.clear_cdi("2026-06-01")
        MockGenerator.clear_cdi("2026-06-02")

    def test_future_date_is_422(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate("2026-06-01", CDI)

        status, response = close_day("2026-06-02")
        assert status == 422, response
        assert response["code"] == "QIT001029"
        assert bank_date() == "2026-06-01"

        status, response = close_day("2026-06-01")
        assert status == 200, response
        MockGenerator.clear_cdi("2026-06-01")

    def test_impossible_date_is_422(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate("2026-06-01", CDI)

        for accounting_date in ["2026-02-30", "2026-13-01"]:
            status, response = close_day(accounting_date)
            assert status == 422, (accounting_date, response)
            assert response["code"] == "QIT001030"

        assert bank_date() == "2026-06-01"

        status, response = close_day("2026-06-01")
        assert status == 200, response
        MockGenerator.clear_cdi("2026-06-01")

    def test_day_without_cdi_rate_still_closes(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate("2026-06-01")

        status, response = close_day("2026-06-01")

        assert status == 200, response
        assert response == {"closed_date": "2026-06-01", "accounting_date": "2026-06-02"}
        MockGenerator.clear_cdi("2026-06-01")

    def test_central_bank_down_is_503_and_the_day_does_not_advance(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_delay("2026-06-01", 7)

        status, response = close_day("2026-06-01")
        assert status == 503, response
        assert response["code"] == "QIT001031"
        assert bank_date() == "2026-06-01"

        MockGenerator.set_cdi_rate("2026-06-01", CDI)
        status, response = close_day("2026-06-01")
        assert status == 200, response
        assert response == {"closed_date": "2026-06-01", "accounting_date": "2026-06-02"}
        MockGenerator.clear_cdi("2026-06-01")

    def test_automatically_blocked_account_stays_blocked(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate("2026-06-01", CDI)
        origin = ObjectGenerator.create_funded_account(100000)
        destination = ObjectGenerator.create_account()

        for _ in range(10):
            status, response = transfer(origin, destination, 100)
            assert status == 201, response

        status, response = transfer(origin, destination, 100)
        assert status == 422, response
        assert response["code"] == "QIT001019"
        assert account_status(origin) == "BLOCKED"

        status, response = close_day("2026-06-01")
        assert status == 200, response
        assert account_status(origin) == "BLOCKED"

        status, response = transfer(origin, destination, 100)
        assert status == 409, response
        assert response["code"] == "QIT001011"

        status, response = RequestGenerator.POST_unblock(origin["account_key"])
        assert status == 204, response

        status, response = transfer(origin, destination, 100)
        assert status == 201, response
        MockGenerator.clear_cdi("2026-06-01")

    def test_refuses_body_out_of_schema(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate("2026-06-01", CDI)
        payloads = [
            {},
            {"accounting_date": "2026-6-1"},
            {"accounting_date": 20260601},
            {"accounting_date": "2026-06-01", "extra": 1},
        ]

        for payload in payloads:
            status, response = RequestGenerator.POST_day_closing(payload)
            assert status == 400, (payload, response)
            assert response["code"] == "QIT000001"

        status, response = close_day("2026-06-01")
        assert status == 200, response
        MockGenerator.clear_cdi("2026-06-01")

    def test_requires_admin_token(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate("2026-06-01", CDI)
        MockGenerator.set_cdi_rate("2026-06-02", CDI)

        status, response = close_day("2026-06-01")
        assert status == 200, response

        for admin_token in [None, "token_errado"]:
            status, response = RequestGenerator.POST_day_closing(PayloadGenerator.day_closing("2026-06-02"), admin_token=admin_token)
            assert status == 403, (admin_token, response)
            assert response["code"] == "QIT000003"

        status, response = RequestGenerator.POST_day_closing(PayloadGenerator.day_closing("2026-06-02"), internal_token=None)
        assert status == 403, response
        assert response["code"] == "QIT000002"

        assert bank_date() == "2026-06-02"
        MockGenerator.clear_cdi("2026-06-01")
        MockGenerator.clear_cdi("2026-06-02")
