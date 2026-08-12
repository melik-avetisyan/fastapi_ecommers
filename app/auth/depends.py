from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.config.config import Config
from app.models import User as UserModel
from app.database.depends import get_data_service, DataService
from app.utilities.enums import UserRole, TokenType

from .service import AuthService, decode_token
from ..exceptions.exceptions import (TokenException,
                                     PermissionDenied,
                                     NotFound,
                                     )


config = Config()

oauth2_scheme = OAuth2PasswordBearer("login/token")


# блок с зависимостями для обработчиков:
# - валидации access и фабрика для верификции переданной роли пользователя
# - внедрения auth_service


def verify_access(
        token: Annotated[str, Depends(oauth2_scheme)]
                    ) -> dict:

    "декодирование и проверка токена на соответствие типа"

    payload = decode_token(token)

    _token_type = payload.get("token_type")

    if _token_type != TokenType.ACCESS:
        raise TokenException(detail="Expected access token",
                             error="invalid type")

    return payload


def get_sub_from_access(
        payload: Annotated[dict, Depends(verify_access)]
) -> str:

    """извлечение(и проверка наличия) поля sub из декодированного access"""

    email = payload.get("sub")

    if email is None:
        raise TokenException(detail="Expect sub field, but don't passed",
                             error="empty sub")

    return email


async def get_user(
        data_service: Annotated[DataService, Depends(get_data_service)],
        email: Annotated[str, Depends(get_sub_from_access)]
) -> UserModel | None:

    """верификаци(проверка существования) активного пользователя по email"""

    user_instance = await data_service.get_user(email=email)

    if user_instance is None:
        raise NotFound(detail="User")

    return user_instance


def validate_user_role(roles: list[UserRole]):

    """фабрика, принимающая спискок ролей для валидации вхождения
    поля user.role в переданный список"""

    async def check(user: Annotated[UserModel, Depends(get_user)]
                    ) -> UserModel:

        """
        проверка соответствия роли пользователя на переданный список,
        в ошибке указаны разрешенные роли.
        """

        if user.role not in roles:
            raise PermissionDenied(detail="role")

        return user

    return check


async def get_auth_service(
        data_service: Annotated[DataService, Depends(get_data_service)]
) -> AuthService:

    """зависимость для обслуживания аутентификации, ротации токенов и
    создания пользователя"""

    auth_service = AuthService(data_service)

    return auth_service
