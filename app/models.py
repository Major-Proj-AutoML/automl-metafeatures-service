from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class MetaFeaturesRecord(Base):
    __tablename__ = "meta_features"
    __table_args__ = (UniqueConstraint("dataset_id", name="uq_meta_features_dataset_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    features: Mapped[dict] = mapped_column(JSON, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
