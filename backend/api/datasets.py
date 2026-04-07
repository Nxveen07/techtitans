import random
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException

from db.models import DatasetSample
from db.session import get_db


router = APIRouter(prefix="/api/v1/datasets", tags=["datasets"])


class DatasetSampleCreate(BaseModel):
    content: str = Field(min_length=5)
    label: str = Field(pattern="^(verified|suspicious|unverified)$")
    source_type: str = "text"
    split: str = "unsplit"


class DatasetSplitRequest(BaseModel):
    train_ratio: float = 0.8
    val_ratio: float = 0.1
    test_ratio: float = 0.1
    seed: int = 42


@router.post("/samples")
def create_sample(payload: DatasetSampleCreate, db: Session = Depends(get_db)):
    try:
        row = DatasetSample(
            content=payload.content.strip(),
            label=payload.label.strip(),
            source_type=payload.source_type.strip(),
            split=payload.split.strip(),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database unavailable. Check PostgreSQL connection.")
    return {"status": "success", "sample_id": row.id}


@router.get("/samples")
def list_samples(
    db: Session = Depends(get_db),
    label: str | None = Query(default=None),
    split: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    stmt = select(DatasetSample).order_by(DatasetSample.id.desc())
    if label:
        stmt = stmt.where(DatasetSample.label == label)
    if split:
        stmt = stmt.where(DatasetSample.split == split)
    try:
        rows = db.execute(stmt.offset(offset).limit(limit)).scalars().all()
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database unavailable. Check PostgreSQL connection.")

    data = [
        {
            "id": row.id,
            "content": row.content,
            "label": row.label,
            "source_type": row.source_type,
            "split": row.split,
            "created_at": row.created_at.isoformat() if isinstance(row.created_at, datetime) else None,
        }
        for row in rows
    ]
    return {"status": "success", "count": len(data), "items": data}


@router.post("/split")
def split_dataset(payload: DatasetSplitRequest, db: Session = Depends(get_db)):
    total = payload.train_ratio + payload.val_ratio + payload.test_ratio
    if abs(total - 1.0) > 1e-6:
        return {"status": "error", "detail": "train_ratio + val_ratio + test_ratio must equal 1.0"}

    try:
        rows = db.execute(select(DatasetSample)).scalars().all()
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database unavailable. Check PostgreSQL connection.")
    if not rows:
        return {"status": "error", "detail": "No samples available to split."}

    rng = random.Random(payload.seed)
    rng.shuffle(rows)

    n = len(rows)
    n_train = int(n * payload.train_ratio)
    n_val = int(n * payload.val_ratio)

    for idx, row in enumerate(rows):
        if idx < n_train:
            row.split = "train"
        elif idx < n_train + n_val:
            row.split = "val"
        else:
            row.split = "test"

    try:
        db.commit()
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database unavailable. Check PostgreSQL connection.")
    return {"status": "success", "total": n, "train": n_train, "val": n_val, "test": n - n_train - n_val}
