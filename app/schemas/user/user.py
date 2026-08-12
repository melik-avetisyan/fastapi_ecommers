from pydantic import BaseModel, Field, EmailStr, ConfigDict
from app.utilities.enums import UserRole


class UserCreate(BaseModel):

    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8,
                          description="Password, min 8 simbols")
    role: UserRole = Field(default=UserRole.BUYER.value,
                           description="buyer, seller, admin")


class User(BaseModel):

    id: int = Field(..., description="unique user id")
    email: EmailStr
    role: str
    is_active: bool = Field(..., description="active status")
    model_config = ConfigDict(from_attributes=True)
