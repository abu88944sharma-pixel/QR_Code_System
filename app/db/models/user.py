from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base, CommonMixin


class User(CommonMixin, Base):
    __tablename__ = "users"

    auth0_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    created_by = Column(String, nullable=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True, index=True)

    role = relationship("Role", back_populates="users")
    client = relationship("Client", back_populates="users")
