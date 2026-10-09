from models import Category, Customer, Deposit, Entry, Transaction
from utils.document_number import mask_document_number


class EntryDTO:
    """Um item do extrato (MOV-14, MOV-17, MOV-18): keys públicas, dinheiro em centavos, nunca id (R5).

    A outra ponta (`counterparty`) chega pronta do controller, montada por
    um dos três métodos de baixo; o CPF e o CNPJ de outra pessoa só saem
    mascarados (PRD-12).
    """

    @staticmethod
    def obj_to_dict(entry: Entry, transaction: Transaction, counterparty: dict, category: Category = None) -> dict:
        category_dict = None
        if category is not None:
            category_dict = {
                "category_key": category.category_key,
                "name": category.name,
            }

        return {
            "entry_key": entry.entry_key,
            "transaction_key": transaction.transaction_key,
            "transaction_type": transaction.transaction_type.enumerator,
            "entry_type": entry.entry_type.enumerator,
            "amount": entry.amount,
            "balance_after": entry.balance_after,
            "category": category_dict,
            "counterparty": counterparty,
            "accounting_date": transaction.accounting_date.isoformat(),
            "created_at": entry.created_at.isoformat(),
        }

    @staticmethod
    def customer_counterparty(customer: Customer) -> dict:
        """Na transferência: o outro cliente, com o CPF mascarado."""
        return {
            "type": "CUSTOMER",
            "name": customer.name,
            "document_number": mask_document_number(customer.document_number),
        }

    @staticmethod
    def depositor_counterparty(deposit: Deposit) -> dict:
        """No depósito: quem depositou, com o CPF ou o CNPJ mascarado."""
        return {
            "type": "DEPOSITOR",
            "name": deposit.depositor_name,
            "document_number": mask_document_number(deposit.depositor_document),
        }

    @staticmethod
    def bank_counterparty() -> dict:
        """Na tarifa, no prêmio, no rendimento, no IOF e no IR: o banco."""
        return {"type": "BANK"}
