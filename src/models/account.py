from sqlalchemy import CHAR, BigInteger, Column, Date, DateTime, ForeignKey, Integer, UniqueConstraint, func, text
from sqlalchemy.orm import relationship
from models.base import Base
from models import AccountStatus, AccountType, Customer, PiggyRank


class Account(Base):
    __tablename__ = "account"

    id = Column(Integer, primary_key=True)
    account_key = Column(CHAR(36), nullable=False)
    account_type_id = Column(Integer, ForeignKey(AccountType.id), nullable=False)
    status_id = Column(Integer, ForeignKey(AccountStatus.id), nullable=False)
    customer_id = Column(Integer, ForeignKey(Customer.id), nullable=True)
    parent_account_id = Column(Integer, ForeignKey("account.id"), nullable=True)
    balance = Column(BigInteger, nullable=True)
    token_hash = Column(CHAR(64), nullable=True)
    xp = Column(BigInteger, nullable=False, server_default=text("0"))
    level = Column(Integer, nullable=False, server_default=text("0"))
    points_free = Column(Integer, nullable=False, server_default=text("0"))
    points_fee = Column(Integer, nullable=False, server_default=text("0"))
    points_chance = Column(Integer, nullable=False, server_default=text("0"))
    rank_id = Column(Integer, ForeignKey(PiggyRank.id), nullable=True)
    yield_rank_id = Column(Integer, ForeignKey(PiggyRank.id), nullable=True)
    piggy_record = Column(BigInteger, nullable=False, server_default=text("0"))
    grace_until = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("account_key"),
        UniqueConstraint("parent_account_id"),
    )

    account_type = relationship("AccountType", foreign_keys=[account_type_id], lazy="selectin")
    status = relationship("AccountStatus", foreign_keys=[status_id], lazy="selectin")
    rank = relationship("PiggyRank", foreign_keys=[rank_id], lazy="selectin")
    yield_rank = relationship("PiggyRank", foreign_keys=[yield_rank_id], lazy="selectin")
