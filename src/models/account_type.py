from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint, func
from models.base import Base


class AccountType(Base):
    __tablename__ = "account_type"

    id = Column(Integer, primary_key=True)
    enumerator = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("enumerator"),)

    CUSTOMER = "CUSTOMER"
    PIGGY_BANK = "PIGGY_BANK"
    BANK = "BANK"
    OUTSIDE_WORLD = "OUTSIDE_WORLD"
