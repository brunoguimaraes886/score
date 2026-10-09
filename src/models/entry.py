from sqlalchemy import CHAR, BigInteger, Column, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import relationship
from models.base import Base
from models import Account, Category, EntryType, Transaction


class Entry(Base):
    __tablename__ = "entry"

    id = Column(Integer, primary_key=True)
    entry_key = Column(CHAR(36), nullable=False)
    transaction_id = Column(Integer, ForeignKey(Transaction.id), nullable=False)
    account_id = Column(Integer, ForeignKey(Account.id), nullable=False)
    entry_type_id = Column(Integer, ForeignKey(EntryType.id), nullable=False)
    category_id = Column(Integer, ForeignKey(Category.id), nullable=True)
    amount = Column(BigInteger, nullable=False)
    balance_after = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.clock_timestamp())

    __table_args__ = (UniqueConstraint("entry_key"),)

    entry_type = relationship("EntryType", foreign_keys=[entry_type_id], lazy="selectin")
