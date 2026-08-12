from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, DateTime

from app.database.declarative_base import Base
from app.utilities.enums import SessionStatus


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .users import User
    from .refreshs import RefreshToken


class Session(Base):

    __tablename__ = "sessions"
    unique_field = "id"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    exp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(default=SessionStatus.ACTIVE.value)

    user: Mapped["User"] = relationship(back_populates="sessions")
    refresh_token: Mapped["RefreshToken"] = relationship(
                                                    back_populates="session",
                                                    uselist=False)
