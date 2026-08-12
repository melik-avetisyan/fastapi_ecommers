from datetime import datetime

from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.declarative_base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .sessions import Session


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    unique_field = "jti"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    jti: Mapped[str] = mapped_column(unique=True)
    exp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    token_type: Mapped[str]

    session: Mapped["Session"] = relationship(back_populates="refresh_token")
