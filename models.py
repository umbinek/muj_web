from sqlalchemy import create_engine, Column, Integer, Float, DateTime, String
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()

class Measurement(Base):
    __tablename__ = "measurements"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)
    temperature = Column(Float)
    humidity = Column(Float)

class AirQuality(Base):
    __tablename__ = "air_quality"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)
    value = Column(Float)
    unit = Column(String(10), default="ppm")

# This function create engine
def get_engine(db_uri):
    return create_engine(db_uri, connect_args={"check_same_thread": False})

# Define SessionLocal so that app.py can import it.
# Note: We then initialize it again in app.py with a specific engine.
SessionLocal = sessionmaker()
