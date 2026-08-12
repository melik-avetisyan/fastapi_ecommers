from datetime import datetime

from app.database.declarative_base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func, DateTime, ForeignKey

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .users import User
    from .products import Product


class Review(Base):
    __tablename__ = "reviews"
    unique_field = "id"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    comment: Mapped[str]
    comment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                   server_default=func.now())
    grade: Mapped[int]
    is_active: Mapped[bool] = mapped_column(default=True)

    user: Mapped["User"] = relationship(back_populates="reviews")
    product: Mapped["Product"] = relationship(back_populates="reviews")
