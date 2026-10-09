from sqlalchemy.exc import IntegrityError

from calculations import split_redemption
from controllers.base_controller import BaseController
from controllers.gamification_controller import GamificationController
from dtos import EntryDTO, TransactionDTO
from errors import (
    AccountNotActive,
    CategoryNotFound,
    IdempotencyKeyConflict,
    InsufficientBalance,
    InsufficientCategoryBalance,
)
from models import Account, AccountStatus, AccountType, Category, EntryType, Transaction, TransactionType
from repositories import AccountRepository, BankClockRepository, CategoryRepository, EntryRepository, LotRepository, TransactionRepository
from utils.request_hash import hash_request_body


class PiggyBankController(BaseController):
    """As regras do cofrinho: guardar e resgatar (COF).

    Guardar e resgatar seguem o desenho do dinheiro em movimento
    (TransactionController): dono → repetição → relógio → trava → regras →
    gravação. A trava pega a conta e o cofrinho, na ordem do id (MOV-05,
    MOV-11). Sem tarifa (MOV-09) e sem XP de movimentação (GAM-17): o único
    XP é o do recorde do cofrinho (GAM-04).
    """

    def __init__(self) -> None:
        super().__init__(__name__)
        self.account_repository = AccountRepository(self.context)
        self.bank_clock_repository = BankClockRepository(self.context)
        self.category_repository = CategoryRepository(self.context)
        self.entry_repository = EntryRepository(self.context)
        self.lot_repository = LotRepository(self.context)
        self.transaction_repository = TransactionRepository(self.context)
        self.gamification_controller = GamificationController()

    def save(self, account_key: str, account_token: str, saving_data: dict) -> dict:
        """Guardar: leva dinheiro da conta para uma categoria do cofrinho (COF-06, COF-10, COF-11). As regras, nesta ordem:

        1. a conta é do dono do token (404 QIT001010, R8);
        2. a mesma request_control_key com o mesmo pedido devolve a resposta
           da primeira vez, com os saldos de depois daquele guardar (MOV-19);
           com outro pedido, 409 QIT001014 (MOV-12);
        3. trava a conta e o cofrinho (MOV-05);
        4. a conta está ACTIVE (409 QIT001011, CLI-09);
        5. a categoria é a "economias": sem category_key no corpo, é ela;
           outra key, 404 QIT001021 (as outras categorias entram no 9.6);
        6. o saldo da conta cobre o valor (422 QIT001015).

        Depois: a operação SAVE; AMOUNT −valor na conta e AMOUNT +valor no
        cofrinho, na categoria; um lote novo com o valor e a data contábil
        (COF-06). O ranque sobe na hora se o saldo do cofrinho alcançou um
        ranque maior (GAM-19), e passar do recorde dá XP (GAM-04). A
        resposta traz a key, o saldo da conta e o saldo do cofrinho.
        """
        account = self.get_owned_account(account_key, account_token)

        request_control_key = saving_data["request_control_key"]
        request_hash = hash_request_body(TransactionType.SAVE, account_key, saving_data)

        repeated_transaction = self._find_repeated(request_control_key, request_hash)
        if repeated_transaction is not None:
            return self._saving_response(repeated_transaction, account)

        accounting_date = self.bank_clock_repository.get_accounting_date()
        account, piggy_bank = self._lock_account_and_piggy_bank(account)

        # Uma chamada com a mesma chave pode ter concluído enquanto esta esperava a trava.
        repeated_transaction = self._find_repeated(request_control_key, request_hash)
        if repeated_transaction is not None:
            return self._saving_response(repeated_transaction, account)

        if account.status.enumerator != AccountStatus.ACTIVE:
            raise AccountNotActive(account_key, account.status.enumerator)

        category = self._get_category(piggy_bank, saving_data.get("category_key"))
        amount = saving_data["amount"]

        if account.balance < amount:
            raise InsufficientBalance(account_key)

        try:
            transaction = self.transaction_repository.create(TransactionType.SAVE, request_control_key, request_hash, accounting_date)
            self.entry_repository.create(transaction, account, EntryType.AMOUNT, -amount)
            self.entry_repository.create(transaction, piggy_bank, EntryType.AMOUNT, amount, category)
            self.lot_repository.create(category, transaction, accounting_date, amount)

            self.gamification_controller.raise_rank(account, piggy_bank, accounting_date)
            self.gamification_controller.award_record_xp(account, transaction, accounting_date)

            transaction_dto = TransactionDTO.with_piggy_bank_balance(transaction, account.balance, piggy_bank.balance)
            self.logger.info("operation_ready_to_commit transaction_key=%s", transaction.transaction_key)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()

            repeated_transaction = self._find_repeated(request_control_key, request_hash)
            if repeated_transaction is None:
                raise

            return self._saving_response(repeated_transaction, account)

        return transaction_dto

    def redeem(self, account_key: str, account_token: str, redemption_data: dict) -> dict:
        """Resgatar: traz dinheiro de uma categoria do cofrinho para a conta (COF-06, COF-07, COF-10, COF-24). As regras, nesta ordem:

        1. a conta é do dono do token (404 QIT001010, R8);
        2. a mesma request_control_key com o mesmo pedido devolve a resposta
           da primeira vez (MOV-19); com outro pedido, 409 QIT001014 (MOV-12);
        3. trava a conta e o cofrinho (MOV-05);
        4. a conta está ACTIVE (409 QIT001011, CLI-09);
        5. a categoria é a "economias": sem category_key no corpo, é ela;
           outra key, 404 QIT001021 (as outras categorias entram no 9.6);
        6. o saldo da categoria cobre o valor (422 QIT001023, COF-07), mesmo
           que o cofrinho todo tenha o dinheiro.

        Depois: a operação REDEEM; o valor sai dos lotes da categoria, do
        mais antigo para o mais novo, cada um até zerar (COF-06), e de cada
        lote o principal e o rendimento saem na proporção do lote (COF-24);
        AMOUNT −valor no cofrinho, na categoria, e AMOUNT +valor na conta.
        IOF e IR entram no passo 9.2: nesta fase o bruto é o líquido. O
        ranque não cai (GAM-19) e o recorde não muda (GAM-04). A resposta
        traz a key, os dois saldos, o bruto, o IOF, o IR e o líquido (COF-08).
        """
        account = self.get_owned_account(account_key, account_token)

        request_control_key = redemption_data["request_control_key"]
        request_hash = hash_request_body(TransactionType.REDEEM, account_key, redemption_data)

        repeated_transaction = self._find_repeated(request_control_key, request_hash)
        if repeated_transaction is not None:
            return self._redemption_response(repeated_transaction, account)

        accounting_date = self.bank_clock_repository.get_accounting_date()
        account, piggy_bank = self._lock_account_and_piggy_bank(account)

        # Uma chamada com a mesma chave pode ter concluído enquanto esta esperava a trava.
        repeated_transaction = self._find_repeated(request_control_key, request_hash)
        if repeated_transaction is not None:
            return self._redemption_response(repeated_transaction, account)

        if account.status.enumerator != AccountStatus.ACTIVE:
            raise AccountNotActive(account_key, account.status.enumerator)

        category = self._get_category(piggy_bank, redemption_data.get("category_key"))
        amount = redemption_data["amount"]

        if self.category_repository.get_balance(category) < amount:
            raise InsufficientCategoryBalance(category.category_key)

        try:
            transaction = self.transaction_repository.create(TransactionType.REDEEM, request_control_key, request_hash, accounting_date)
            self._take_from_lots(category, amount)
            self.entry_repository.create(transaction, piggy_bank, EntryType.AMOUNT, -amount, category)
            self.entry_repository.create(transaction, account, EntryType.AMOUNT, amount)

            redemption_amounts = self.get_redemption_amounts(transaction, piggy_bank)
            transaction_dto = TransactionDTO.with_redemption(transaction, account.balance, piggy_bank.balance, redemption_amounts)
            self.logger.info("operation_ready_to_commit transaction_key=%s", transaction.transaction_key)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()

            repeated_transaction = self._find_repeated(request_control_key, request_hash)
            if repeated_transaction is None:
                raise

            return self._redemption_response(repeated_transaction, account)

        return transaction_dto

    def get_redemption_amounts(self, transaction: Transaction, piggy_bank: Account) -> dict:
        """O bruto, o IOF, o IR e o líquido de um resgate, remontados dos lançamentos da operação (COF-08, MOV-19).

        Bruto: o que saiu do cofrinho (os AMOUNT do cofrinho, com o sinal
        trocado). IOF e IR: os lançamentos IOF e IR da conta BANK (passo
        9.2; nesta fase, 0). Líquido: bruto − IOF − IR. A consulta da
        operação (TransactionController.get_transaction) usa o mesmo método.
        """
        bank = self.account_repository.get_system_account(AccountType.BANK)

        gross_amount = 0
        iof = 0
        ir = 0

        for entry in self.entry_repository.list_by_transaction(transaction, [piggy_bank.id, bank.id]):
            entry_type = entry.entry_type.enumerator

            if entry.account_id == piggy_bank.id and entry_type == EntryType.AMOUNT:
                gross_amount = gross_amount - entry.amount

            if entry.account_id == bank.id and entry_type == EntryType.IOF:
                iof = iof + entry.amount

            if entry.account_id == bank.id and entry_type == EntryType.IR:
                ir = ir + entry.amount

        return {
            "gross_amount": gross_amount,
            "iof": iof,
            "ir": ir,
            "net_amount": gross_amount - iof - ir,
        }

    def list_piggy_bank_entries(self, account_key: str, account_token: str, limit: int, offset: int, category_key: str = None) -> dict:
        """Uma página do extrato do cofrinho, só para o dono (COF-05, MOV-04, MOV-14). Não grava nada. As regras, nesta ordem:

        1. a conta é do dono do token (404 QIT001010, R8);
        2. com category_key, a categoria existe neste cofrinho (404
           QIT001021); nesta fase, só a "economias" (passo 9.6).

        Pede limit + 1 linhas ao repository: se veio a linha a mais, existe
        próxima página, e ela não entra na resposta.
        """
        account = self.get_owned_account(account_key, account_token)
        piggy_bank = self.account_repository.get_piggy_bank(account)

        category = None
        if category_key is not None:
            category = self._get_category(piggy_bank, category_key)

        rows = self.entry_repository.list_piggy_bank_page(piggy_bank, limit, offset, category)

        is_last_page = True
        if len(rows) > limit:
            is_last_page = False
            rows = rows[:-1]

        entries = []
        for entry, transaction in rows:
            entries.append(self._piggy_bank_entry_to_dict(entry, transaction))

        return {
            "entries_list_dto": entries,
            "is_last_page": is_last_page,
        }

    def _take_from_lots(self, category: Category, amount: int) -> int:
        """Tira o valor dos lotes da categoria, do mais antigo para o mais novo, cada um até zerar (COF-06).

        De cada lote, principal e rendimento saem na proporção dele
        (split_redemption, COF-24); o resíduo fica. Devolve quanto saiu de
        rendimento, somado: é sobre ele que o imposto do passo 9.2 incide.
        """
        remaining = amount
        yield_taken = 0

        for lot in self.lot_repository.list_open_for_update(category):
            if remaining == 0:
                break

            taken = min(remaining, lot.principal_remaining + lot.yield_remaining)
            principal_part, yield_part = split_redemption(lot.principal_remaining, lot.yield_remaining, taken)

            self.lot_repository.update_remaining(lot, lot.principal_remaining - principal_part, lot.yield_remaining - yield_part, lot.residue)

            yield_taken = yield_taken + yield_part
            remaining = remaining - taken

        return yield_taken

    def _get_category(self, piggy_bank: Account, category_key: str) -> Category:
        """A categoria do pedido: sem category_key, a "economias" (COF-03).

        Nesta fase o cofrinho só tem a "economias": outra key responde 404
        QIT001021 (passo 9.6).
        """
        category = self.category_repository.get_default(piggy_bank)

        if category_key is not None and category_key != category.category_key:
            raise CategoryNotFound(category_key)

        return category

    def _lock_account_and_piggy_bank(self, account: Account) -> tuple:
        """A conta e o cofrinho dela, travados na ordem do id (MOV-05, MOV-11), com os valores relidos do banco."""
        piggy_bank = self.account_repository.get_piggy_bank(account)

        locked_accounts = {}
        for locked_account in self.account_repository.lock_accounts([account, piggy_bank]):
            locked_accounts[locked_account.id] = locked_account

        return locked_accounts[account.id], locked_accounts[piggy_bank.id]

    def _saving_response(self, transaction: Transaction, account: Account) -> dict:
        """A resposta de um guardar já feito, remontada dos lançamentos (MOV-19)."""
        piggy_bank = self.account_repository.get_piggy_bank(account)

        return TransactionDTO.with_piggy_bank_balance(
            transaction,
            self._balance_after(transaction, account),
            self._balance_after(transaction, piggy_bank),
        )

    def _redemption_response(self, transaction: Transaction, account: Account) -> dict:
        """A resposta de um resgate já feito, remontada dos lançamentos (MOV-19)."""
        piggy_bank = self.account_repository.get_piggy_bank(account)

        return TransactionDTO.with_redemption(
            transaction,
            self._balance_after(transaction, account),
            self._balance_after(transaction, piggy_bank),
            self.get_redemption_amounts(transaction, piggy_bank),
        )

    def _find_repeated(self, request_control_key: str, request_hash: str) -> Transaction:
        """A operação já gravada com esta chave e o mesmo pedido; None quando a chave é nova (MOV-12, MOV-19).

        A chave já usada com outro pedido (outro hash, inclusive de outra
        operação) responde 409 QIT001014.
        """
        transaction = self.transaction_repository.get_by_request_control_key(request_control_key)

        if transaction is None:
            return None

        if transaction.request_hash != request_hash:
            raise IdempotencyKeyConflict(request_control_key)

        return transaction

    def _balance_after(self, transaction: Transaction, account: Account) -> int:
        """O saldo da conta (ou do cofrinho) logo depois da operação: o balance_after do último lançamento dela na operação (MOV-19)."""
        entries = self.entry_repository.list_by_transaction(transaction, [account.id])

        return entries[-1].balance_after

    def _piggy_bank_entry_to_dict(self, entry, transaction: Transaction) -> dict:
        """Um lançamento do cofrinho no formato do extrato, com a categoria dele e a outra ponta (MOV-17).

        No cofrinho só há dois tipos de lançamento: AMOUNT (guardar e
        resgatar), cuja outra ponta é a conta principal, e YIELD (rendimento,
        passo 7.12), cuja outra ponta é o banco.
        """
        category = self.category_repository.get_by_id(entry.category_id)

        counterparty = EntryDTO.account_counterparty()
        if entry.entry_type.enumerator != EntryType.AMOUNT:
            counterparty = EntryDTO.bank_counterparty()

        return EntryDTO.obj_to_dict(entry, transaction, counterparty, category)
