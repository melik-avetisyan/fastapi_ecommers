from pydantic import BaseModel, Field, ConfigDict


class CategoryCreate(BaseModel):

    name: str = Field(...,
                      min_length=3,
                      max_length=50,
                      description="category name form 3 to 50 symbols")
    parent_id: int | None = Field(None,
                                  description="parent category id if exists")


class Category(CategoryCreate):

    id: int = Field(...,
                    description="unique category id")
    name: str = Field(...,
                      description="category name")
    is_active: bool = Field(...,
                            description="active status")

    model_config = ConfigDict(from_attributes=True)


class CategoryUpdate(BaseModel):

    name: str | None = Field(None,
                             min_length=3,
                             max_length=50,
                             description="category name form 3 to 50 symbols")
    parent_id: int | None = Field(None,
                                  description="parent category id if exists")
