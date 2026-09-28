from typing import Annotated
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import Depends

from .engine import async_session_fabric
from .service import DataService


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:

    """зависимость возвращает и после завершения работы обработчика
    закрывает сессию с БД"""

    async with async_session_fabric() as session:
        yield session


async def get_data_service(
        session: Annotated[AsyncSession, Depends(get_async_session)]
) -> DataService:

    """зависимость вернёт экземпляр класса для работы с БД -
    DataService, инициализированный ассинхронной сессией"""

    return DataService(session)
