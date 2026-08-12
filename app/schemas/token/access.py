from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.utilities.enums import UserRole


class Access(BaseModel):

    sub: EmailStr
    role: UserRole
    token_type: str
    exp: datetime
