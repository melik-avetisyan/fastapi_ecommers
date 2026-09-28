from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.schemas import (ProductCreate, ProductUpdate, Review as ReviewSchema,
                         Product as ProductSchema, ProductPage
                         )
from app.models import (Product as ProductModel, Category as CategoryModel,
                        User as UserModel, Review as ReviewModel)

from app.database.depends import (get_async_session, get_data_service,
                                  DataService)
from app.auth.depends import validate_user_role
from app.utilities.enums import (UserRole, DataBaseTables, SortingParams,
                                 ProductFilterParams)
from app.exceptions.exceptions import NotFound, BadRequest
from app.service import parse_pagination_params


router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductPage,
            status_code=status.HTTP_200_OK)
async def read_products(data_service:
                        Annotated[DataService, Depends(get_data_service)],
                        params:
                        Annotated[parse_pagination_params, Depends()],
                        ):

    page_params = params.page_params.model_dump()
    sort_params = params.sort_params.model_dump()
    filter_params = params.filter_params.model_dump(exclude_none=True)

    if (sort_params.get(SortingParams.IS_RANK) is True and
       filter_params.get(ProductFilterParams.SEARCH, None) is None):

        raise BadRequest("Ranking attribute is true without search string")

    total_number = await data_service.total_in_table(
        table=DataBaseTables.PRODUCT,
        filter_params=filter_params
    )

    items = await data_service.table_pagination(
        table=DataBaseTables.PRODUCT,
        page_params=page_params,
        filter_params=filter_params,
        sort_params=sort_params
    )

    result = {
        "items": items,
        "total_number": total_number,
        "page": page_params["page"],
        "limit": page_params["limit"]
    }

    return result


@router.get("/{product_id}/", response_model=ProductSchema,
            status_code=status.HTTP_200_OK)
async def read_product(product_id: int,
                       session: AsyncSession = Depends(get_async_session)):

    stmt = (select(ProductModel)
            .where(ProductModel.id == product_id)
            .where(ProductModel.is_active.is_(True)))

    result = await session.scalars(stmt)
    product_instance = result.one_or_none()

    if product_instance is None:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Product not found or inactive")

    stmt = (select(CategoryModel)
            .where(CategoryModel.id == product_instance.category_id)
            .where(CategoryModel.is_active.is_(True)))

    result = await session.scalars(stmt)
    category_instance = result.one_or_none()

    if category_instance is None:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Category not found or inactive")

    return product_instance


@router.get("/category/{category_id}/", response_model=list[ProductSchema],
            status_code=status.HTTP_200_OK)
async def read_products_in_category(category_id: int,
                                    session: AsyncSession = Depends(
                                        get_async_session)):

    stmt = (select(CategoryModel)
            .where(CategoryModel.id == category_id)
            .where(CategoryModel.is_active.is_(True)))

    result = await session.scalars(stmt)
    category_instance = result.one_or_none()

    if category_instance is None:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Category not found or inactive")

    stmt = (select(ProductModel)
            .where(ProductModel.category_id == category_id)
            .where(ProductModel.is_active.is_(True)))

    result = await session.scalars(stmt)
    products_list = result.all()

    return products_list


@router.get("/{product_id}/reviews/", response_model=list[ReviewSchema],
            status_code=status.HTTP_200_OK)
async def read_reviews_in_product(product_id: int,
                                  data_service: Annotated[
                                      DataService, Depends(get_data_service)]
                                  ) -> list[ReviewModel]:

    product_instance = await data_service.get_one_by_unique_field(
        table=DataBaseTables.PRODUCT,
        unique_field_value=product_id
    )

    if not product_instance:
        raise NotFound(detail="Product")

    reviews = await data_service.get_many_by_and_conditions(
        table=DataBaseTables.REVIEW,
        product_id=product_id
        )

    return reviews


@router.post("", response_model=ProductSchema,
             status_code=status.HTTP_201_CREATED)
async def create_product(raw_product: ProductCreate,
                         session:
                         Annotated[AsyncSession, Depends(get_async_session)],
                         seller:
                         Annotated[UserModel, Depends(validate_user_role(
                                       roles=[UserRole.SELLER]))]
                         ):

    stmt = (select(CategoryModel)
            .where(CategoryModel.is_active.is_(True))
            .where(CategoryModel.id == raw_product.category_id))

    result = await session.scalars(stmt)

    category_instance = result.one_or_none()

    if category_instance is None:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Category not found or inactivate")

    product_instance = ProductModel(**raw_product.model_dump(),
                                    seller_id=seller.id)

    session.add(product_instance)
    await session.commit()
    await session.refresh(product_instance)

    return product_instance


@router.put("/{product_id}", response_model=ProductSchema,
            status_code=status.HTTP_200_OK)
async def update_product(product_id: int,
                         product_update: ProductUpdate,
                         session: Annotated[AsyncSession, Depends(
                             get_async_session)],
                         seller_instance: Annotated[UserModel, Depends(
                             validate_user_role(roles=[UserRole.SELLER])
                             )]):

    stmt = (select(ProductModel)
            .where(ProductModel.is_active.is_(True))
            .where(ProductModel.id == product_id))

    result = await session.scalars(stmt)
    product_instance = result.one_or_none()

    if product_instance is None:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Product not found or inactive")

    if product_instance.seller_id != seller_instance.id:

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Permission denied for your id")

    new_category_id = product_update.category_id

    if new_category_id:

        stmt = (select(CategoryModel)
                .where(CategoryModel.id == new_category_id)
                .where(CategoryModel.is_active.is_(True)))

        result = await session.scalars(stmt)
        category_instance = result.one_or_none()

        if category_instance is None:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Category not forund or inactive")

    update_data = product_update.model_dump(exclude_unset=True)

    if not update_data:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No data passed for update")

    stmt = (update(ProductModel)
            .where(ProductModel.id == product_id)
            .values(**update_data))

    await session.execute(stmt)
    await session.commit()
    await session.refresh(product_instance)

    return product_instance


@router.delete("/{product_id}", response_model=ProductSchema,
               status_code=status.HTTP_200_OK)
async def delete_product(product_id: int,
                         session: Annotated[AsyncSession, Depends(
                             get_async_session)],
                         seller: Annotated[UserModel, Depends(
                             validate_user_role(roles=[UserRole.SELLER])
                         )]):

    stmt = (select(ProductModel)
            .where(ProductModel.is_active.is_(True))
            .where(ProductModel.id == product_id))

    product_instance = await session.scalar(stmt)

    if product_instance is None:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Product not found or inactive")

    if product_instance.seller_id != seller.id:

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Permission denied")

    stmt = (update(ProductModel)
            .where(ProductModel.id == product_id)
            .values(is_active=False))

    await session.execute(stmt)
    await session.commit()
    await session.refresh(product_instance)

    return product_instance
