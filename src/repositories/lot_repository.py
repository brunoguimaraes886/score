from datetime import date
from decimal import Decimal
from uuid import uuid4

from database import Context
from models import Account, Category, Lot, Transaction


class LotRepository:
    """Consulta e grava os lotes do cofrinho (COF-06, COF-23). Nenhuma regra de negócio mora aqui.

    A key nasce aqui, com uuid4 (DAD-12). O lote guarda em colunas o
    principal e o rendimento que restam e o resíduo; quem decide os valores
    é o controller, com o cofrinho travado (COF-23, MOV-05). Lote não se
    apaga: o que zera continua na tabela, com os restos em 0.
    """

    def __init__(self, context: Context) -> None:
        self.session = context.db_session

    def create(self, category: Category, transaction: Transaction, accounting_date: date, principal: int) -> Lot:
        """Um lote novo para cada guardar (COF-06): o principal guardado, rendimento 0 e resíduo 0, com a data contábil do guardar."""
        lot = Lot()
        lot.lot_key = str(uuid4())
        lot.category_id = category.id
        lot.transaction_id = transaction.id
        lot.accounting_date = accounting_date
        lot.principal_remaining = principal
        lot.yield_remaining = 0
        lot.residue = Decimal("0")

        self.session.add(lot)
        self.session.flush()

        return lot

    def list_open_for_update(self, category: Category) -> list:
        """Os lotes da categoria que ainda têm dinheiro, do mais antigo para o mais novo (id crescente), travados com SELECT ... FOR UPDATE (COF-06)."""
        return (
            self.session.query(Lot)
            .filter(Lot.category_id == category.id, Lot.principal_remaining + Lot.yield_remaining > 0)
            .order_by(Lot.id)
            .with_for_update()
            .populate_existing()
            .all()
        )

    def list_open_by_piggy_bank_for_update(self, piggy_bank: Account) -> list:
        """Lotes com dinheiro de todas as categorias, por categoria e antiguidade, travados."""
        return (
            self.session.query(Lot)
            .join(Category, Category.id == Lot.category_id)
            .filter(Category.account_id == piggy_bank.id, Lot.principal_remaining + Lot.yield_remaining > 0)
            .order_by(Lot.category_id, Lot.id)
            .with_for_update(of=Lot)
            .populate_existing()
            .all()
        )

    def update_remaining(self, lot: Lot, principal_remaining: int, yield_remaining: int, residue: Decimal) -> None:
        """Escreve no lote o principal e o rendimento que restam e o resíduo (COF-23)."""
        lot.principal_remaining = principal_remaining
        lot.yield_remaining = yield_remaining
        lot.residue = residue
