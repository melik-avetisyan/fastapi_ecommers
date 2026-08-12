from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class ReviewCreate(BaseModel):

    product_id: int = Field(..., description="Id of linked product")
    comment: str = Field(..., description="Review comment")
    grade: int = Field(..., le=5, ge=1)


class Review(ReviewCreate):

    id: int = Field(..., description="Review id")
    user_id: int = Field(..., description="Reviewer's id")
    comment_date: datetime = Field(..., description="Review create date")
    is_active: bool = Field(..., decription="Review active status")

    model_config = ConfigDict(from_attributes=True)
