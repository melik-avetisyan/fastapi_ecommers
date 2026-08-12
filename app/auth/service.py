import uuid
import jwt

from datetime import datetime, timedelta, timezone
from pwdlib import PasswordHash

from app.config.config import Config
from app.models import User as UserModel
from app.database.depends import DataService
from app.utilities.enums import SessionStatus, TokenType, DataBaseTables

from ..exceptions.exceptions import (CredentialsException, NotFound,
                                     IntegrityError, InternalError,
                                     TokenException)

from sqlalchemy.exc import (SQLAlchemyError,
                            IntegrityError as IntegrityErrorAlchemy)

from app.schemas import (SessionCreate, Session as SessionSchema,
                         RefreshCreate, Refresh as RefreshSchema,
                         UserCreate,
                         Access as AccessSchema,
                         AccessRefreshResponse,
                         RefreshRequest)


password_hash = PasswordHash.recommended()
config = Config()


def decode_token(token: str) -> dict:

    """декодирование(валидация токена на консистентность) и перехват ошибок"""

    try:
        payload = jwt.decode(token, config.secret_key,
                             algorithms=[config.algorithm])

    except jwt.ExpiredSignatureError:
        raise TokenException(detail="Access token has expired",
                             error="access expired")
    except jwt.InvalidTokenError:
        raise TokenException()

    return payload


def decode_exp_refresh(token: str) -> str:

    """попытка извлечения payload из истекшего токена"""

    try:
        payload = jwt.decode(token,
                             config.secret_key,
                             algorithms=[config.algorithm],
                             options={"verify_exp": False})
    except jwt.InvalidTokenError:
        raise TokenException()

    return payload


def hash_password(password: str) -> str:

    """хеширование пароля"""

    return password_hash.hash(password)


class AuthService:

    """
    функции и методы
    - создание нового пользователя
    - аутентификации statefull(храним refresh и сессию на сервере)
    - ротации access/refresh отдельно.
    """

    def __init__(self, data_service: DataService):

        """инициализация службой работы с БД"""

        self.data_service = data_service

    async def create_user(self, user_schema: UserCreate) -> UserModel:

        """создает запись пользователя проверяя предварительно поле email
        на наличие в БД и отрабатывает ошибку Integrity error в процессе
        создания пользователя"""

        user_instance = await self.data_service.get_user(
            email=user_schema.email)

        if user_instance is not None:
            raise IntegrityError("Email already registrated")

        user_schema.password = hash_password(user_schema.password)

        user_data = {
            "email": user_schema.email,
            "hashed_password": user_schema.password,
            "role": user_schema.role
        }

        try:
            user_instance = await self.data_service.create_record(
                table=DataBaseTables.USER,
                **user_data
            )

            return user_instance

        except IntegrityErrorAlchemy as e:

            constraint_name = e.orig.diag.constraint_name
            raise IntegrityError(f"{constraint_name} conflict")

        except SQLAlchemyError as e:

            print(f"{e} is logged here")
            raise InternalError()

    async def login(self, email: str, plain_password: str
                    ) -> AccessRefreshResponse:

        """
        в транзакции аутентифицирует пользователя и создает его сессию на
        сервере+refresh, при успешном завершении блока session.begin() будет
        выпущен commit, после создает access - возвращает пару токенов.
        """
        try:
            async with self.data_service.session.begin():

                user = await self.validate_user_credentials(
                    email=email,
                    plain_password=plain_password)

                session_schema = await self.create_session(user.id)
                refresh_token = await self.create_refresh(session_schema.id)

        except SQLAlchemyError as e:
            print(f"{e} is loged here")
            raise InternalError()

        access_token = self.create_access(user)

        refresh_access_shcema = AccessRefreshResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer")

        return refresh_access_shcema

    async def validate_user_credentials(self, email: str, plain_password: str
                                        ) -> UserModel:

        """по credentials проверяет существование пользователя(404 если нет)
        и корректность пароля(401 если ошибка там)"""

        user_instance = await self.data_service.get_user(email=email)

        if user_instance is None:
            raise NotFound(detail="User")

        if not password_hash.verify(plain_password,
                                    user_instance.hashed_password):
            CredentialsException()

        return user_instance

    async def create_session(self, user_id: int) -> SessionSchema:

        """создает сессию пользователя на сервере и добавляет в
        сессию sqlalchemy без commit"""

        expired = (datetime.now(timezone.utc) +
                   timedelta(minutes=config.expire_time["session"]))

        session_create = SessionCreate(user_id=user_id,
                                       status=SessionStatus.ACTIVE,
                                       exp=expired)

        session_instance = (
            await self.data_service.create_record_in_transaction(
                table=DataBaseTables.SESSION,
                **session_create.model_dump())
        )

        session_schema = SessionSchema.model_validate(session_instance)

        return session_schema

    async def create_refresh(self, session_id: int) -> str:

        """создает refresh токен привязанный к id сессии пользователя на
        сервере и добавляет в сессию sqlalchemy без commit"""

        expired = (datetime.now(timezone.utc) +
                   timedelta(minutes=config.expire_time["refresh"]))

        jti = str(uuid.uuid4())

        refresh_create = RefreshCreate(session_id=session_id,
                                       jti=jti,
                                       exp=expired,
                                       token_type=TokenType.REFRESH)

        refresh_instance = (
            await self.data_service.create_record_in_transaction(
                table=DataBaseTables.REFRESH,
                **refresh_create.model_dump())
        )

        refresh_schema = RefreshSchema.model_validate(refresh_instance)

        refresh_token = jwt.encode(refresh_schema.model_dump(),
                                   config.secret_key,
                                   config.algorithm)

        return refresh_token

    def create_access(self, user: UserModel) -> str:

        """создает access token привязанный к email пользователя, stateless"""

        expired = (datetime.now(timezone.utc) +
                   timedelta(minutes=config.expire_time["access"]))

        access_schema = AccessSchema(sub=user.email,
                                     role=user.role,
                                     token_type=TokenType.ACCESS,
                                     exp=expired)

        access_token = jwt.encode(access_schema.model_dump(),
                                  config.secret_key,
                                  config.algorithm)

        return access_token

    async def rotate_refresh(self, token: RefreshRequest) -> str:

        """
        принимает refresh и верифицирует refresh/сессию/пользователя,
        (во всех верификациях при любой ошибке TokenException 401+detail)

        - при ошибке верификации:
        удаляет refresh из БД, меняет статус сессии на expired, передает ошибку
        дальше

        - при успехе верификации:
        удаляет токен из БД, создает новый refresh с преждним session_id

        """

        try:
            payload = await self.verify_refresh(token)
            user_id = await self.verify_session(payload)
            _ = await self.verify_user(user_id, payload)

        except TokenException as e:

            payload = e.payload
            await self.delete_refresh(payload)
            await self.update_session_staus(payload,
                                            new_status=SessionStatus.EXPIRED)
            raise e

        await self.delete_refresh(payload)

        session_id = payload.get("session_id")

        async with self.data_service.session.begin():

            refresh_token = await self.create_refresh(session_id)

        return refresh_token

    async def verify_refresh(self, token: RefreshRequest) -> dict:

        """верификация(проверка) токена на то, что по значению jti
        находится(существует) токен в БД"""

        payload, jti = await self.validate_refresh(token)

        token_instance = await self.data_service.get_one_by_unique_field(
            table=DataBaseTables.REFRESH,
            unique_field_value=jti)

        if token_instance is None:

            raise TokenException(detail="Token don't exist",
                                 error="invalid token",
                                 payload=payload)

        return payload

    async def validate_refresh(self, token: RefreshRequest) -> tuple[str, int]:

        """валидация токена на срок, декодируемость и наличие все полей"""

        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            payload = decode_exp_refresh(token)
            raise TokenException(detail="Refresh token has expired",
                                 error="token expired",
                                 payload=payload)

        jti = payload.get("jti")
        session_id = payload.get("session_id")

        if jti is None:
            raise TokenException(detail="Empty required field jti",
                                 error="empty jti",
                                 payload=payload)
        if session_id is None:
            raise TokenException(detail="Empty required field session",
                                 error="empty session_id",
                                 payload=payload)

        return payload, jti

    async def verify_session(self, payload: dict) -> int:

        """верификация(проверка) сессии на существование в БД,
        статус active, срок жизни"""

        session_id = payload.get("session_id")

        session_instance = await self.data_service.get_one_by_unique_field(
            table=DataBaseTables.SESSION,
            unique_field_value=session_id)

        if session_instance is None:

            raise TokenException(detail="Session don't exist",
                                 error="session not found",
                                 payload=payload)

        if session_instance.status != SessionStatus.ACTIVE:

            raise TokenException(detail="Session not active",
                                 error="session not active",
                                 payload=payload)

        if session_instance.exp < datetime.now(timezone.utc):

            raise TokenException(detail="Session has expired",
                                 error="session expired",
                                 payload=payload)

        return session_instance.user_id

    async def verify_user(self, user_id: int, payload: dict) -> UserModel:

        """верификация(проверка) пользователя на существование в БД,
        статус active"""

        user_instance = await self.data_service.get_user(id=user_id)

        if not user_instance:
            raise TokenException(detail="Session has expired",
                                 error="session expired",
                                 payload=payload)

        return user_instance

    async def delete_refresh(self, payload: dict) -> None:

        """по уникальному полю jti удаляет refresh токен если он существует"""

        jti = payload.get("jti")

        if jti:
            await self.data_service.hard_delete_by_unique_field_value(
                table=DataBaseTables.REFRESH,
                value=jti
            )

    async def update_session_staus(self, payload: dict, new_status: str
                                   ) -> None:

        """меняет статус сессии на сервере или логирует отсутсвие сессии"""

        session_id = payload.get("session_id")

        if session_id:
            session_instance = await self.data_service.change_session_status(
                session_id=session_id,
                status=new_status
            )

            if session_instance is None:
                print(f"LOG: there is not session_id={session_id} \
                      in database but passed")

    async def rotate_access(self, token: RefreshRequest) -> str:

        """
        принимает refresh и верифицирует refresh/сессию/пользователя,
        (во всех верификациях при любой ошибке TokenException 401+detail)

        - при ошибке верификации:
        удаляет refresh из БД, меняет статус сессии на expired, передает ошибку
        дальше

        - при успехе верификации:
        создает новый access с преждним user и возвращает
        """

        try:
            payload = await self.verify_refresh(token)
            user_id = await self.verify_session(payload)
            user_instance = await self.verify_user(user_id, payload)

        except TokenException as e:
            payload = e.payload
            await self.delete_refresh(payload)
            await self.update_session_staus(payload,
                                            new_status=SessionStatus.EXPIRED)
            raise e

        access_token = self.create_access(user_instance)

        return access_token
