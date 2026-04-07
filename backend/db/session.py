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
if "postgresql" in DATABASE_URL:
    _engine_kwargs["connect_args"] = {"connect_timeout": 2}

# Use a failsafe engine creation
try:
    engine = create_engine(DATABASE_URL, **_engine_kwargs)
except Exception:
    # Fallback to a dummy sqlite in-memory if Postgres totally fails to initialize
    engine = create_engine("sqlite:///:memory:")

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
