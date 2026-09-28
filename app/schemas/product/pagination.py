from pydantic import BaseModel, Field, ConfigDict, model_validator
from app.schemas import Product
from app.utilities.enums import ProductSortField


class ProductPage(BaseModel):

    """Пагинация продуктов"""

    items: list[Product] = Field(..., description="Products on current page")
    page: int = Field(..., ge=1, description="Current page number")
    total_number: int = Field(..., ge=0, description="Total count of products")
    limit: int = Field(..., ge=1, le=100, description="Count of items on page")

    model_config = ConfigDict(from_attributes=True)


class ProductFilterParams(BaseModel):

    """Условия формирования запроса для пагинации"""

    category_id: int | None = Field(default=None,
                                    description="ID of target category")

    seller_id: int | None = Field(default=None,
                                  description="ID of target seller")

    min_price: int | None = Field(default=None, gt=1,
                                  description="Number of min price")

    max_price: int | None = Field(default=None, gt=1,
                                  description="Number of max price")

    search: str | None = Field(default=None, min_length=1,
                               description="Searsch by product name")

    in_stock: bool | None = Field(default=None,
                                  description="switch between on stock True"
                                  "and out of stock(False) filter")

    @model_validator(mode="after")
    def check_price_correspondence(self):
        if self.min_price is not None and self.max_price is not None:
            if self.min_price > self.max_price:
                raise ValueError("price error: the min price is"
                                 "higher then the max price")
        return self

    @model_validator(mode="after")
    def check_search_field(self):

        if self.search is not None:
            self.search = self.search.strip()

            if not self.search:
                self.search = None

        return self


class ProductPageParams(BaseModel):

    "Параметры страницы"

    page: int = Field(default=1, ge=1, description="Number of page")

    limit: int = Field(default=10, ge=1, le=100,
                       description="Amount of items on page")


class ProductSortParams(BaseModel):

    "Параметры сортировки результата запроса"

    sort_by: list[ProductSortField] = [ProductSortField.ID]

    is_descending: bool = Field(default=False, description="Sort direction")

    is_rank: bool = Field(default=False, description="Apply ranking")


class ParseProductPaginationParams(ProductFilterParams,
                                   ProductPageParams,
                                   ProductSortParams):

    "Принимает все query-params из запроса пользователя"

    pass


class ProductPaginationParams(BaseModel):

    """Группирует параметры запроса по моделям"""

    page_params: ProductPageParams
    sort_params: ProductSortParams
    filter_params: ProductFilterParams
