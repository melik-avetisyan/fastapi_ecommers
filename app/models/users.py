from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.declarative_base import Base
from app.utilities.enums import UserRole

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .products import Product
    from .sessions import Session
    from .reviews import Review


class User(Base):
    __tablename__ = "users"
    unique_field = "email"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(index=True, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    role: Mapped[str] = mapped_column(default=UserRole.BUYER.value)

    products: Mapped[list["Product"]] = relationship(back_populates="seller")
    sessions: Mapped[list["Session"]] = relationship(back_populates="user")
    reviews: Mapped[list["Review"]] = relationship(back_populates="user")
