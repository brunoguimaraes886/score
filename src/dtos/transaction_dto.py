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
    def with_piggy_bank_balance(transaction: Transaction, balance: int, piggy_bank_balance: int) -> dict:
        """A resposta do guardar: a key, o saldo da conta e o saldo total do cofrinho, os dois depois de guardar (docs/rotas.md)."""
        return {
            "transaction_key": transaction.transaction_key,
            "balance": balance,
            "piggy_bank_balance": piggy_bank_balance,
        }

    @staticmethod
    def with_redemption(transaction: Transaction, balance: int, piggy_bank_balance: int, redemption_amounts: dict) -> dict:
        """A resposta do resgate: a do guardar mais o bruto, o IOF, o IR e o líquido (COF-08)."""
        return {
            "transaction_key": transaction.transaction_key,
            "balance": balance,
            "piggy_bank_balance": piggy_bank_balance,
            "gross_amount": redemption_amounts["gross_amount"],
            "iof": redemption_amounts["iof"],
            "ir": redemption_amounts["ir"],
            "net_amount": redemption_amounts["net_amount"],
        }

    @staticmethod
    def obj_to_dict(transaction: Transaction, entries: list, redemption_amounts: dict = None) -> dict:
        """A operação para o dono (GET .../transactions/{transaction_key}), com os lançamentos já no formato do extrato.

        Na operação REDEEM, `redemption_amounts` traz o bruto, o IOF, o IR e
        o líquido, que entram no fim do objeto (docs/rotas.md, COF-08).
        """
        transaction_dict = {
            "transaction_key": transaction.transaction_key,
            "type": transaction.transaction_type.enumerator,
            "accounting_date": transaction.accounting_date.isoformat(),
            "created_at": transaction.created_at.isoformat(),
            "entries": entries,
        }

        if redemption_amounts is not None:
            transaction_dict.update(redemption_amounts)

        return transaction_dict
