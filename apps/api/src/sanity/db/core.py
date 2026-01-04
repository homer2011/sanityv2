from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.sanity.config import settings

# Create async database engine (connection factory)
engine = create_async_engine(
    settings.DB_URL,
    echo=True,
)

# Create async sessionmaker (session factory)
async_session_factory = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)
