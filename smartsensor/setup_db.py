from sqlalchemy import create_engine, Column, Integer, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime


DB_SOURCE = "sqlite:///smartsensor.db"


engine = create_engine(DB_SOURCE)
Base = declarative_base()


class Measurement(Base):
    __tablename__ = "measurements"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now)
    temperature = Column(Float)
    humidity = Column(Float)

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print(f"Database created: {DB_SOURCE}")
