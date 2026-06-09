import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, Float
from app.db.base import Base
from app.db.types import GUID


class DriverLocation(Base):
    __tablename__ = "driver_locations"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    driver_id = Column(GUID, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)
