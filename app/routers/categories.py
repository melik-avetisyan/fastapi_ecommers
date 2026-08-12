from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.database.depends import get_async_session
from app.models import Category as CategoryModel
from app.models import User as UserModel
from app.schemas import (CategoryCreate, CategoryUpdate,
                         Category as CategorySchema)
from app.utilities.enums import UserRole
from app.auth.depends import validate_user_role

router = APIRouter(
    prefix="/categories",
    tags=["categories"]
)


@router.get("", response_model=list[CategorySchema])
async def read_categories(session: AsyncSession = Depends(get_async_session)):

    stmt = select(CategoryModel).where(CategoryModel.is_active.is_(True))
    result = await session.scalars(stmt)
    categories = result.all()

    return categories


@router.post("", response_model=CategorySchema,
             status_code=status.HTTP_201_CREATED)
async def create_category(category: CategoryCreate,
                          session: Annotated[AsyncSession, Depends(
                              get_async_session)],
                          _: Annotated[UserModel, Depends(
                              validate_user_role(roles=[UserRole.ADMIN])
                          )]):

    if category.parent_id is not None:

        stmt = (select(CategoryModel)
                .where(CategoryModel.id == category.parent_id)
                .where(CategoryModel.is_active.is_(True)))

        result = await session.execute(stmt)
        parent_category = result.first()

        if parent_category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Parent category not found")

    category_instance = CategoryModel(**category.model_dump())

    session.add(category_instance)
    await session.commit()

    return category_instance


@router.put("/{category_id}", response_model=CategorySchema)
async def update_category(category_id: int,
                          category_update: CategoryUpdate,
                          session: Annotated[AsyncSession, Depends(
                              get_async_session)],
                          _: Annotated[UserModel, Depends(
                              validate_user_role(roles=[UserRole.ADMIN])
                          )]):

    stmt = (select(CategoryModel)
            .where(CategoryModel.id == category_id)
            .where(CategoryModel.is_active.is_(True)))

    result = await session.scalars(stmt)
    category_instance = result.one_or_none()

    if category_instance is None:
        raise HTTPException(status_code=404, detail="Category not found")

    if category_instance.parent_id is not None:

        stmt = (select(CategoryModel)
                .where(CategoryModel.id == category_instance.parent_id)
                .where(CategoryModel.is_active.is_(True)))

        result = await session.scalars(stmt)
        parent_instance = result.one_or_none()

        if parent_instance is None:
            raise HTTPException(status_code=400,
                                detail="Parent category not found")

        if parent_instance.id == category_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Category can not be is is own parent")

    update_data = category_update.model_dump(exclude_unset=True)

    if not update_data:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No data passed for update")

    stmt = (update(CategoryModel)
            .where(CategoryModel.id == category_id)
            .values(**update_data))

    await session.execute(stmt)
    await session.commit()

    return category_instance


@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
async def delete_category(category_id: int,
                          session: Annotated[AsyncSession, Depends(
                              get_async_session)],
                          _: Annotated[UserModel, Depends(
                              validate_user_role(roles=[UserRole.ADMIN])
                          )]):

    stmt = (select(CategoryModel)
            .where(CategoryModel.id == category_id,
            CategoryModel.is_active.is_(True)))

    category_instance = await session.scalar(stmt)

    if not category_instance:
        raise HTTPException(status_code=404, detail="Category not found")

    stmt = (update(CategoryModel)
            .where(CategoryModel.id == category_id)
            .values(is_active=False))

    await session.execute(stmt)
    await session.commit()

    return {"status": "success", "message": "Category marked as inactive"}
