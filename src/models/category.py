from sqlalchemy import CHAR, Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func, text
from sqlalchemy.orm import relationship
from models.base import Base
from models import Account, CategoryStatus


class Category(Base):
    __tablename__ = "category"

    id = Column(Integer, primary_key=True)
    category_key = Column(CHAR(36), nullable=False)
    account_id = Column(Integer, ForeignKey(Account.id), nullable=False)
    status_id = Column(Integer, ForeignKey(CategoryStatus.id), nullable=False)
    name = Column(String(255), nullable=False)
    is_default = Column(Boolean, nullable=False, server_default=text("false"))
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("category_key"),)

    status = relationship("CategoryStatus", foreign_keys=[status_id], lazy="selectin")
