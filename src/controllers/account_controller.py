from sqlalchemy.exc import IntegrityError

from controllers.base_controller import BaseController
from controllers.yield_controller import YieldController
from dtos import AccountDTO
from errors import (
    AccountNotActive,
    AccountNotBlocked,
    AccountNotEmpty,
    AccountNotFound,
    CustomerAlreadyHasAccount,
    CustomerNotFound,
)
from models import Account, AccountStatus, AccountStatusEvent
from repositories import AccountRepository, CategoryRepository, CustomerRepository
from utils.account_token import generate_account_token, hash_account_token


class AccountController(BaseController):
    """As regras da conta (CLI-01, CLI-04, CLI-05, API-16)."""

    def __init__(self) -> None:
        super().__init__(__name__)
        self.account_repository = AccountRepository(self.context)
        self.category_repository = CategoryRepository(self.context)
        self.customer_repository = CustomerRepository(self.context)

    def open_account(self, customer_key: str) -> dict:
        """Abre a conta do cliente e sua estrutura de cofrinho."""
        customer = self.customer_repository.get_by_key(customer_key)
        if customer is None:
            raise CustomerNotFound(customer_key)
        if self.account_repository.get_open_account_by_customer(customer) is not None:
            raise CustomerAlreadyHasAccount(customer_key)
        account_token = generate_account_token()
        try:
            account = self.account_repository.create_customer_account(customer, hash_account_token(account_token))
            piggy_bank = self.account_repository.get_piggy_bank(account)
            self.category_repository.create_default(piggy_bank)
            account_dto = AccountDTO.open_account_to_dict(account, account_token)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            if self.account_repository.get_open_account_by_customer(customer) is not None:
                raise CustomerAlreadyHasAccount(customer_key)
            raise
        return account_dto

    def get_account(self, account_key: str, account_token: str) -> dict:
        account = self.get_owned_account(account_key, account_token)
        yields = YieldController()
        account, piggy_bank, accounting_date = yields.lock_snapshot(account)
        customer = self.customer_repository.get_by_id(account.customer_id)
        summary = yields.account_summary(piggy_bank, accounting_date)
        return AccountDTO.obj_to_dict(account, customer, piggy_bank, summary)

    def block_account(self, account_key: str, reason: str) -> None:
        account = self._get_locked_customer_account(account_key)
        if account.status.enumerator != AccountStatus.ACTIVE:
            raise AccountNotActive(account_key, account.status.enumerator)
        self.account_repository.change_status(account, AccountStatus.BLOCKED, AccountStatusEvent.MANUAL, reason)
        self.session.commit()

    def unblock_account(self, account_key: str) -> None:
        account = self._get_locked_customer_account(account_key)
        if account.status.enumerator != AccountStatus.BLOCKED:
            raise AccountNotBlocked(account_key, account.status.enumerator)
        self.account_repository.change_status(account, AccountStatus.ACTIVE, AccountStatusEvent.MANUAL)
        self.session.commit()

    def close_account(self, account_key: str, account_token: str) -> None:
        """O dono encerra a conta (CLI-05, CLI-06). As regras, nesta ordem:

        1. a conta é do dono do token (404 QIT001010, R8);
        2. trava a linha da conta (o estado e o saldo são relidos depois da
           trava: um depósito ao mesmo tempo espera ou é esperado);
        3. a conta está ACTIVE (409 QIT001011): bloqueada precisa ser
           desbloqueada antes, e encerrada é final;
        4. o saldo é zero (409 QIT001012, CLI-06);
        5. o cofrinho está zerado e é travado depois da conta (MOV-11).

        O cofrinho zerado entra no passo 7.15, entre a regra 4 e a gravação.
        Depois: estado CLOSED e o evento, sem origem e sem motivo (quem muda
        é o dono).
        """
        account = self.get_owned_account(account_key, account_token)
        account = self.account_repository.lock_accounts([account])[0]
        if account.status.enumerator != AccountStatus.ACTIVE:
            raise AccountNotActive(account_key, account.status.enumerator)
        if account.balance != 0:
            raise AccountNotEmpty(account_key)

        piggy_bank = self.account_repository.lock_accounts([self.account_repository.get_piggy_bank(account)])[0]
        if piggy_bank.balance != 0:
            raise AccountNotEmpty(account_key)

        self.account_repository.change_status(account, AccountStatus.CLOSED)
        self.session.commit()

    def _get_locked_customer_account(self, account_key: str) -> Account:
        account = self.account_repository.get_customer_account(account_key)
        if account is None:
            raise AccountNotFound(account_key)
        return self.account_repository.lock_accounts([account])[0]
