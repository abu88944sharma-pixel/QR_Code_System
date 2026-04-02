"""Role model - maps Auth0 role IDs to local role names (e.g. super_admin, admin)."""

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.db.base import Base, CommonMixin


class Role(CommonMixin, Base):
    __tablename__ = "roles"

    auth0_role_id = Column(String, unique=True, nullable=True)  # Auth0's unique role identifier
    auth0_role_name = Column(String, unique=True, index=True, nullable=False)

    users = relationship("User", back_populates="role")
