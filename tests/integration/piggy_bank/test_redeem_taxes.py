"""IOF e IR no resgate: POST /accounts/{account_key}/redemptions depois da virada (COF-08, COF-12, COF-24, COF-25, MOV-12, MOV-19).

O imposto incide só sobre o rendimento que sai de cada lote, pelo prazo
do lote em dias do relógio do banco: IOF regressivo nos primeiros 29 dias;
IR de 22,5% até 180 dias, sobre o rendimento menos o IOF. Cada imposto é
arredondado uma vez, no total do resgate, para cima, e nunca passa do
rendimento. No extrato da conta, o resgate é uma linha só, com o líquido;
o bruto, o IOF e o IR saem na resposta e na consulta da operação.

CDI de teste: 1% ao dia (R$ 1.000,00 rendem R$ 10,00), para números
redondos. Todo teste começa com DbUtils.rollback() (o relógio volta a
2026-06-01) e programa no Mockserver a taxa de cada dia que fecha.
"""

from datetime import date, timedelta
from uuid import uuid4

from tests.utils import DbUtils, MockGenerator, ObjectGenerator, PayloadGenerator, RequestGenerator


ONE_PERCENT = "1.000000"
FIRST_DAY = date(2026, 6, 1)


def day(offset: int) -> str:
    """2026-06-01 + offset dias, em texto: o relógio começa em 2026-06-01 depois do DbUtils.rollback() (DIA-04)."""
    return (FIRST_DAY + timedelta(days=offset)).isoformat()


def close_day(accounting_date: str) -> None:
    status, response = RequestGenerator.POST_day_closing(PayloadGenerator.day_closing(accounting_date))
    assert status == 200, response


def save(account: dict, amount: int) -> None:
    status, response = RequestGenerator.POST_saving(account["account_key"], account["account_token"], PayloadGenerator.saving(amount=amount))
    assert status == 201, response


def redeem(account: dict, amount: int, request_control_key: str = None) -> dict:
    payload = PayloadGenerator.redemption(amount=amount, request_control_key=request_control_key)
    status, response = RequestGenerator.POST_redemption(account["account_key"], account["account_token"], payload)
    assert status == 201, response

    return response


def amounts_of(redemption: dict) -> tuple:
    """(bruto, IOF, IR, líquido)."""
    return redemption["gross_amount"], redemption["iof"], redemption["ir"], redemption["net_amount"]


def balances_of(account: dict) -> tuple:
    """(saldo da conta, saldo do cofrinho)."""
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["balance"], response["piggy_bank_balance"]


def redemption_lines(account: dict) -> list:
    """(tipo de lançamento, valor) das linhas de resgate no extrato da conta principal."""
    status, response = RequestGenerator.GET_entries(account["account_key"], account["account_token"], {"limit": "100"})
    assert status == 200, response

    return [(entry["entry_type"], entry["amount"]) for entry in response["data"] if entry["transaction_type"] == "REDEEM"]


def create_account_with_one_day_yield() -> dict:
    """Uma conta que guardou R$ 1.000,00 em 2026-06-01; depois da virada desse dia, o lote tem 100000 + 1000 de rendimento, com 1 dia de prazo."""
    account = ObjectGenerator.create_funded_account(100000)
    save(account, 100000)
    close_day(day(0))
    assert balances_of(account) == (0, 101000)

    return account


class TestRedeemTaxes:
    def test_one_day_lot_pays_iof_and_ir_on_the_yield(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0), ONE_PERCENT)
        account = create_account_with_one_day_yield()

        request_control_key = str(uuid4())
        redemption = redeem(account, 101000, request_control_key)

        assert amounts_of(redemption) == (101000, 960, 9, 100031)
        assert (redemption["balance"], redemption["piggy_bank_balance"]) == (100031, 0)
        assert balances_of(account) == (100031, 0)
        assert redemption_lines(account) == [("AMOUNT", 100031)]

        status, operation = RequestGenerator.GET_transaction(account["account_key"], account["account_token"], redemption["transaction_key"])
        assert status == 200, operation
        assert amounts_of(operation) == (101000, 960, 9, 100031)
        assert [(entry["entry_type"], entry["amount"]) for entry in operation["entries"]] == [("AMOUNT", -101000), ("AMOUNT", 100031)]

        assert redeem(account, 101000, request_control_key) == redemption
        assert balances_of(account) == (100031, 0)
        MockGenerator.clear_cdi(day(0))

    def test_partial_redemption_taxes_only_the_yield_part(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0), ONE_PERCENT)
        account = create_account_with_one_day_yield()

        first = redeem(account, 50500)
        assert amounts_of(first) == (50500, 480, 5, 50015)
        assert balances_of(account) == (50015, 50500)

        second = redeem(account, 50500)
        assert amounts_of(second) == (50500, 480, 5, 50015)
        assert balances_of(account) == (100030, 0)
        MockGenerator.clear_cdi(day(0))

    def test_each_lot_pays_by_its_own_term(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0), ONE_PERCENT)
        MockGenerator.set_cdi_rate(day(1), ONE_PERCENT)
        account = ObjectGenerator.create_funded_account(100000)

        save(account, 50000)
        close_day(day(0))
        save(account, 50000)
        close_day(day(1))
        assert balances_of(account) == (0, 101505)

        redemption = redeem(account, 101505)

        assert amounts_of(redemption) == (101505, 1415, 21, 100069)
        assert balances_of(account) == (100069, 0)
        MockGenerator.clear_cdi(day(0))
        MockGenerator.clear_cdi(day(1))

    def test_no_iof_from_thirty_days(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0), ONE_PERCENT)
        for offset in range(1, 30):
            MockGenerator.set_cdi_rate(day(offset))

        account = create_account_with_one_day_yield()
        for offset in range(1, 30):
            close_day(day(offset))

        assert balances_of(account) == (0, 101000)

        redemption = redeem(account, 101000)

        assert amounts_of(redemption) == (101000, 0, 225, 100775)
        assert balances_of(account) == (100775, 0)
        for offset in range(30):
            MockGenerator.clear_cdi(day(offset))

    def test_tax_can_take_the_whole_yield_of_a_tiny_redemption(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0), ONE_PERCENT)
        account = create_account_with_one_day_yield()

        request_control_key = str(uuid4())
        redemption = redeem(account, 1, request_control_key)

        assert amounts_of(redemption) == (1, 1, 0, 0)
        assert (redemption["balance"], redemption["piggy_bank_balance"]) == (0, 100999)
        assert balances_of(account) == (0, 100999)
        assert redemption_lines(account) == []

        assert redeem(account, 1, request_control_key) == redemption
        MockGenerator.clear_cdi(day(0))
