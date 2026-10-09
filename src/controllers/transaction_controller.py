from sqlalchemy.exc import IntegrityError

from calculations import calculate_fee
from controllers.base_controller import BaseController
from dtos import TransactionDTO
from errors import (
    AccountNotActive,
    AccountNotFound,
    DestinationAccountNotActive,
    DestinationAccountNotFound,
    IdempotencyKeyConflict,
    InsufficientBalance,
    InvalidDocumentNumber,
    SameAccountTransfer,
)
from models import Account, AccountStatus, AccountType, EntryType, Transaction, TransactionType
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

    def withdraw(self, account_key: str, account_token: str, withdrawal_data: dict) -> dict:
        """Saque: o dinheiro vai para a conta OUTSIDE_WORLD (MOV-07, MOV-15). As regras, nesta ordem:

        1. a conta é do dono do token (404 QIT001010, R8): só o dono saca;
        2. a mesma request_control_key com o mesmo pedido devolve a resposta
           da primeira vez, com o saldo de depois daquele saque (MOV-19);
           com outro pedido, 409 QIT001014 (MOV-12);
        3. trava a conta (MOV-05);
        4. a conta está ACTIVE (409 QIT001011, CLI-09);
        5. o saldo cobre o valor (422 QIT001015, MOV-08).

        Depois: a operação WITHDRAWAL, o AMOUNT −valor na conta e o AMOUNT
        +valor na OUTSIDE_WORLD. Sem tarifa (MOV-09). A resposta traz a key
        e o saldo novo.
        """
        account = self.get_owned_account(account_key, account_token)

        request_control_key = withdrawal_data["request_control_key"]
        request_hash = hash_request_body(TransactionType.WITHDRAWAL, account_key, withdrawal_data)

        repeated_transaction = self._find_repeated(request_control_key, request_hash)
        if repeated_transaction is not None:
            return TransactionDTO.with_balance(repeated_transaction, self._balance_after(repeated_transaction, account))

        accounting_date = self.bank_clock_repository.get_accounting_date()
        account = self.account_repository.lock_accounts([account])[0]

        # Uma chamada com a mesma chave pode ter concluído enquanto esta esperava a trava.
        repeated_transaction = self._find_repeated(request_control_key, request_hash)
        if repeated_transaction is not None:
            return TransactionDTO.with_balance(repeated_transaction, self._balance_after(repeated_transaction, account))

        if account.status.enumerator != AccountStatus.ACTIVE:
            raise AccountNotActive(account_key, account.status.enumerator)

        amount = withdrawal_data["amount"]

        if account.balance < amount:
            raise InsufficientBalance(account_key)

        outside_world = self.account_repository.get_system_account(AccountType.OUTSIDE_WORLD)

        try:
            transaction = self.transaction_repository.create(TransactionType.WITHDRAWAL, request_control_key, request_hash, accounting_date)
            self.entry_repository.create(transaction, account, EntryType.AMOUNT, -amount)
            self.entry_repository.create(transaction, outside_world, EntryType.AMOUNT, amount)

            transaction_dto = TransactionDTO.with_balance(transaction, account.balance)
            self.logger.info("operation_ready_to_commit transaction_key=%s", transaction.transaction_key)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()

            repeated_transaction = self._find_repeated(request_control_key, request_hash)
            if repeated_transaction is None:
                raise

            return TransactionDTO.with_balance(repeated_transaction, self._balance_after(repeated_transaction, account))

        return transaction_dto

    def transfer(self, account_key: str, account_token: str, transfer_data: dict) -> dict:
        """Transferência entre contas de cliente, com tarifa (MOV-01 a MOV-03, MOV-06, MOV-09, DAD-16). As regras, nesta ordem:

        1. a conta de origem é do dono do token (404 QIT001010, R8);
        2. a mesma request_control_key com o mesmo pedido devolve a resposta
           da primeira vez, com o saldo de depois daquela transferência
           (MOV-19); com outro pedido, 409 QIT001014 (MOV-12);
        3. trava a origem e, se o destino existe e é de cliente, também o
           destino, as duas na ordem do id (MOV-05, MOV-11);
        4. a origem está ACTIVE (409 QIT001011, CLI-09);
        5. a origem é diferente do destino (422 QIT001016, MOV-08);
        6. o destino existe e é de cliente (404 QIT001017);
        7. o destino está ACTIVE (409 QIT001018, CLI-09);
        8. o saldo da origem cobre valor + tarifa (422 QIT001015, MOV-01,
           MOV-02); a tarifa é calculate_fee(valor, 0): os pontos entram
           no passo 8.7;
        9. o limite diário (CLI-08) entra no passo 6.9.

        Depois: a operação TRANSFER e os lançamentos, nesta ordem: AMOUNT
        −valor e FEE −tarifa na origem; AMOUNT +valor no destino; FEE
        +tarifa na conta BANK. Tarifa zero não gera lançamento (MOV-10). A
        resposta traz a key e o saldo novo da origem (API-10).
        """
        account = self.get_owned_account(account_key, account_token)

        request_control_key = transfer_data["request_control_key"]
        request_hash = hash_request_body(TransactionType.TRANSFER, account_key, transfer_data)

        repeated_transaction = self._find_repeated(request_control_key, request_hash)
        if repeated_transaction is not None:
            return TransactionDTO.with_balance(repeated_transaction, self._balance_after(repeated_transaction, account))

        accounting_date = self.bank_clock_repository.get_accounting_date()

        destination_account_key = transfer_data["destination_account_key"]
        destination = self.account_repository.get_customer_account(destination_account_key)

        accounts_to_lock = [account]
        if destination is not None:
            accounts_to_lock.append(destination)

        locked_accounts = {}
        for locked_account in self.account_repository.lock_accounts(accounts_to_lock):
            locked_accounts[locked_account.id] = locked_account

        account = locked_accounts[account.id]
        if destination is not None:
            destination = locked_accounts[destination.id]

        # Uma chamada com a mesma chave pode ter concluído enquanto esta esperava a trava.
        repeated_transaction = self._find_repeated(request_control_key, request_hash)
        if repeated_transaction is not None:
            return TransactionDTO.with_balance(repeated_transaction, self._balance_after(repeated_transaction, account))

        if account.status.enumerator != AccountStatus.ACTIVE:
            raise AccountNotActive(account_key, account.status.enumerator)

        if destination_account_key == account.account_key:
            raise SameAccountTransfer()

        if destination is None:
            raise DestinationAccountNotFound(destination_account_key)

        if destination.status.enumerator != AccountStatus.ACTIVE:
            raise DestinationAccountNotActive(destination_account_key)

        amount = transfer_data["amount"]
        fee = calculate_fee(amount, 0)

        if account.balance < amount + fee:
            raise InsufficientBalance(account_key)

        bank = self.account_repository.get_system_account(AccountType.BANK)

        try:
            transaction = self.transaction_repository.create(TransactionType.TRANSFER, request_control_key, request_hash, accounting_date)
            self.entry_repository.create(transaction, account, EntryType.AMOUNT, -amount)

            if fee > 0:
                self.entry_repository.create(transaction, account, EntryType.FEE, -fee)

            self.entry_repository.create(transaction, destination, EntryType.AMOUNT, amount)

            if fee > 0:
                self.entry_repository.create(transaction, bank, EntryType.FEE, fee)

            transaction_dto = TransactionDTO.with_balance(transaction, account.balance)
            self.logger.info("operation_ready_to_commit transaction_key=%s", transaction.transaction_key)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()

            repeated_transaction = self._find_repeated(request_control_key, request_hash)
            if repeated_transaction is None:
                raise

            return TransactionDTO.with_balance(repeated_transaction, self._balance_after(repeated_transaction, account))

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

    def _balance_after(self, transaction: Transaction, account: Account) -> int:
        """O saldo da conta logo depois da operação: o balance_after do último lançamento dela na operação (MOV-19)."""
        entries = self.entry_repository.list_by_transaction(transaction, [account.id])

        return entries[-1].balance_after
