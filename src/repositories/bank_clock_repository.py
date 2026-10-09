from datetime import date, timedelta

from database import Context
from models import BankClock


class BankClockRepository:
    """O relógio do banco: a data contábil, numa tabela de uma linha só (DIA-01, DIA-04).

    Nenhuma regra de negócio mora aqui. Toda operação de dinheiro lê a
    data por get_accounting_date antes de travar qualquer conta; a virada
    do dia (fase 7) trava a linha por lock e muda a data por advance.
    """

    def __init__(self, context: Context) -> None:
        self.session = context.db_session

    def get_accounting_date(self) -> date:
        """O "hoje" do banco, lido com SELECT ... FOR SHARE.

        A trava compartilhada deixa várias operações lerem a data ao mesmo
        tempo e segura a virada do dia (lock, FOR UPDATE) até elas
        terminarem: nenhuma operação grava uma data que a virada já fechou.
        """
        return self.session.query(BankClock).with_for_update(read=True).one().accounting_date

    def lock(self) -> BankClock:
        """A linha do relógio, travada com SELECT ... FOR UPDATE, com os valores relidos do banco."""
        return self.session.query(BankClock).with_for_update().populate_existing().one()

    def advance(self, bank_clock: BankClock) -> date:
        """Passa o relógio travado para o dia seguinte do calendário e devolve a data nova (DIA-01)."""
        bank_clock.accounting_date = bank_clock.accounting_date + timedelta(days=1)

        return bank_clock.accounting_date
