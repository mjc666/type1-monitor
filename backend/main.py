import logging
from fastapi import FastAPI, Depends, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from db import init_db, get_db
from models import GlucoseReading, PumpBolus, PumpBasal, PumpIOB, PumpStatus
from sync_engine import start_sync, sync_dexcom, sync_tandem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Type1 Monitor API")

@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

@app.on_event("startup")
def on_startup():
    logger.info("Initializing database...")
    init_db()
    logger.info("Starting background sync...")
    start_sync()

@app.get("/api/status")
def get_status(db: Session = Depends(get_db)):
    latest_glucose = db.query(GlucoseReading).order_by(GlucoseReading.timestamp.desc()).first()
    latest_iob = db.query(PumpIOB).order_by(PumpIOB.timestamp.desc()).first()
    latest_status = db.query(PumpStatus).order_by(PumpStatus.timestamp.desc()).first()
    
    return {
        "glucose": latest_glucose,
        "iob": latest_iob,
        "pump_status": latest_status,
        "timestamp": datetime.now()
    }

@app.get("/api/history")
def get_history(hours: int = 24, db: Session = Depends(get_db)):
    start_time = datetime.now() - timedelta(hours=hours)
    
    glucose = db.query(GlucoseReading).filter(GlucoseReading.timestamp >= start_time).order_by(GlucoseReading.timestamp.asc()).all()
    boluses = db.query(PumpBolus).filter(PumpBolus.timestamp >= start_time).order_by(PumpBolus.timestamp.asc()).all()
    basals = db.query(PumpBasal).filter(PumpBasal.timestamp >= start_time).order_by(PumpBasal.timestamp.asc()).all()
    iob = db.query(PumpIOB).filter(PumpIOB.timestamp >= start_time).order_by(PumpIOB.timestamp.asc()).all()
    pump_status = db.query(PumpStatus).filter(PumpStatus.timestamp >= start_time).order_by(PumpStatus.timestamp.asc()).all()
    
    return {
        "glucose": glucose,
        "boluses": boluses,
        "basals": basals,
        "iob": iob,
        "pump_status": pump_status
    }

@app.post("/api/sync")
def trigger_sync():
    sync_dexcom()
    sync_tandem()
    return {"status": "Sync triggered"}

@app.get("/api/config")
def get_config_status():
    import os
    return {
        "dexcom_set": bool(os.getenv("DEXCOM_USER")),
        "tandem_set": bool(os.getenv("TCONNECT_USER")),
        "db_host": os.getenv("DB_HOST", "127.0.0.1")
    }
