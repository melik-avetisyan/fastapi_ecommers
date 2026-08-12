from pydantic import BaseModel


class AccessRefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class AccessResponse(BaseModel):
    access_token: str
    token_type: str


class RefreshResponse(BaseModel):
    refresh_token: str
    token_type: str
