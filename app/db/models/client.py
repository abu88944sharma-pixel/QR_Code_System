from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.db.base import Base, CommonMixin


class Client(CommonMixin, Base):
    __tablename__ = "clients"

    client_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)

    users = relationship("User", back_populates="client")
