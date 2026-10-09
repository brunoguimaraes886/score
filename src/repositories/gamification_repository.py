from datetime import date
from uuid import uuid4

from database import Context
from models import Account, LevelEvent, PiggyRank, PointsEvent, RankEvent, Transaction, XpEvent


class GamificationRepository:
    """Grava a gamificação da conta: os eventos e os valores atuais nas colunas da conta (DAD-14).

    Nenhuma regra de negócio mora aqui: quem decide quanto XP, que nível e
    quantos pontos é o GamificationController. A key de cada evento nasce
    aqui, com uuid4 (DAD-12). Evento não se altera nem se apaga (R4): este
    repository só cria eventos; nas colunas da conta, só escreve o valor
    novo que o controller manda. Quem chama já travou a conta (MOV-05).
    """

    def __init__(self, context: Context) -> None:
        self.session = context.db_session

    def create_xp_event(self, account: Account, source: str, xp: int, accounting_date: date, transaction: Transaction = None) -> XpEvent:
        """Um ganho de XP: XpEvent.TRANSFER_SENT, TRANSFER_RECEIVED ou PIGGY_RECORD. A operação fica nula no XP da virada."""
        xp_event = XpEvent()
        xp_event.xp_event_key = str(uuid4())
        xp_event.account_id = account.id
        xp_event.source = source
        xp_event.xp = xp
        xp_event.accounting_date = accounting_date

        if transaction is not None:
            xp_event.transaction_id = transaction.id

        self.session.add(xp_event)

        return xp_event

    def create_level_event(self, account: Account, level: int, accounting_date: date) -> LevelEvent:
        """Um nível alcançado (GAM-05): cada um vale 1 ponto livre (GAM-06)."""
        level_event = LevelEvent()
        level_event.level_event_key = str(uuid4())
        level_event.account_id = account.id
        level_event.level = level
        level_event.accounting_date = accounting_date

        self.session.add(level_event)

        return level_event

    def create_points_event(self, account: Account, action: str, points: int, benefit: str = None) -> PointsEvent:
        """Uma mudança dos pontos (GAM-07, GAM-21): PointsEvent.APPLY com o benefício, ou PointsEvent.RESET sem benefício."""
        points_event = PointsEvent()
        points_event.points_event_key = str(uuid4())
        points_event.account_id = account.id
        points_event.action = action
        points_event.benefit = benefit
        points_event.points = points

        self.session.add(points_event)

        return points_event

    def create_rank_event(self, account: Account, rank_enumerator: str, kind: str, accounting_date: date) -> RankEvent:
        """Uma mudança de ranque (GAM-12, GAM-14): RankEvent.UP, GRACE_START, GRACE_END ou DOWN. Quem usa é a fase 7."""
        rank_event = RankEvent()
        rank_event.rank_event_key = str(uuid4())
        rank_event.account_id = account.id
        rank_event.rank = self.session.query(PiggyRank).filter(PiggyRank.enumerator == rank_enumerator).one()
        rank_event.kind = kind
        rank_event.accounting_date = accounting_date

        self.session.add(rank_event)

        return rank_event

    def update_progress(self, account: Account, level: int, xp: int, points_free: int) -> None:
        """Escreve o nível, o XP dentro do nível e os pontos livres da conta (DAD-14)."""
        account.level = level
        account.xp = xp
        account.points_free = points_free

    def update_points(self, account: Account, points_free: int, points_fee: int, points_chance: int) -> None:
        """Escreve os pontos livres, em tarifa e em chance da conta (DAD-14)."""
        account.points_free = points_free
        account.points_fee = points_fee
        account.points_chance = points_chance

    def update_piggy_record(self, account: Account, piggy_record: int) -> None:
        """Escreve o recorde do cofrinho, em centavos (GAM-04)."""
        account.piggy_record = piggy_record

    def update_rank(self, account: Account, rank_enumerator: str, grace_until: date) -> None:
        """Escreve o ranque atual da conta e o fim da carência; grace_until nulo fora da carência (GAM-12, GAM-14)."""
        account.rank = self.session.query(PiggyRank).filter(PiggyRank.enumerator == rank_enumerator).one()
        account.grace_until = grace_until
