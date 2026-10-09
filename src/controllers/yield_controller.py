from controllers.base_controller import BaseController
from calculations import redemption_taxes
from repositories import AccountRepository, BankClockRepository, CategoryRepository, LotRepository


class YieldController(BaseController):
    """Estimativa de resgate total por categoria, na data contabil atual (COF-28)."""

    def __init__(self) -> None:
        super().__init__(__name__)
        self.account_repository = AccountRepository(self.context)
        self.bank_clock_repository = BankClockRepository(self.context)
        self.category_repository = CategoryRepository(self.context)
        self.lot_repository = LotRepository(self.context)

    def lock_snapshot(self, account):
        accounting_date = self.bank_clock_repository.get_accounting_date()
        piggy_bank = self.account_repository.get_piggy_bank(account)
        locked = {a.id: a for a in self.account_repository.lock_accounts([account, piggy_bank])}
        return locked[account.id], locked[piggy_bank.id], accounting_date

    def category_summary(self, category, accounting_date) -> dict:
        parts = [((accounting_date - lot.accounting_date).days, lot.yield_remaining)
                 for lot in self.lot_repository.list_open_for_update(category)]
        gross_yield = sum(value for _, value in parts)
        iof, ir = redemption_taxes(parts)
        return {"gross_yield": gross_yield, "net_yield": gross_yield - iof - ir,
                "yield_accounting_date": accounting_date.isoformat()}

    def account_summary(self, piggy_bank, accounting_date) -> dict:
        gross_yield = 0
        net_yield = 0
        offset = 0
        while True:
            categories = self.category_repository.list_active_page(piggy_bank, 100, offset)
            for category in categories[:100]:
                summary = self.category_summary(category, accounting_date)
                gross_yield += summary["gross_yield"]
                net_yield += summary["net_yield"]
            if len(categories) <= 100:
                break
            offset += 100
        return {"piggy_bank_gross_yield": gross_yield, "piggy_bank_net_yield": net_yield,
                "yield_accounting_date": accounting_date.isoformat()}
