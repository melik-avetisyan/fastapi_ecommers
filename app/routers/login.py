from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.depends import get_auth_service, AuthService
from app.schemas import (AccessRefreshResponse, AccessResponse, RefreshRequest,
                         RefreshResponse)

router = APIRouter(prefix="/login", tags=["logins"])


@router.post("/token", response_model=AccessRefreshResponse)
async def login(
    credentials: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):

    """реализовавыет процедуру аутентификации"""

    refresh_access_shcema = await auth_service.login(
        email=credentials.username,
        plain_password=credentials.password
    )

    return refresh_access_shcema


@router.post("/access", response_model=AccessResponse)
async def rotate_access(
    token: RefreshRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> AccessResponse:

    """реализация процедуры ротации access"""

    token = token.refresh_token

    access_token = await auth_service.rotate_access(token)

    access_token = AccessResponse(
            access_token=access_token,
            token_type="bearer"
        )

    return access_token


@router.post("/refresh", response_model=RefreshResponse)
async def rotate_refresh(
    token: RefreshRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> RefreshResponse:

    """реализация процедуры ротации refresh"""

    token = token.refresh_token

    refresh_token = await auth_service.rotate_refresh(token)

    refresh_token = RefreshResponse(
        refresh_token=refresh_token,
        token_type="bearer"
    )

    return refresh_token
