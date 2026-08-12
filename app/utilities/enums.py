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

    CATEGORY = "category"
    PRODUCT = "product"
    USER = "user"
    REFRESH = "refresh"
    SESSION = "session"
    REVIEW = "review"


class TokenType(str, Enum):

    REFRESH = "refresh"
    ACCESS = "access"
