from typing import Annotated
from fastapi import APIRouter, Depends, status

from app.database.depends import DataService, get_data_service
from app.auth.depends import validate_user_role
from app.utilities.enums import DataBaseTables, UserRole
from app.schemas import ReviewCreate, Review as ReviewSchema
from app.models import (User as UserModel, Review as ReviewModel)
from app.exceptions.exceptions import BadRequest, NotFound, PermissionDenied


router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/", response_model=list[ReviewSchema])
async def read_reviews(data_service:
                       Annotated[DataService, Depends(get_data_service)]
                       ) -> list[ReviewModel]:

    """отдает список всех записей таблицы reviews согласно
    схеме ReviewSchema"""

    review_list = await data_service.get_many_by_and_conditions(
        table=DataBaseTables.REVIEW,
        is_active=True
    )

    return review_list


@router.post("/", status_code=status.HTTP_201_CREATED,
             response_model=ReviewSchema)
async def create_review(user:
                        Annotated[UserModel,
                                  Depends(validate_user_role(
                                      roles=[UserRole.BUYER]))],
                        data_service:
                        Annotated[DataService, Depends(get_data_service)],
                        review_create: ReviewCreate
                        ) -> ReviewModel:

    """
    валидирует роль пользователя - buyer;
    создает запись в таблице review и пересчитвает с присвоением поле grade
    продукта к которому создал отзыв.
    """

    product_id = review_create.product_id

    product_instance = await data_service.get_one_by_unique_field(
        table=DataBaseTables.PRODUCT,
        unique_field_value=product_id)

    if product_instance is None:
        raise BadRequest(detail="Invalid product_id")

    user_id = user.id

    review_instance = await data_service.create_record(
        table=DataBaseTables.REVIEW,
        **review_create.model_dump(),
        user_id=user_id)

    await data_service.recount_product_rating(product_id)

    return review_instance


@router.delete("/{review_id}")
async def delete_review(review_id: int,
                        user:
                        Annotated[UserModel, Depends(validate_user_role(
                            roles=[UserRole.BUYER, UserRole.ADMIN]))],
                        data_service:
                        Annotated[DataService, Depends(get_data_service)]
                        ) -> dict:

    """
    получает инстанс review, проверяет на существование и доступ
    пользователя к действию, удаляет отзыв и пересчитывает рейтинг
    """

    review_instance = await data_service.get_one_by_unique_field(
        table=DataBaseTables.REVIEW,
        unique_field_value=review_id
    )

    if review_instance is None:
        raise NotFound(detail="Review")

    if user.role == UserRole.BUYER and user.id != review_instance.user_id:
        raise PermissionDenied(detail="id")

    result = await data_service.soft_delete(
        table=DataBaseTables.REVIEW,
        unique_field_value=review_id
    )

    if not result:
        print(f"LOG: can't delete review {review_id}")

    await data_service.recount_product_rating(review_instance.product_id)

    return {"message": "Review deleted"}
