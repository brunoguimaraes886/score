from datetime import date

from connectors import BcbConnector
from controllers.base_controller import BaseController
from errors import DayAlreadyClosed, FutureAccountingDate, InvalidAccountingDate
from repositories import BankClockRepository


class DayClosingController(BaseController):
    """A virada do dia (DIA-01 a DIA-05): uma transação só, tudo ou nada.

    Ordem (DIA-03): pede a taxa do CDI → rendimento por lote (7.12) → XP
    de recorde (7.13) → ranques e carência, e o ranque que rende amanhã
    (7.14) → avança a data.
    """

    def __init__(self) -> None:
        super().__init__(__name__)
        self.bank_clock_repository = BankClockRepository(self.context)
        self.bcb_connector = BcbConnector()

    def close_day(self, day_closing_data: dict) -> dict:
        accounting_date = day_closing_data["accounting_date"]
        closing_date = self._parse_accounting_date(accounting_date)
        bank_clock = self.bank_clock_repository.lock()

        if closing_date < bank_clock.accounting_date:
            raise DayAlreadyClosed(accounting_date)

        if closing_date > bank_clock.accounting_date:
            raise FutureAccountingDate(accounting_date, bank_clock.accounting_date.isoformat())

        self.bcb_connector.get_cdi_rate(closing_date)

        new_date = self.bank_clock_repository.advance(bank_clock)
        self.logger.info("day_closing_ready_to_commit accounting_date=%s", closing_date)
        self.session.commit()

        return {"closed_date": closing_date.isoformat(), "accounting_date": new_date.isoformat()}

    def _parse_accounting_date(self, accounting_date: str) -> date:
        try:
            return date.fromisoformat(accounting_date)
        except ValueError:
            raise InvalidAccountingDate(accounting_date) from None
