from models import Category


class CategoryDTO:
    """A categoria que a API devolve: a key pública, nunca o id nem o account_id (R5)."""

    @staticmethod
    def only_obj_key(category: Category) -> dict:
        """A resposta da criação: só a key (API-10)."""
        return {"category_key": category.category_key}

    @staticmethod
    def obj_to_dict(category: Category, balance: int) -> dict:
        """A categoria na lista e na consulta: o saldo em centavos (COF-05) e o estado público em maiúsculas, ACTIVE ou DELETED (API-15, docs/rotas.md)."""
        return {
            "category_key": category.category_key,
            "name": category.name,
            "is_default": category.is_default,
            "status": category.status.enumerator,
            "balance": balance,
            "created_at": category.created_at.isoformat(),
        }
