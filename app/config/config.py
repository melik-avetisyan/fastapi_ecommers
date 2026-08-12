import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config():
    secret_key = os.getenv("SECRET_KEY")
    algorithm = os.getenv("ALGORITHM")
    expire_time = {
        "access": int(os.getenv("ACCESS_TOKEN_EXPIRE_MIN")),
        "refresh": int(os.getenv("REFRESH_TOKEN_EXPIRE_MIN")),
        "session": int(os.getenv("SESSION_EXPIRE_MIN"))}
