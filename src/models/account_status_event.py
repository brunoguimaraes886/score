from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship
from models.base import Base
from models import Account, AccountStatus, BlockReason


class AccountStatusEvent(Base):
    __tablename__ = "account_status_event"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey(Account.id), nullable=False)
    status_id = Column(Integer, ForeignKey(AccountStatus.id), nullable=False)
    block_reason_id = Column(Integer, ForeignKey(BlockReason.id), nullable=True)
    source = Column(String(20), nullable=True)
    event_datetime = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.clock_timestamp())

    status = relationship("AccountStatus", foreign_keys=[status_id], lazy="selectin")
    block_reason = relationship("BlockReason", foreign_keys=[block_reason_id], lazy="selectin")

    MANUAL = "MANUAL"
    AUTOMATIC = "AUTOMATIC"
