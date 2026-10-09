from datetime import datetime
from uuid import uuid4

from database import Context
from models import Account, Category, CategoryStatus, CategoryStatusEvent


# COF-03: o nome da categoria padrão, que nasce com o cofrinho.
DEFAULT_CATEGORY_NAME = "economias"


class CategoryRepository:
    """Consulta e grava as categorias do cofrinho (COF-03). Nenhuma regra de negócio mora aqui."""

    def __init__(self, context: Context) -> None:
        self.session = context.db_session

    def create_default(self, piggy_bank: Account) -> Category:
        """Cria a categoria "economias" do cofrinho, ACTIVE, e grava o evento do estado (R4)."""
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
