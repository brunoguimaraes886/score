from sqlalchemy import CHAR, Column, DateTime, Integer, String, UniqueConstraint, func
from models.base import Base


class RequestLog(Base):
    __tablename__ = "request_log"

    id = Column(Integer, primary_key=True)
    request_log_key = Column(CHAR(36), nullable=False)
    request_id = Column(String(64), nullable=False)
    method = Column(String, nullable=False)
    path = Column(String, nullable=False)
    status = Column(Integer, nullable=False)
    error_code = Column(String(20), nullable=True)
    client_ip = Column(String(45), nullable=True)
    account_key = Column(String, nullable=True)
    auth_failure = Column(String(20), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("request_log_key"),)

    INTERNAL = "INTERNAL"
    ADMIN = "ADMIN"
    ACCOUNT = "ACCOUNT"
