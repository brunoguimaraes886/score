from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint, func
from models.base import Base


class PiggyRank(Base):
    __tablename__ = "piggy_rank"

    id = Column(Integer, primary_key=True)
    enumerator = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("enumerator"),)

    DEFAULT = "DEFAULT"
    BRONZE = "BRONZE"
    SILVER = "SILVER"
    GOLD = "GOLD"
    PLATINUM = "PLATINUM"
    DIAMOND = "DIAMOND"
