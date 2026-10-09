from sqlalchemy.exc import IntegrityError

from controllers.base_controller import BaseController
from controllers.yield_controller import YieldController
from dtos import CategoryDTO
from errors import (
    AccountNotActive,
    CategoryDeleted,
    CategoryNotEmpty,
    CategoryNotFound,
    DefaultCategoryCannotBeDeleted,
    DuplicatedCategoryName,
)
from models import Account, AccountStatus, Category, CategoryStatus
from repositories import AccountRepository, CategoryRepository


class CategoryController(BaseController):
    """As regras das categorias do cofrinho: criar, listar, consultar e excluir (COF-03, COF-04, COF-05, COF-18, API-15).

    Conta bloqueada cria, lista e exclui categoria (CLI-09); conta
    encerrada só lê (CLI-05). Nenhuma categoria se apaga: excluir é mudar
    o estado para DELETED e gravar o evento (R4).
    """

    def __init__(self) -> None:
        super().__init__(__name__)
        self.account_repository = AccountRepository(self.context)
        self.category_repository = CategoryRepository(self.context)

    def create_category(self, account_key: str, account_token: str, category_data: dict) -> dict:
        """Cria uma categoria no cofrinho da conta (COF-03, COF-18). As regras, nesta ordem:

        1. a conta é do dono do token (404 QIT001010, R8);
        2. a conta não está CLOSED (409 QIT001011, CLI-05); BLOCKED cria
           (CLI-09);
        3. o nome não se repete entre as categorias ativas do cofrinho (409
           QIT001024, COF-18). Quem confere é o índice
           category_active_name_idx, na gravação: o IntegrityError desfaz
           tudo e vira o 409, nunca 500 (R3).

        Depois: a categoria ACTIVE, não padrão, e o evento do estado. A
        resposta traz só a key (API-10).
        """
        account = self.get_owned_account(account_key, account_token)
        account, piggy_bank = self._lock_account_and_piggy_bank(account)

        if account.status.enumerator == AccountStatus.CLOSED:
            raise AccountNotActive(account_key, account.status.enumerator)

        name = category_data["name"]

        try:
            category = self.category_repository.create(piggy_bank, name)

            category_dto = CategoryDTO.only_obj_key(category)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()

            raise DuplicatedCategoryName(name)

        return category_dto

    def list_categories(self, account_key: str, account_token: str, limit: int, offset: int) -> dict:
        account = self.get_owned_account(account_key, account_token)
        yields = YieldController()
        account, piggy_bank, accounting_date = yields.lock_snapshot(account)
        rows = self.category_repository.list_active_page(piggy_bank, limit, offset)
        is_last_page = len(rows) <= limit
        rows = rows[:limit]
        categories = [CategoryDTO.obj_to_dict(category, self.category_repository.get_balance(category),
                      yields.category_summary(category, accounting_date)) for category in rows]
        return {"categories_list_dto": categories, "is_last_page": is_last_page}

    def get_category(self, account_key: str, account_token: str, category_key: str) -> dict:
        account = self.get_owned_account(account_key, account_token)
        yields = YieldController()
        account, piggy_bank, accounting_date = yields.lock_snapshot(account)
        category = self._get_category(piggy_bank, category_key)
        return CategoryDTO.obj_to_dict(category, self.category_repository.get_balance(category),
                                       yields.category_summary(category, accounting_date))

    def delete_category(self, account_key: str, account_token: str, category_key: str) -> None:
        """Exclui uma categoria do cofrinho (COF-04, API-15). As regras, nesta ordem:

        1. a conta é do dono do token (404 QIT001010, R8);
        2. trava a conta e o cofrinho, na ordem do id, como guardar e
           resgatar (MOV-05, MOV-11): um guardar na mesma categoria espera a
           exclusão terminar, e depois vê a categoria excluída;
        3. a conta não está CLOSED (409 QIT001011, CLI-05); BLOCKED exclui
           (CLI-09);
        4. a categoria existe neste cofrinho (404 QIT001021, R8);
        5. a categoria não está excluída (409 QIT001022);
        6. a categoria não é a "economias" (409 QIT001025, COF-04);
        7. o saldo da categoria é 0 (409 QIT001026, COF-04).

        Depois: o estado DELETED e o evento, na mesma transação (R4). Sem
        corpo na resposta (204).
        """
        account = self.get_owned_account(account_key, account_token)
        account, piggy_bank = self._lock_account_and_piggy_bank(account)

        if account.status.enumerator == AccountStatus.CLOSED:
            raise AccountNotActive(account_key, account.status.enumerator)

        category = self._get_category(piggy_bank, category_key)

        if category.status.enumerator == CategoryStatus.DELETED:
            raise CategoryDeleted(category_key)

        if category.is_default:
            raise DefaultCategoryCannotBeDeleted(category_key)

        if self.category_repository.get_balance(category) != 0:
            raise CategoryNotEmpty(category_key)

        self.category_repository.delete(category)
        self.session.commit()

    def _get_category(self, piggy_bank: Account, category_key: str) -> Category:
        """A categoria com esta key neste cofrinho, ativa ou excluída; 404 QIT001021 quando não existe aqui (R8)."""
        category = self.category_repository.get_by_key(piggy_bank, category_key)

        if category is None:
            raise CategoryNotFound(category_key)

        return category

    def _lock_account_and_piggy_bank(self, account: Account) -> tuple:
        """A conta e o cofrinho dela, travados na ordem do id (MOV-05, MOV-11), com os valores relidos do banco."""
        piggy_bank = self.account_repository.get_piggy_bank(account)

        locked_accounts = {}
        for locked_account in self.account_repository.lock_accounts([account, piggy_bank]):
            locked_accounts[locked_account.id] = locked_account

        return locked_accounts[account.id], locked_accounts[piggy_bank.id]
