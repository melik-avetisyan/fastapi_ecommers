from decimal import Decimal
from datetime import datetime

from sqlalchemy import (String, Numeric, ForeignKey, DateTime, func,
                        Computed, Index)
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.dialects.postgresql import TSVECTOR

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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now())

    tsv = mapped_column(
        TSVECTOR,
        Computed(
            """
            setweight(to_tsvector('english', coalesce(name, '') ), 'A')
            ||
            setweight(to_tsvector('english', coalesce(description, '')), 'B')
            """,
            persisted=True
        ),
        nullable=False
    )

    category: Mapped["Category"] = relationship(back_populates="products")
    seller: Mapped["User"] = relationship(back_populates="products")
    reviews: Mapped[list["Review"]] = relationship(back_populates="product")

    __table_args__ = (
        Index("idx_products_tsv_gin", "tsv", postgresql_using="gin"),
    )
