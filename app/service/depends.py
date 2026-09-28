from typing import Annotated

from fastapi import Query
from app.schemas import (ParseProductPaginationParams,
                         ProductPaginationParams,
                         ProductFilterParams,
                         ProductPageParams,
                         ProductSortParams)


def parse_pagination_params(params:
                            Annotated[ParseProductPaginationParams, Query()]
                            ) -> ProductPaginationParams:

    data = params.model_dump()

    params = ProductPaginationParams(
        page_params=ProductPageParams.model_validate(data),
        sort_params=ProductSortParams.model_validate(data),
        filter_params=ProductFilterParams.model_validate(data)
    )

    return params
