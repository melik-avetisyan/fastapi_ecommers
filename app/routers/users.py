from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.auth.depends import get_auth_service, AuthService
from app.schemas import User as UserSchema, UserCreate


router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserSchema,
             status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):

    """реализация процедуры создания нового пользователя"""

    user_instance = await auth_service.create_user(
        user_schema=user
    )

    return user_instance
