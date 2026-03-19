from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("--- Database Check ---")
    
    # Check glucose_readings
    result = conn.execute(text("SELECT COUNT(*) FROM glucose_readings"))
    count = result.scalar()
    print(f"Glucose readings: {count}")
    
    # Check pump_iob
    result = conn.execute(text("SELECT COUNT(*) FROM pump_iob"))
    count = result.scalar()
    print(f"Pump IOB entries: {count}")

    # Check pump_boluses
    result = conn.execute(text("SELECT COUNT(*) FROM pump_boluses"))
    count = result.scalar()
    print(f"Pump Boluses: {count}")
