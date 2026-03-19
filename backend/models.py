from sqlalchemy import Column, Integer, String, DateTime, Numeric, TIMESTAMP, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class GlucoseReading(Base):
    __tablename__ = "glucose_readings"
    id = Column(Integer, primary_key=True, index=True)
    value = Column(Integer, nullable=False)
    trend = Column(String(50))
    trend_arrow = Column(String(10))
    timestamp = Column(DateTime, nullable=False, unique=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

class PumpBolus(Base):
    __tablename__ = "pump_boluses"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    bolus_id = Column(String(100), unique=True, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

class PumpBasal(Base):
    __tablename__ = "pump_basals"
    id = Column(Integer, primary_key=True, index=True)
    rate = Column(Numeric(10, 2), nullable=False)
    basal_id = Column(String(100), unique=True, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

class PumpIOB(Base):
    __tablename__ = "pump_iob"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

class PumpStatus(Base):
    __tablename__ = "pump_status"
    id = Column(Integer, primary_key=True, index=True)
    battery_percent = Column(Integer)
    insulin_remaining = Column(Integer)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
