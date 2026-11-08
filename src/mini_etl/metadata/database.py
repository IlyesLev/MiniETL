import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

class Base(DeclarativeBase):
    pass

def create_metadata_engine():
    database_url = os.getenv("METADATA_DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "METADATA_DATABASE_URL is not configured"
        )

    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )


def create_session_factory(engine):
    return sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )
