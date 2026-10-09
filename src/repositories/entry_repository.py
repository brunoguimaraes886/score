from uuid import uuid4

from database import Context
from models import Account, Category, Customer, Entry, EntryType, Transaction


class EntryRepository:
    """Consulta e grava os lançamentos: as pernas de cada operação (DAD-05, DAD-16).

    Nenhuma regra de negócio mora aqui. A key nasce aqui, com uuid4
    (DAD-12). Lançamento não se altera nem se apaga (R4, DAD-11).
    """

    def __init__(self, context: Context) -> None:
        self.session = context.db_session

    def create(
        self,
        transaction: Transaction,
        account: Account,
        entry_type_enumerator: str,
        amount: int,
        category: Category = None,
    ) -> Entry:
        """Grava um lançamento de `amount` centavos (negativo sai, positivo entra) na conta.

        Conta com saldo em coluna (de cliente e cofrinho): soma o amount ao
        balance e grava o saldo novo em balance_after (DAD-07, MOV-19).
        Contas do sistema (BANK e OUTSIDE_WORLD) têm balance nulo: os dois
        ficam nulos, e o saldo delas é a soma dos lançamentos (DAD-09).

        Quem chama já travou a conta de cliente (MOV-05). O flush grava na
        ordem das chamadas: o id dos lançamentos de uma operação cresce
        nessa ordem, e o extrato desempata por ele (MOV-14).
        """
        entry = Entry()
        entry.entry_key = str(uuid4())
        entry.transaction_id = transaction.id
        entry.account_id = account.id
        entry.entry_type = self.session.query(EntryType).filter(EntryType.enumerator == entry_type_enumerator).one()
        entry.amount = amount
        entry.created_at = transaction.created_at

        if category is not None:
            entry.category_id = category.id

        if account.balance is not None:
            account.balance = account.balance + amount
            entry.balance_after = account.balance

        self.session.add(entry)
        self.session.flush()

        return entry

    def list_by_transaction(self, transaction: Transaction, account_ids: list) -> list:
        """Os lançamentos da operação nas contas de account_ids, na ordem em que foram gravados (id crescente)."""
        return (
            self.session.query(Entry)
            .filter(Entry.transaction_id == transaction.id, Entry.account_id.in_(account_ids))
            .order_by(Entry.id)
            .all()
        )

    def get_transfer_counterparty_customer(self, entry: Entry) -> Customer:
        """O cliente da outra ponta de um lançamento AMOUNT de transferência (MOV-17).

        É o dono da conta do outro lançamento AMOUNT da mesma operação: na
        transferência, os dois AMOUNT são o de quem envia e o de quem recebe.
        """
        return (
            self.session.query(Customer)
            .join(Account, Account.customer_id == Customer.id)
            .join(Entry, Entry.account_id == Account.id)
            .join(EntryType, EntryType.id == Entry.entry_type_id)
            .filter(
                Entry.transaction_id == entry.transaction_id,
                Entry.id != entry.id,
                EntryType.enumerator == EntryType.AMOUNT,
            )
            .one()
        )

    def list_page(self, account: Account, limit: int, offset: int) -> list:
        """Uma página do extrato da conta: pares (lançamento, operação), mais recente primeiro (MOV-14).

        Ordem: created_at decrescente e, no empate (os lançamentos de uma
        operação nascem no mesmo instante), o id decrescente. Pede limit + 1
        linhas: a linha a mais só diz ao controller que existe próxima
        página. O índice entry_account_created_at_id_idx cobre esta consulta.
        """
        return (
            self.session.query(Entry, Transaction)
            .join(Transaction, Transaction.id == Entry.transaction_id)
            .filter(Entry.account_id == account.id)
            .order_by(Entry.created_at.desc(), Entry.id.desc())
            .limit(limit + 1)
            .offset(offset)
            .all()
        )
