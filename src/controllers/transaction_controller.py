from sqlalchemy.exc import IntegrityError

from controllers.base_controller import BaseController
from dtos import TransactionDTO
from errors import (
    AccountNotActive,
    AccountNotFound,
    IdempotencyKeyConflict,
    InvalidDocumentNumber,
)
from models import AccountStatus, AccountType, EntryType, Transaction, TransactionType
from repositories import AccountRepository, BankClockRepository, DepositRepository, EntryRepository, TransactionRepository
from utils.document_number import FORMATTED_CPF_LENGTH, is_valid_cnpj, is_valid_cpf
from utils.request_hash import hash_request_body


class TransactionController(BaseController):
    """As regras do dinheiro em movimento: depósito, saque, transferência, consulta e extrato (MOV).

    Toda operação de dinheiro segue o mesmo desenho:

    1. confere quem pede e repete a resposta de um pedido já feito (MOV-12);
    2. lê a data contábil (DIA-01) e trava as contas de cliente, na ordem
       do id (MOV-05, MOV-11); as regras são conferidas depois da trava,
       com o estado e o saldo relidos do banco;
    3. grava a operação e os lançamentos, que somam zero (DAD-16), e faz o
       commit; regra que falha não grava nada (DAD-13).
    """

    def __init__(self) -> None:
        super().__init__(__name__)
        self.account_repository = AccountRepository(self.context)
        self.bank_clock_repository = BankClockRepository(self.context)
        self.deposit_repository = DepositRepository(self.context)
        self.entry_repository = EntryRepository(self.context)
        self.transaction_repository = TransactionRepository(self.context)

    def deposit(self, account_key: str, deposit_data: dict) -> dict:
        """Depósito: o dinheiro vem da conta OUTSIDE_WORLD (MOV-07, MOV-15, MOV-16). As regras, nesta ordem:

        1. a conta existe e é de cliente (404 QIT001010); o depósito não
           pede token de conta, e esta recusa não conta como falha de token;
        2. a mesma request_control_key com o mesmo pedido devolve a resposta
           da primeira vez; com outro pedido, 409 QIT001014 (MOV-12);
        3. trava a conta (MOV-05);
        4. a conta está ACTIVE (409 QIT001011, CLI-09);
        5. o CPF ou o CNPJ de quem deposita existe (422 QIT001003, MOV-16).

        Depois: a operação DEPOSIT, o lançamento AMOUNT −valor na
        OUTSIDE_WORLD, o AMOUNT +valor na conta e a linha em deposits. Sem
        tarifa (MOV-09). A resposta traz só a key da operação.
        """
        account = self.account_repository.get_customer_account(account_key)

        if account is None:
            raise AccountNotFound(account_key)

        request_control_key = deposit_data["request_control_key"]
        request_hash = hash_request_body(TransactionType.DEPOSIT, account_key, deposit_data)

        repeated_transaction = self._find_repeated(request_control_key, request_hash)
        if repeated_transaction is not None:
            return TransactionDTO.only_obj_key(repeated_transaction)

        accounting_date = self.bank_clock_repository.get_accounting_date()
        account = self.account_repository.lock_accounts([account])[0]

        # Uma chamada com a mesma chave pode ter concluído enquanto esta esperava a trava.
        repeated_transaction = self._find_repeated(request_control_key, request_hash)
        if repeated_transaction is not None:
            return TransactionDTO.only_obj_key(repeated_transaction)

        if account.status.enumerator != AccountStatus.ACTIVE:
            raise AccountNotActive(account_key, account.status.enumerator)

        if not self._is_valid_depositor_document(deposit_data["depositor_document"]):
            raise InvalidDocumentNumber()

        outside_world = self.account_repository.get_system_account(AccountType.OUTSIDE_WORLD)
        amount = deposit_data["amount"]

        try:
            transaction = self.transaction_repository.create(TransactionType.DEPOSIT, request_control_key, request_hash, accounting_date)
            self.entry_repository.create(transaction, outside_world, EntryType.AMOUNT, -amount)
            self.entry_repository.create(transaction, account, EntryType.AMOUNT, amount)
            self.deposit_repository.create(transaction, deposit_data["depositor_name"], deposit_data["depositor_document"])

            transaction_dto = TransactionDTO.only_obj_key(transaction)
            self.logger.info("operation_ready_to_commit transaction_key=%s", transaction.transaction_key)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()

            repeated_transaction = self._find_repeated(request_control_key, request_hash)
            if repeated_transaction is None:
                raise

            return TransactionDTO.only_obj_key(repeated_transaction)

        return transaction_dto

    def _find_repeated(self, request_control_key: str, request_hash: str) -> Transaction:
        """A operação já gravada com esta chave e o mesmo pedido; None quando a chave é nova (MOV-12, MOV-19).

        A chave já usada com outro pedido (outro hash) responde 409
        QIT001014.
        """
        transaction = self.transaction_repository.get_by_request_control_key(request_control_key)

        if transaction is None:
            return None

        if transaction.request_hash != request_hash:
            raise IdempotencyKeyConflict(request_control_key)

        return transaction

    def _is_valid_depositor_document(self, depositor_document: str) -> bool:
        """CPF (14 caracteres formatado) ou CNPJ (18): o schema já garantiu um dos dois formatos (MOV-16)."""
        if len(depositor_document) == FORMATTED_CPF_LENGTH:
            return is_valid_cpf(depositor_document)

        return is_valid_cnpj(depositor_document)
