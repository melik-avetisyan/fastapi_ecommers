from decimal import Decimal

from sqlalchemy import String, Numeric, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.database.declarative_base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .categories import Category
    from .users import User
    from .reviews import Review


class Product(Base):

    __tablename__ = "products"
    unique_field = "id"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"),
                                             nullable=False)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"),
                                           nullable=False)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(200), nullable=True)
    stock: Mapped[int] = mapped_column(nullable=False)
    rating: Mapped[float] = mapped_column(server_default="0.0")
    is_active: Mapped[bool] = mapped_column(default=True)

    category: Mapped["Category"] = relationship(back_populates="products")
    seller: Mapped["User"] = relationship(back_populates="products")
    reviews: Mapped[list["Review"]] = relationship(back_populates="product")
