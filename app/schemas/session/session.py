from pydantic import BaseModel, ConfigDict
from datetime import datetime


class SessionCreate(BaseModel):

    user_id: int
    status: str
    exp: datetime


class Session(SessionCreate):

    id: int
    model_config = ConfigDict(from_attributes=True)
