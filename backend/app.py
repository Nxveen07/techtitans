from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.analyze import router as analyze_router
from api.datasets import router as datasets_router
from db.models import Base
from db.session import engine


app = FastAPI(title="TruthTrace AI", description="Backend APIs", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router)
app.include_router(datasets_router)


@app.get("/health")
def health_check():
    """Health check endpoint for frontend connection status."""
    return {"status": "ok", "message": "TruthTrace API is running"}


@app.on_event("startup")
def startup_init() -> None:
    try:
        Base.metadata.create_all(bind=engine)
        print("[INFO] Database tables initialized.")
    except Exception as exc:
        print(f"[WARN] Database initialization skipped: {exc}")
        print("[WARN] API will still run — DB-dependent endpoints will return 503 until DB is available.")
