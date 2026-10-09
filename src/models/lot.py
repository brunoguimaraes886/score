from sqlalchemy import CHAR, BigInteger, Column, Date, DateTime, ForeignKey, Integer, Numeric, UniqueConstraint, func, text
from models.base import Base
from models import Category, Transaction


class Lot(Base):
    __tablename__ = "lot"

    id = Column(Integer, primary_key=True)
    lot_key = Column(CHAR(36), nullable=False)
    category_id = Column(Integer, ForeignKey(Category.id), nullable=False)
    transaction_id = Column(Integer, ForeignKey(Transaction.id), nullable=False)
    accounting_date = Column(Date, nullable=False)
    principal_remaining = Column(BigInteger, nullable=False)
    yield_remaining = Column(BigInteger, nullable=False, server_default=text("0"))
    residue = Column(Numeric(9, 8), nullable=False, server_default=text("0"))
    created_at = Column(DateTime, nullable=False, server_default=func.clock_timestamp())

    __table_args__ = (UniqueConstraint("lot_key"),)
