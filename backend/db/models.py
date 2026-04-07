from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db.session import Base


class DatasetSample(Base):
    __tablename__ = "dataset_samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    label: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, default="text")
    split: Mapped[str] = mapped_column(String(16), nullable=False, default="unsplit", index=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AnalysisLog(Base):
    __tablename__ = "analysis_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    classification: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
