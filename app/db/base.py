from sqlalchemy import Boolean, Column, DateTime, Integer, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class CommonMixin:
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    delete_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, server_default=text("false"), default=False, nullable=False)
    is_active = Column(Boolean, server_default=text("true"), default=True, nullable=False)
