from sqlalchemy import CHAR, Column, Date, DateTime, Integer, UniqueConstraint, func
from models.base import Base


class BankClock(Base):
    __tablename__ = "bank_clock"

    id = Column(Integer, primary_key=True)
    bank_clock_key = Column(CHAR(36), nullable=False)
    accounting_date = Column(Date, nullable=False)
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("bank_clock_key"),)
