from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import DeclarativeBase, InstrumentedAttribute

from app.models import (Category as CategoryModel,
                        Product as ProductModel,
                        User as UserModel,
                        RefreshToken as RefreshTokenModel,
                        Session as SessionModel,
                        Review as ReviewModel)


class TableModels:

    category = CategoryModel
    product = ProductModel
    user = UserModel
    refresh = RefreshTokenModel
    session = SessionModel
    review = ReviewModel


class AbstractDataService():

    """манипуляции с моделями таблиц, их инстансами и их полями"""

    tables = TableModels()

    async def _get_one_by_unique_field(self,
                                       table: DeclarativeBase,
                                       unique_field_name: str,
                                       unique_field_value
                                       ) -> DeclarativeBase | None:

        """
        забирает из БД один активный инстанс таблицы или ничего, параметры:
        таблица, название уникального поля, значание уникального поля.
        """

        field_model: InstrumentedAttribute = getattr(table, unique_field_name)

        stmt = select(table).where(field_model == unique_field_value)

        if hasattr(table, 'is_active'):

            stmt = stmt.where(table.is_active.is_(True))

        user_instance = await self.session.scalars(stmt)
        user_instance = user_instance.one_or_none()

        return user_instance

    async def _get_many_by_and_conditions(self,
                                          table: DeclarativeBase,
                                          **conditions_dict
                                          ) -> list[DeclarativeBase | None]:

        """отдает СПИСОК инстансов таблицы соответвсующих условиям,
        переданным в именованных аргументах функции, примененным через
        логическое AND"""

        conditions_list = [getattr(table, field_name) == value
                           for field_name, value in conditions_dict.items()]

        stmt = select(table).where(*conditions_list)

        result = await self.session.scalars(stmt)
        result = result.all()

        return result

    async def _create_record(self, table: DeclarativeBase, **data
                             ) -> DeclarativeBase:

        """создает одну запись переданной таблицы в стиле orm"""

        record = table(**data)

        self.session.add(record)
        await self.session.commit()

        return record

    async def _create_record_no_commit(self, table: DeclarativeBase, **data
                                       ) -> DeclarativeBase:

        """добавляет в сессию одну запись переданной таблицы в стиле orm
        без commit"""

        record = table(**data)

        self.session.add(record)
        await self.session.flush()

        return record

    async def _hard_delete(self, instance: DeclarativeBase) -> None:

        """окончаетльно удаляет переданный инстанс из БД"""

        await self.session.delete(instance)
        await self.session.commit()

    async def _soft_delete(self, instance: DeclarativeBase) -> None:

        """меняет поле is_active у переданного инстанса таблицы на False"""

        instance.is_active = False
        await self.session.commit()

    async def _change_one_field(self,
                                table: DeclarativeBase,
                                unique_field_value: int | str,
                                target_field: str,
                                new_value) -> DeclarativeBase | None:

        unique_field_name = getattr(table, "unique_field")

        instance = await self._get_one_by_unique_field(
            table=table,
            unique_field_name=unique_field_name,
            unique_field_value=unique_field_value
        )

        if instance:

            setattr(instance, target_field, new_value)

            await self.session.commit()

            return instance

        else:

            return None


class DataService(AbstractDataService):

    """
    принимает запросы на манипуляции с данными, переводит на мапперы использует
    методы более низкой абстракции
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_one_by_unique_field(self,
                                      table: str,
                                      unique_field_value
                                      ) -> DeclarativeBase | None:

        """обертка над _get_one_by_unique_field +
        - извлекает модель таблицы
        - имя уникального поля таблицы"""

        table_model = getattr(self.tables, table)
        unique_field_name = getattr(table_model, "unique_field")

        instance = await self._get_one_by_unique_field(
            table=table_model,
            unique_field_name=unique_field_name,
            unique_field_value=unique_field_value)

        return instance

    async def get_many_by_and_conditions(self,
                                         table: str,
                                         **conditions
                                         ) -> list[DeclarativeBase | None]:

        """обертка над _get_many_by_and_conditions + получает модель таблицы"""

        table_model = getattr(self.tables, table)

        result = await self._get_many_by_and_conditions(table_model,
                                                        **conditions)

        return result

    async def get_user(self,
                       email: str = None,
                       id: int = None) -> UserModel:

        """
        получает пользователя по переданному именованному аргументу,
        хранящему значение уникального поля(id или email)
        """

        field = "email" if email else "id"
        value = email if email else id

        user_instance = await self._get_one_by_unique_field(
            table=UserModel,
            unique_field_name=field,
            unique_field_value=value)

        return user_instance

    async def create_record(self,
                            table: str,
                            **data
                            ) -> DeclarativeBase:

        """обертка над _create_record"""

        table_model = getattr(self.tables, table)

        record = await self._create_record(
            table=table_model,
            **data)

        return record

    async def create_record_in_transaction(self, table: str, **data
                                           ) -> DeclarativeBase:

        """обертка над _create_record_no_commit"""

        table_model = getattr(self.tables, table)

        record = await self._create_record_no_commit(
            table=table_model,
            **data
        )

        return record

    async def hard_delete_by_unique_field_value(self,
                                                table: str,
                                                value
                                                ) -> None:

        """проверяет наличие и передает инстанс для полного удаления"""

        instance = await self.get_one_by_unique_field(
            table=table,
            unique_field_value=value
        )
        if instance:
            await self._hard_delete(instance)

    async def soft_delete(self, table: str, unique_field_value) -> None:

        """проверяет возможность мягкого удаления и передает инстанс
        в удаляющую функцию, возвращает булевый результат"""

        instance = await self.get_one_by_unique_field(
            table=table,
            unique_field_value=unique_field_value)

        if instance and hasattr(instance, "is_active"):

            await self._soft_delete(instance)

            return True
        else:
            return False

    async def change_session_status(self, session_id: int, status: str
                                    ) -> DeclarativeBase | None:

        """принимает id клиентской сессии и новый статус для присвоения,
        присваивает и возвращает инстанс или None если в БД нет сессии"""

        changed_session = await self._change_one_field(
            table=SessionModel,
            unique_field_value=session_id,
            target_field="status",
            new_value=status)

        return changed_session

    async def recount_product_rating(self, product_id: int):

        """получает средний рейтинг из таблицы review по id продукта и
        записывает значение в поле grade продукта"""

        stmt = (select(func.avg(ReviewModel.grade))
                .where(ReviewModel.product_id == product_id)
                .where(ReviewModel.is_active.is_(True)))

        average_grade = await self.session.scalar(stmt)

        average_grade = average_grade if average_grade is not None else 0.0

        changed_product = await self._change_one_field(
            table=ProductModel,
            unique_field_value=product_id,
            target_field="rating",
            new_value=average_grade
        )

        return changed_product
