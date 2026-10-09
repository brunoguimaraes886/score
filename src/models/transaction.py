from sqlalchemy import CHAR, Column, Date, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import relationship
from models.base import Base
from models import TransactionType


class Transaction(Base):
    __tablename__ = "transaction"

    id = Column(Integer, primary_key=True)
    transaction_key = Column(CHAR(36), nullable=False)
    transaction_type_id = Column(Integer, ForeignKey(TransactionType.id), nullable=False)
    request_control_key = Column(CHAR(36), nullable=True)
    request_hash = Column(CHAR(64), nullable=True)
    accounting_date = Column(Date, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.clock_timestamp())

    __table_args__ = (
        UniqueConstraint("transaction_key"),
        UniqueConstraint("request_control_key"),
    )

    transaction_type = relationship("TransactionType", foreign_keys=[transaction_type_id], lazy="selectin")
