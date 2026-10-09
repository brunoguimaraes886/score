from sqlalchemy import CHAR, Column, Date, DateTime, ForeignKey, Integer, UniqueConstraint, func
from models.base import Base
from models import Account


class LevelEvent(Base):
    __tablename__ = "level_event"

    id = Column(Integer, primary_key=True)
    level_event_key = Column(CHAR(36), nullable=False)
    account_id = Column(Integer, ForeignKey(Account.id), nullable=False)
    level = Column(Integer, nullable=False)
    accounting_date = Column(Date, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("level_event_key"),)
