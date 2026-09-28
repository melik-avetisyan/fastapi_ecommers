from fastapi import HTTPException, status


class TokenException(HTTPException):

    """ошибка, покрывающая все сценарии в которых токены не валидны:

    -токен истек
    -не декодируется
    -нет поля sub у access
    -передан другой тип токена у access
    -нет поля session_id у refresh
    -нет поля jti у refresh
    -refresh токена нет в БД
    -сессии по session_id нет в БД
    -сессия истекла
    -сессия не в статусе 'active'

    """

    def __init__(self,
                 detail="Could not validate token",
                 error="invalid token",
                 payload=None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": f"Bearer error={error}"}
        )

        self.payload = payload


class CredentialsException(HTTPException):

    "ошибка ввода пароля при аутентификации"

    def __init__(self,
                 detail="Invalid password",
                 error="invalid password"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": f"error={error}"}

        )


class PermissionDenied(HTTPException):

    """
    ошибка запрета доступа к маршруту или действию, по роли или id пользователя
    """

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied for your {detail}"
        )


class NotFound(HTTPException):

    """
    шаблон ошибки при отсутствии активной записи в БД по значению
    уникального поля
    """

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{detail} not found or inactive"
        )


class IntegrityError(HTTPException):

    """ошибка при создании инстанса с существующим в БД значением
    уникального поля"""

    def __init__(self, detail="Name conflict"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class InternalError(HTTPException):

    """обертка для внутренних ошибок сервера"""

    def __init__(self, detail="Internal server error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class BadRequest(HTTPException):

    """обертка для ошибок запроса"""

    def __init__(self, detail):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )
