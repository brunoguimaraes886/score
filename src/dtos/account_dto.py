from models import Account, Customer


class AccountDTO:
    """A conta que a API devolve: keys públicas, nunca id nem token_hash (R5, API-16)."""

    @staticmethod
    def obj_to_dict(account: Account, customer: Customer, piggy_bank: Account) -> dict:
        """A conta para o dono: saldo e saldo total do cofrinho, em centavos (DAD-08)."""
        return {
            "account_key": account.account_key,
            "customer_key": customer.customer_key,
            "status": account.status.enumerator,
            "balance": account.balance,
            "piggy_bank_balance": piggy_bank.balance,
            "created_at": account.created_at.isoformat(),
        }

    @staticmethod
    def open_account_to_dict(account: Account, account_token: str) -> dict:
        """A resposta da abertura: a key e o token, que só sai aqui, uma vez (API-16)."""
        return {"account_key": account.account_key, "account_token": account_token}
