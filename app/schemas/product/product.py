from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from datetime import datetime


class ProductCreate(BaseModel):

    name: str = Field(...,
                      min_length=3,
                      max_length=100,
                      description="product name form 3 to 100 symbols")

    description: str | None = Field(None,
                                    max_length=500,
                                    description="product description "
                                                "before 500 symbols")

    price: Decimal = Field(...,
                           gt=0,
                           description="product price more than 0",
                           decimal_places=2)
    image_url: str | None = Field(None,
                                  max_length=200,
                                  description="product image url")

    stock: int = Field(...,
                       ge=0,
                       description="product amount in stock")

    category_id: int = Field(...,
                             description="product category id")


class Product(ProductCreate):

    id: int = Field(...,
                    description="unique product id")
    seller_id: int = Field(...,
                           description="seller id")
    rating: float = Field(...,
                          description="product current rating")
    is_active: bool = Field(...,
                            description="active status")
    created_at: datetime = Field(...)

    updated_at: datetime | None = Field(default=None)

    model_config = ConfigDict(from_attributes=True)


class ProductUpdate(BaseModel):

    name: str | None = Field(None,
                             min_length=3,
                             max_length=100,
                             description="product name form 3 to 100 symbols")

    description: str | None = Field(None,
                                    max_length=500,
                                    description="product description "
                                                "before 500 symbols")

    price: Decimal | None = Field(None,
                                  gt=0,
                                  description="product price more than 0",
                                  decimal_places=2)

    image_url: str | None = Field(None,
                                  max_length=200,
                                  description="product image url")

    stock: int | None = Field(None,
                              ge=0,
                              description="product amount in stock")

    category_id: int | None = Field(None,
                                    description="product category id")
