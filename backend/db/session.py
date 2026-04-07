import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://truthtrace:password@127.0.0.1:5432/truthtracedb",
)

_engine_kwargs = {"future": True, "pool_pre_ping": True}
if DATABASE_URL.startswith("postgresql"):
    _engine_kwargs["connect_args"] = {"connect_timeout": 5}

engine = create_engine(DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
