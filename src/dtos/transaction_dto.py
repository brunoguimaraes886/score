from models import Transaction


class TransactionDTO:
    """A operação que a API devolve: a key pública, nunca o id nem a request_control_key (R5)."""

    @staticmethod
    def only_obj_key(transaction: Transaction) -> dict:
        """A resposta do depósito: só a key da operação (MOV-16)."""
        return {"transaction_key": transaction.transaction_key}

    @staticmethod
    def with_balance(transaction: Transaction, balance: int) -> dict:
        """A resposta do saque e da transferência: a key e o saldo da conta depois da operação, em centavos (API-10)."""
        return {
            "transaction_key": transaction.transaction_key,
            "balance": balance,
        }

    @staticmethod
    def obj_to_dict(transaction: Transaction, entries: list) -> dict:
        """A operação para o dono (GET .../transactions/{transaction_key}), com os lançamentos já no formato do extrato."""
        return {
            "transaction_key": transaction.transaction_key,
            "type": transaction.transaction_type.enumerator,
            "accounting_date": transaction.accounting_date.isoformat(),
            "created_at": transaction.created_at.isoformat(),
            "entries": entries,
        }
