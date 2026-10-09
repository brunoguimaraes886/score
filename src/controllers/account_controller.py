from sqlalchemy.exc import IntegrityError

from controllers.base_controller import BaseController
from dtos import AccountDTO
from errors import (
    AccountNotActive,
    AccountNotBlocked,
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
        """A conta, só para o dono; também bloqueada ou encerrada (CLI-05). Não grava nada."""
        account = self.get_owned_account(account_key, account_token)
        customer = self.customer_repository.get_by_id(account.customer_id)
        piggy_bank = self.account_repository.get_piggy_bank(account)
        return AccountDTO.obj_to_dict(account, customer, piggy_bank)

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

    def _get_locked_customer_account(self, account_key: str) -> Account:
        account = self.account_repository.get_customer_account(account_key)
        if account is None:
            raise AccountNotFound(account_key)
        return self.account_repository.lock_accounts([account])[0]
