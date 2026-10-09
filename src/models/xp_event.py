from sqlalchemy import CHAR, BigInteger, Column, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from models.base import Base
from models import Account, Transaction


class XpEvent(Base):
    __tablename__ = "xp_event"

    id = Column(Integer, primary_key=True)
    xp_event_key = Column(CHAR(36), nullable=False)
    account_id = Column(Integer, ForeignKey(Account.id), nullable=False)
    transaction_id = Column(Integer, ForeignKey(Transaction.id), nullable=True)
    source = Column(String(20), nullable=False)
    xp = Column(BigInteger, nullable=False)
    accounting_date = Column(Date, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("xp_event_key"),)

    TRANSFER_SENT = "TRANSFER_SENT"
    TRANSFER_RECEIVED = "TRANSFER_RECEIVED"
    PIGGY_RECORD = "PIGGY_RECORD"
