from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import (select, func, BinaryExpression, UnaryExpression,
                        Function, cast, ColumnElement)
from sqlalchemy.orm import DeclarativeBase, InstrumentedAttribute
from sqlalchemy.dialects.postgresql import REGCONFIG

from app.models import (Category as CategoryModel,
                        Product as ProductModel,
                        User as UserModel,
                        RefreshToken as RefreshTokenModel,
                        Session as SessionModel,
                        Review as ReviewModel)

from app.utilities.enums import (DataBaseTables, ProductFilterParams,
                                 SortingParams, UniversalTableField)


class TableModels:

    categories = CategoryModel
    products = ProductModel
    users = UserModel
    refresh_tokens = RefreshTokenModel
    sessions = SessionModel
    reviews = ReviewModel


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

        instance = await self.session.scalars(stmt)
        instance = instance.one_or_none()

        return instance

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
                                      table: DataBaseTables,
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
                                         table: DataBaseTables,
                                         **conditions
                                         ) -> list[DeclarativeBase | None]:

        """обертка над _get_many_by_and_conditions + получает модель таблицы"""

        table_model = getattr(self.tables, table)

        if hasattr(table_model, "is_active"):
            conditions.update(is_active=True)

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
                            table: DataBaseTables,
                            **data
                            ) -> DeclarativeBase:

        """обертка над _create_record"""

        table_model = getattr(self.tables, table)

        record = await self._create_record(
            table=table_model,
            **data)

        return record

    async def create_record_in_transaction(self,
                                           table: DataBaseTables,
                                           **data
                                           ) -> DeclarativeBase:

        """обертка над _create_record_no_commit"""

        table_model = getattr(self.tables, table)

        record = await self._create_record_no_commit(
            table=table_model,
            **data
        )

        return record

    async def hard_delete_by_unique_field_value(self,
                                                table: DataBaseTables,
                                                value
                                                ) -> None:

        """проверяет наличие и передает инстанс для полного удаления"""

        instance = await self.get_one_by_unique_field(
            table=table,
            unique_field_value=value
        )
        if instance:
            await self._hard_delete(instance)

    async def soft_delete(self,
                          table: DataBaseTables,
                          unique_field_value) -> None:

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

    async def change_session_status(self,
                                    session_id: int,
                                    status: str
                                    ) -> DeclarativeBase | None:

        """принимает id клиентской сессии и новый статус для присвоения,
        присваивает и возвращает инстанс или None если в БД нет сессии"""

        changed_session = await self._change_one_field(
            table=SessionModel,
            unique_field_value=session_id,
            target_field="status",
            new_value=status)

        return changed_session

    async def recount_product_rating(self,
                                     product_id: int):

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

    async def total_in_table(self,
                             table: DataBaseTables,
                             filter_params: dict) -> int:

        """считает количество активных записей в таблице с фильтрами"""

        table_model: DeclarativeBase = getattr(self.tables, table)

        conditions = self.where_constructor(table_model,
                                            filter_params)

        stmt = (select(func.coalesce(func.count(), 0))
                .select_from(table_model)
                .where(*conditions)
                )

        count = await self.session.scalar(stmt)

        return count

    async def table_pagination(self,
                               table: DataBaseTables,
                               page_params: dict,
                               filter_params: dict,
                               sort_params: dict
                               ) -> list[DeclarativeBase]:

        """пагинация с фильтрами и сортировкой"""

        table_model: DeclarativeBase = getattr(self.tables, table)

        conditions = self.where_constructor(table_model, filter_params)

        sorting = self.sorting_constructor(table_model,
                                           sort_params,
                                           filter_params)

        stmt = (select(table_model)
                .where(*conditions)
                .order_by(*sorting)
                .offset((page_params["page"]-1) * page_params["limit"])
                .limit(page_params["limit"]))

        result = await self.session.scalars(stmt)

        result = result.all()

        return result

    def where_constructor(self,
                          table: DeclarativeBase,
                          filter_params: dict
                          ) -> list[BinaryExpression]:

        """
        Фабрика для сборки условий фильтрации для каждой таблицы
        """

        match table.__table__.name:
            case DataBaseTables.PRODUCT:
                conditions = self.product_where_conditions(filter_params)

        return conditions

    def product_where_conditions(self, filter_params
                                 ) -> list[BinaryExpression]:

        """
        Собирает условия фильтрации для таблицы Product из переданных
        параметров
        """

        conditions = []

        for key, value in filter_params.items():

            match key:
                case ProductFilterParams.CATEGORY_ID:
                    conditions.append(ProductModel.category_id == value)
                case ProductFilterParams.SELLER_ID:
                    conditions.append(ProductModel.seller_id == value)
                case ProductFilterParams.MIN_PRICE:
                    conditions.append(ProductModel.price >= value)
                case ProductFilterParams.MAX_PRICE:
                    conditions.append(ProductModel.price <= value)
                case ProductFilterParams.IN_STOCK:
                    conditions.append(ProductModel.stock > 0 if value
                                      else ProductModel.stock == 0)
                case ProductFilterParams.SEARCH:
                    ts_query = self.make_tsquery(value)
                    conditions.append(ProductModel.tsv.op('@@')(ts_query))

        conditions.append(ProductModel.is_active.is_(True))

        return conditions

    def sorting_constructor(self,
                            table_model: DeclarativeBase,
                            sort_params: dict,
                            condition_params: dict
                            ) -> list[ColumnElement]:

        """
        Формирует список условий сортировки по переданным колонкам
        и/или релевантности
        """

        sorting_list = self.make_sorting_list(table_model, sort_params)

        is_ranking = sort_params.get(SortingParams.IS_RANK, False)

        if is_ranking is True:

            search_value = condition_params[ProductFilterParams.SEARCH]

            sorting_list = self.add_rank_in_sorting(table_model,
                                                    sorting_list,
                                                    search_value)

        return sorting_list

    def add_rank_in_sorting(self,
                            table: DeclarativeBase,
                            sorting_list: list[UnaryExpression],
                            search_value: str
                            ) -> list[ColumnElement]:
        """
        Добавляет к сортировке по клонкам на первое место сортировку по
        значению ранга релевантности с использованием алгоритма cover density
        """

        search_column = getattr(table, UniversalTableField.TSV)

        ts_query = self.make_tsquery(search_value)
        rank = func.ts_rank_cd(search_column, ts_query).desc()

        sorting_list.insert(0, rank)

        return sorting_list

    def make_sorting_list(self,
                          table_model: DeclarativeBase,
                          sort_params: dict) -> list[ColumnElement]:

        """
        формирует список колонок в виде UnaryExpression для
        сортировки результата выборки
        """

        sorting = []

        is_descending: bool = sort_params[SortingParams.IS_DESCENDING]

        for field in sort_params[SortingParams.SORT_BY]:

            model_column = getattr(table_model, field)

            sort_param = (model_column.desc() if is_descending
                          else model_column)

            sorting.append(sort_param)

        return sorting

    def make_tsquery(self, value) -> Function:

        """Превращает строку в объект полнотекстового логического запроса"""

        result = func.websearch_to_tsquery(
            cast('english', REGCONFIG),
            value)

        return result
