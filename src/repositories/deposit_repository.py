from uuid import uuid4

from database import Context
from models import Deposit, Transaction


class DepositRepository:
    """Consulta e grava quem depositou (MOV-15, MOV-16), na tabela deposits. Nenhuma regra de negócio mora aqui."""

    def __init__(self, context: Context) -> None:
        self.session = context.db_session

    def create(self, transaction: Transaction, depositor_name: str, depositor_document: str) -> Deposit:
        """Grava o nome e o CPF ou CNPJ formatado de quem depositou, ligados à operação DEPOSIT.

        O documento inteiro fica só aqui, no banco (PRD-12): para fora, só
        sai mascarado.
        """
        deposit = Deposit()
        deposit.deposit_key = str(uuid4())
        deposit.transaction_id = transaction.id
        deposit.depositor_name = depositor_name
        deposit.depositor_document = depositor_document

        self.session.add(deposit)
        self.session.flush()

        return deposit

    def get_by_transaction(self, transaction: Transaction) -> Deposit:
        """Quem fez o depósito desta operação; None quando a operação não é um depósito."""
        return self.session.query(Deposit).filter(Deposit.transaction_id == transaction.id).first()
