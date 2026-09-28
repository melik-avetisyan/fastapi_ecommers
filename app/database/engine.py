from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


DATABASE_URL = "postgresql+asyncpg://ecommerce_user:ecommerce_password" \
               "@localhost:5432/ecommerce_db"


async_engine = create_async_engine(DATABASE_URL, echo=True)
async_session_fabric = async_sessionmaker(async_engine, expire_on_commit=False)
