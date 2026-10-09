from sqlalchemy import CHAR, Column, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import relationship
from models.base import Base
from models import Account, PiggyRank


class RankEvent(Base):
    __tablename__ = "rank_event"

    id = Column(Integer, primary_key=True)
    rank_event_key = Column(CHAR(36), nullable=False)
    account_id = Column(Integer, ForeignKey(Account.id), nullable=False)
    rank_id = Column(Integer, ForeignKey(PiggyRank.id), nullable=False)
    kind = Column(String(20), nullable=False)
    accounting_date = Column(Date, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("rank_event_key"),)

    rank = relationship("PiggyRank", foreign_keys=[rank_id], lazy="selectin")

    UP = "UP"
    GRACE_START = "GRACE_START"
    GRACE_END = "GRACE_END"
    DOWN = "DOWN"
