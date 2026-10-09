from datetime import date
from uuid import uuid4

from database import Context
from models import Entry, Transaction, TransactionType


class TransactionRepository:
    """Consulta e grava as operações (DAD-06). Nenhuma regra de negócio mora aqui.

    A key nasce aqui, com uuid4 (DAD-12). Operação não se altera nem se
    apaga (R4, DAD-11): este repository só cria e consulta.
    """

    def __init__(self, context: Context) -> None:
        self.session = context.db_session

    def create(self, transaction_type_enumerator: str, request_control_key: str, request_hash: str, accounting_date: date) -> Transaction:
        """Cria a operação com as duas datas (DAD-17): accounting_date vem do relógio do banco; created_at, do NOW() do banco.

        O flush manda o INSERT na hora: dá o id aos lançamentos e, se a
        request_control_key já existe, levanta o IntegrityError do UNIQUE
        aqui, antes de qualquer lançamento (MOV-19). Se outra transação
        acabou de gravar a mesma chave e ainda não fez commit, o INSERT
        espera por ela.
        """
        transaction = Transaction()
        transaction.transaction_key = str(uuid4())
        transaction.transaction_type = (
            self.session.query(TransactionType).filter(TransactionType.enumerator == transaction_type_enumerator).one()
        )
        transaction.request_control_key = request_control_key
        transaction.request_hash = request_hash
        transaction.accounting_date = accounting_date

        self.session.add(transaction)
        self.session.flush()

        return transaction

    def get_by_request_control_key(self, request_control_key: str) -> Transaction:
        """A operação gravada com esta chave de idempotência; None quando não existe (MOV-12)."""
        return self.session.query(Transaction).filter(Transaction.request_control_key == request_control_key).first()

    def get_by_key_for_account(self, transaction_key: str, account_ids: list) -> Transaction:
        """A operação com esta key, se ela tem pelo menos um lançamento numa das contas de account_ids; None nos outros casos (R8)."""
        return (
            self.session.query(Transaction)
            .join(Entry, Entry.transaction_id == Transaction.id)
            .filter(Transaction.transaction_key == transaction_key, Entry.account_id.in_(account_ids))
            .first()
        )
