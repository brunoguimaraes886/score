from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint, func
from models.base import Base


class BlockReason(Base):
    __tablename__ = "block_reason"

    id = Column(Integer, primary_key=True)
    enumerator = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("enumerator"),)

    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"
    JUDICIAL_ORDER = "JUDICIAL_ORDER"
    CUSTOMER_REQUEST = "CUSTOMER_REQUEST"
    MANUAL_REVIEW = "MANUAL_REVIEW"
