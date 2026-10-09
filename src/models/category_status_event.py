from sqlalchemy import Column, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import relationship
from models.base import Base
from models import Category, CategoryStatus


class CategoryStatusEvent(Base):
    __tablename__ = "category_status_event"

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey(Category.id), nullable=False)
    status_id = Column(Integer, ForeignKey(CategoryStatus.id), nullable=False)
    event_datetime = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    status = relationship("CategoryStatus", foreign_keys=[status_id], lazy="selectin")
