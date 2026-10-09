from sqlalchemy import CHAR, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from models.base import Base
from models import Transaction


class Deposit(Base):
    __tablename__ = "deposits"

    id = Column(Integer, primary_key=True)
    deposit_key = Column(CHAR(36), nullable=False)
    transaction_id = Column(Integer, ForeignKey(Transaction.id), nullable=False)
    depositor_name = Column(String(255), nullable=False)
    depositor_document = Column(String(18), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("deposit_key"),
        UniqueConstraint("transaction_id"),
    )
