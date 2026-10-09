from datetime import datetime
from uuid import uuid4

from sqlalchemy import func

from database import Context
from models import Account, Category, CategoryStatus, CategoryStatusEvent, Entry


# COF-03: o nome da categoria padrão, que nasce com o cofrinho.
DEFAULT_CATEGORY_NAME = "economias"


class CategoryRepository:
    """Consulta e grava as categorias do cofrinho (COF-03). Nenhuma regra de negócio mora aqui."""

    def __init__(self, context: Context) -> None:
        self.session = context.db_session

    def create_default(self, piggy_bank: Account) -> Category:
        """Cria a categoria "economias" do cofrinho, ACTIVE, e grava o evento do estado (R4).

        O flush dá o id da categoria ao evento. O índice
        category_one_default_idx garante uma padrão por cofrinho.
        """
        active = self.session.query(CategoryStatus).filter(CategoryStatus.enumerator == CategoryStatus.ACTIVE).one()
        category = Category()
        category.category_key = str(uuid4())
        category.account_id = piggy_bank.id
        category.status = active
        category.name = DEFAULT_CATEGORY_NAME
        category.is_default = True
        self.session.add(category)
        self.session.flush()
        status_event = CategoryStatusEvent()
        status_event.category_id = category.id
        status_event.status = active
        status_event.event_datetime = datetime.now()
        self.session.add(status_event)
        return category

    def get_default(self, piggy_bank: Account) -> Category:
        """A categoria "economias" do cofrinho."""
        return (
            self.session.query(Category)
            .filter(Category.account_id == piggy_bank.id, Category.is_default.is_(True))
            .first()
        )

    def get_balance(self, category: Category) -> int:
        """O saldo da categoria: a soma dos lançamentos do cofrinho nela, em centavos (COF-05, COF-23).

        Só os lançamentos do cofrinho têm category_id. O PostgreSQL devolve
        a soma de BIGINT como NUMERIC: o int() a traz de volta para centavos
        inteiros (DAD-08).
        """
        total = self.session.query(func.coalesce(func.sum(Entry.amount), 0)).filter(Entry.category_id == category.id).scalar()

        return int(total)

    def get_by_id(self, category_id: int) -> Category:
        """A categoria com este id; None quando não existe. O id só circula por dentro: para fora sai a category_key (R5)."""
        return self.session.query(Category).filter(Category.id == category_id).first()

    def create(self, piggy_bank: Account, name: str) -> Category:
        """Cria uma categoria do dono no cofrinho, ACTIVE e não padrão, e grava o evento do estado (COF-03, R4).

        A key nasce aqui, com uuid4 (DAD-12). O flush manda o INSERT na hora:
        um nome repetido entre as categorias ativas do cofrinho levanta aqui
        o IntegrityError do índice category_active_name_idx (COF-18).
        """
        category = Category()
        category.category_key = str(uuid4())
        category.account_id = piggy_bank.id
        category.status = self._get_status(CategoryStatus.ACTIVE)
        category.name = name
        category.is_default = False

        self.session.add(category)
        self.session.flush()

        self._add_status_event(category)

        return category

    def get_by_key(self, piggy_bank: Account, category_key: str) -> Category:
        """A categoria com esta key, se ela é deste cofrinho, ativa ou excluída; None nos outros casos (R8)."""
        return (
            self.session.query(Category)
            .filter(Category.account_id == piggy_bank.id, Category.category_key == category_key)
            .first()
        )

    def list_active_page(self, piggy_bank: Account, limit: int, offset: int) -> list:
        """Uma página das categorias ativas do cofrinho, na ordem em que foram criadas.

        Pede limit + 1 linhas: a linha a mais diz ao controller que existe
        próxima página (MOV-04).
        """
        return (
            self.session.query(Category)
            .join(Category.status)
            .filter(Category.account_id == piggy_bank.id, CategoryStatus.enumerator == CategoryStatus.ACTIVE)
            .order_by(Category.created_at, Category.id)
            .limit(limit + 1)
            .offset(offset)
            .all()
        )

    def delete(self, category: Category) -> None:
        """Exclui a categoria: o estado passa a DELETED e o evento é gravado, na mesma transação (API-15, R4). Nada é apagado."""
        category.status = self._get_status(CategoryStatus.DELETED)
        self._add_status_event(category)

    def _add_status_event(self, category: Category) -> None:
        status_event = CategoryStatusEvent()
        status_event.category_id = category.id
        status_event.status = category.status
        status_event.event_datetime = datetime.now()

        self.session.add(status_event)

    def _get_status(self, enumerator: str) -> CategoryStatus:
        """A linha de category_status pelo enumerator (ACTIVE ou DELETED)."""
        return self.session.query(CategoryStatus).filter(CategoryStatus.enumerator == enumerator).one()
