from datetime import datetime
from uuid import uuid4

from sqlalchemy import func

from database import Context
from models import Account, AccountStatus, AccountStatusEvent, AccountType, BlockReason, Customer, PiggyRank


class AccountRepository:
    """Consulta e grava contas: de cliente, cofrinho e do sistema (COF-14, DAD-09).

    Nenhuma regra de negócio mora aqui. A key nasce aqui, com uuid4
    (DAD-12). Toda mudança de estado grava o evento na mesma transação
    (CLI-05, R4).
    """

    def __init__(self, context: Context) -> None:
        self.session = context.db_session

    def create_customer_account(self, customer: Customer, token_hash: str) -> Account:
        """Abre a conta do cliente, o cofrinho ligado a ela e o evento ACTIVE da conta.

        A conta nasce ACTIVE, com saldo 0, só o hash do token (API-16) e o
        ranque DEFAULT, o atual e o que rende (GAM-13). O cofrinho é outra
        linha de account, do tipo PIGGY_BANK, ACTIVE, do mesmo cliente,
        com parent_account_id = id da conta, saldo 0 e sem token (COF-14).

        O primeiro flush dá o id da conta ao cofrinho e ao evento. Uma
        segunda conta não encerrada do mesmo cliente é barrada aqui, pelo
        índice account_one_open_per_customer_idx, como IntegrityError.
        """
        active = self._get_fixed_type(AccountStatus, AccountStatus.ACTIVE)
        default_rank = self._get_fixed_type(PiggyRank, PiggyRank.DEFAULT)

        account = Account()
        account.account_key = str(uuid4())
        account.account_type = self._get_fixed_type(AccountType, AccountType.CUSTOMER)
        account.status = active
        account.customer_id = customer.id
        account.balance = 0
        account.token_hash = token_hash
        account.rank = default_rank
        account.yield_rank = default_rank
        self.session.add(account)
        self.session.flush()

        piggy_bank = Account()
        piggy_bank.account_key = str(uuid4())
        piggy_bank.account_type = self._get_fixed_type(AccountType, AccountType.PIGGY_BANK)
        piggy_bank.status = active
        piggy_bank.customer_id = customer.id
        piggy_bank.parent_account_id = account.id
        piggy_bank.balance = 0
        self.session.add(piggy_bank)
        self._add_status_event(account, active, None, None)
        self.session.flush()
        return account

    def get_by_key(self, account_key: str) -> Account:
        """A conta com esta key, de qualquer tipo; None quando não existe."""
        return self.session.query(Account).filter(Account.account_key == account_key).first()

    def get_customer_account(self, account_key: str) -> Account:
        """A conta de cliente com esta key; None para key que não existe, cofrinho ou conta do sistema."""
        account = self.get_by_key(account_key)
        if account is None or account.account_type.enumerator != AccountType.CUSTOMER:
            return None
        return account

    def get_open_account_by_customer(self, customer: Customer) -> Account:
        """A conta de cliente não encerrada (ACTIVE ou BLOCKED) do cliente; None quando ele não tem (CLI-04)."""
        return (
            self.session.query(Account)
            .join(Account.account_type)
            .join(Account.status)
            .filter(
                Account.customer_id == customer.id,
                AccountType.enumerator == AccountType.CUSTOMER,
                AccountStatus.enumerator != AccountStatus.CLOSED,
            )
            .first()
        )

    def list_open_customer_accounts(self) -> list:
        """As contas de cliente não encerradas, na ordem do id, para a virada."""
        return (
            self.session.query(Account)
            .join(Account.account_type)
            .join(Account.status)
            .filter(
                AccountType.enumerator == AccountType.CUSTOMER,
                AccountStatus.enumerator != AccountStatus.CLOSED,
            )
            .order_by(Account.id)
            .all()
        )

    def get_piggy_bank(self, account: Account) -> Account:
        """O cofrinho da conta: a conta cujo parent_account_id é o id dela (COF-14)."""
        return self.session.query(Account).filter(Account.parent_account_id == account.id).first()

    def get_system_account(self, account_type_enumerator: str) -> Account:
        """A conta BANK ou a OUTSIDE_WORLD, criadas pelo database.sql (DAD-09)."""
        return (
            self.session.query(Account)
            .join(Account.account_type)
            .filter(AccountType.enumerator == account_type_enumerator)
            .one()
        )

    def lock_accounts(self, accounts: list) -> list:
        """Trava as linhas das contas na ordem do id, menor primeiro (MOV-05, MOV-11)."""
        account_ids = sorted(account.id for account in accounts)
        return (
            self.session.query(Account)
            .filter(Account.id.in_(account_ids))
            .order_by(Account.id)
            .with_for_update()
            .populate_existing()
            .all()
        )

    def change_status(self, account: Account, status_enumerator: str, source: str = None, block_reason_enumerator: str = None) -> None:
        """Muda o estado da conta e grava o evento, na mesma transação (CLI-05, R4)."""
        status = self._get_fixed_type(AccountStatus, status_enumerator)
        block_reason = None
        if block_reason_enumerator is not None:
            block_reason = self._get_fixed_type(BlockReason, block_reason_enumerator)
        account.status = status
        self._add_status_event(account, status, source, block_reason)

    def get_active_since(self, account: Account) -> datetime:
        """O created_at do último evento ACTIVE da conta: a abertura ou o último desbloqueio (CLI-08).

        É a partir dele que o limite diário de transferências conta. O
        created_at vem do NOW() do banco, o mesmo relógio do created_at das
        operações (TransactionRepository.count_transfers_sent).
        """
        return (
            self.session.query(func.max(AccountStatusEvent.created_at))
            .select_from(AccountStatusEvent)
            .join(AccountStatus, AccountStatus.id == AccountStatusEvent.status_id)
            .filter(AccountStatusEvent.account_id == account.id, AccountStatus.enumerator == AccountStatus.ACTIVE)
            .scalar()
        )

    def _add_status_event(self, account: Account, status: AccountStatus, source: str, block_reason: BlockReason) -> None:
        status_event = AccountStatusEvent()
        status_event.account_id = account.id
        status_event.status = status
        status_event.block_reason = block_reason
        status_event.source = source
        status_event.event_datetime = datetime.now()
        self.session.add(status_event)

    def _get_fixed_type(self, model, enumerator: str):
        """A linha de uma tabela de tipos fixos pelo enumerator."""
        return self.session.query(model).filter(model.enumerator == enumerator).one()
