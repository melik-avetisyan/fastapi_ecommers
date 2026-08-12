from pydantic import BaseModel, ConfigDict
from datetime import datetime


class RefreshCreate(BaseModel):

    session_id: int
    jti: str
    exp: datetime
    token_type: str


class Refresh(RefreshCreate):

    id: int
    model_config = ConfigDict(from_attributes=True)
