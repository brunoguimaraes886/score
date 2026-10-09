from sqlalchemy import CHAR, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from models.base import Base
from models import Account


class PointsEvent(Base):
    __tablename__ = "points_event"

    id = Column(Integer, primary_key=True)
    points_event_key = Column(CHAR(36), nullable=False)
    account_id = Column(Integer, ForeignKey(Account.id), nullable=False)
    action = Column(String(10), nullable=False)
    benefit = Column(String(10), nullable=True)
    points = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("points_event_key"),)

    APPLY = "APPLY"
    RESET = "RESET"
    FEE = "FEE"
    CHANCE = "CHANCE"
