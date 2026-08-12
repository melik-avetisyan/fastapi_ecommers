from sqlalchemy import Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.declarative_base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .products import Product


class Category(Base):

    __tablename__ = "categories"
    unique_field = "id"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"),
                                                  nullable=True)
    name: Mapped[str] = mapped_column(String(50),
                                      nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    parent: Mapped["Category | None"] = relationship(back_populates="children",
                                                     remote_side="Category.id")
    children: Mapped[list["Category"]] = relationship(back_populates="parent")
    products: Mapped[list["Product"]] = relationship(back_populates="category")
