from datetime import date, timedelta

from calculations import GRACE_DAYS, RANK_CDI_PERCENT, RANK_ORDER, daily_rate, lot_yield, rank_for_balance
from connectors import BcbConnector
from controllers.base_controller import BaseController
from controllers.gamification_controller import GamificationController
from errors import DayAlreadyClosed, FutureAccountingDate, InvalidAccountingDate
from models import Account, AccountStatus, AccountType, EntryType, RankEvent, TransactionType
from repositories import AccountRepository, BankClockRepository, CategoryRepository, EntryRepository, GamificationRepository, LotRepository, TransactionRepository


class DayClosingController(BaseController):
    """A virada diária, uma transação só, tudo ou nada."""

    def __init__(self) -> None:
        super().__init__(__name__)
        self.account_repository = AccountRepository(self.context)
        self.bank_clock_repository = BankClockRepository(self.context)
        self.category_repository = CategoryRepository(self.context)
        self.entry_repository = EntryRepository(self.context)
        self.gamification_repository = GamificationRepository(self.context)
        self.lot_repository = LotRepository(self.context)
        self.transaction_repository = TransactionRepository(self.context)
        self.bcb_connector = BcbConnector()
        self.gamification_controller = GamificationController()

    def close_day(self, day_closing_data: dict) -> dict:
        accounting_date = day_closing_data["accounting_date"]
        closing_date = self._parse_accounting_date(accounting_date)
        bank_clock = self.bank_clock_repository.lock()
        if closing_date < bank_clock.accounting_date:
            raise DayAlreadyClosed(accounting_date)
        if closing_date > bank_clock.accounting_date:
            raise FutureAccountingDate(accounting_date, bank_clock.accounting_date.isoformat())
        cdi_rate = self.bcb_connector.get_cdi_rate(closing_date)
        bank = self.account_repository.get_system_account(AccountType.BANK)
        for customer_account in self.account_repository.list_open_customer_accounts():
            account, piggy_bank = self._lock_account_and_piggy_bank(customer_account)
            if account.status.enumerator == AccountStatus.CLOSED:
                continue
            if cdi_rate is not None:
                self._pay_yield(account, piggy_bank, bank, cdi_rate, closing_date)
            self.gamification_controller.award_record_xp(account, None, closing_date)
            self._update_rank(account, piggy_bank, closing_date)
        new_date = self.bank_clock_repository.advance(bank_clock)
        self.logger.info("day_closing_ready_to_commit accounting_date=%s", closing_date)
        self.session.commit()
        return {"closed_date": closing_date.isoformat(), "accounting_date": new_date.isoformat()}

    def _pay_yield(self, account: Account, piggy_bank: Account, bank: Account, cdi_rate: str, closing_date: date) -> None:
        rate = daily_rate(cdi_rate, RANK_CDI_PERCENT[account.yield_rank.enumerator])
        yield_by_category = {}
        for lot in self.lot_repository.list_open_by_piggy_bank_for_update(piggy_bank):
            cents, residue = lot_yield(lot.principal_remaining + lot.yield_remaining, lot.residue, rate)
            self.check_numeric_limits(lot.principal_remaining + lot.yield_remaining + cents,
                                      lot.yield_remaining + cents,
                                      piggy_bank.balance + sum(yield_by_category.values()) + cents)
            self.lot_repository.update_remaining(lot, lot.principal_remaining, lot.yield_remaining + cents, residue)
            yield_by_category[lot.category_id] = yield_by_category.get(lot.category_id, 0) + cents
        category_ids = [category_id for category_id in sorted(yield_by_category) if yield_by_category[category_id] > 0]
        if len(category_ids) == 0:
            return
        transaction = self.transaction_repository.create(TransactionType.YIELD, None, None, closing_date)
        for category_id in category_ids:
            category = self.category_repository.get_by_id(category_id)
            cents = yield_by_category[category_id]
            self.entry_repository.create(transaction, bank, EntryType.YIELD, -cents)
            self.entry_repository.create(transaction, piggy_bank, EntryType.YIELD, cents, category)

    def _lock_account_and_piggy_bank(self, account: Account) -> tuple:
        piggy_bank = self.account_repository.get_piggy_bank(account)
        locked_accounts = {locked.id: locked for locked in self.account_repository.lock_accounts([account, piggy_bank])}
        return locked_accounts[account.id], locked_accounts[piggy_bank.id]

    def _update_rank(self, account: Account, piggy_bank: Account, closing_date: date) -> None:
        current_rank = account.rank.enumerator
        balance_rank = rank_for_balance(piggy_bank.balance)
        if RANK_ORDER.index(balance_rank) > RANK_ORDER.index(current_rank):
            self.gamification_controller.raise_rank(account, piggy_bank, closing_date)
        elif balance_rank == current_rank:
            if account.grace_until is not None:
                self.gamification_repository.update_rank(account, current_rank, None)
                self.gamification_repository.create_rank_event(account, current_rank, RankEvent.GRACE_END, closing_date)
        elif account.grace_until is None:
            self.gamification_repository.update_rank(account, current_rank, closing_date + timedelta(days=GRACE_DAYS))
            self.gamification_repository.create_rank_event(account, current_rank, RankEvent.GRACE_START, closing_date)
        elif closing_date >= account.grace_until:
            self.gamification_repository.update_rank(account, balance_rank, None)
            self.gamification_repository.create_rank_event(account, balance_rank, RankEvent.DOWN, closing_date)
        self.gamification_repository.update_yield_rank(account, account.rank.enumerator)

    def _parse_accounting_date(self, accounting_date: str) -> date:
        try:
            return date.fromisoformat(accounting_date)
        except ValueError:
            raise InvalidAccountingDate(accounting_date) from None
