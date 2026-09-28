from enum import Enum


class UserRole(str, Enum):

    BUYER = "buyer"
    SELLER = "seller"
    ADMIN = "admin"


class SessionStatus(str, Enum):

    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class DataBaseTables(str, Enum):

    CATEGORY = "categories"
    PRODUCT = "products"
    USER = "users"
    REFRESH = "refresh_tokens"
    SESSION = "sessions"
    REVIEW = "reviews"


class TokenType(str, Enum):

    REFRESH = "refresh"
    ACCESS = "access"


class ErrorType(str, Enum):

    PRICE = 'price'


class ProductSortField(str, Enum):

    ID = "id"
    CREATED_AT = "created_at"
    PRICE = "price"


class ProductFilterParams(str, Enum):

    CATEGORY_ID = "category_id",
    SELLER_ID = "seller_id",
    MIN_PRICE = "min_price",
    MAX_PRICE = "max_price",
    IN_STOCK = "in_stock"
    SEARCH = "search"


class UniversalTableField(str, Enum):

    IS_ACTIVE = "is_active"
    TSV = "tsv"


class SortingParams(str, Enum):

    IS_DESCENDING = "is_descending"
    IS_RANK = "is_rank"
    SORT_BY = "sort_by"
