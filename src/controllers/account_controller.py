from sqlalchemy.exc import IntegrityError

from controllers.base_controller import BaseController
from dtos import AccountDTO
from errors import CustomerAlreadyHasAccount, CustomerNotFound
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
