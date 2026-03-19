import os
import logging
from datetime import datetime, timedelta
import arrow
from dotenv import load_dotenv
from pydexcom import Dexcom
from tconnectsync.api import TConnectApi
from tconnectsync.eventparser import events as eventtypes
from tconnectsync.parser.ciq_therapy_events import split_therapy_events
from apscheduler.schedulers.background import BackgroundScheduler
from db import SessionLocal
from models import GlucoseReading, PumpBolus, PumpBasal, PumpIOB, PumpStatus

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEXCOM_USER = os.getenv("DEXCOM_USER")
DEXCOM_PASS = os.getenv("DEXCOM_PASS")
TCONNECT_USER = os.getenv("TCONNECT_USER")
TCONNECT_PASS = os.getenv("TCONNECT_PASS")

def sync_dexcom():
    if not DEXCOM_USER or not DEXCOM_PASS:
        logger.warning("Dexcom credentials not set.")
        return

    try:
        # Use keyword arguments for pydexcom 0.5.1+
        logger.info("Syncing Dexcom...")
        dexcom = Dexcom(username=DEXCOM_USER, password=DEXCOM_PASS)
        readings = dexcom.get_glucose_readings(max_count=20)
        
        # Fallback: if no readings in history, try current
        if not readings:
            current = dexcom.get_current_glucose_reading()
            if current:
                readings = [current]

        db = SessionLocal()
        added_count = 0
        for r in readings:
            # Ensure naive datetime for comparison and truncate microseconds
            # MySQL DATETIME columns without precision truncate microseconds
            ts = r.datetime.replace(tzinfo=None, microsecond=0)
            exists = db.query(GlucoseReading).filter(GlucoseReading.timestamp == ts).first()
            if not exists:
                reading = GlucoseReading(
                    value=r.value,
                    trend=r.trend_description,
                    trend_arrow=r.trend_arrow,
                    timestamp=ts
                )
                db.add(reading)
                added_count += 1
        db.commit()
        db.close()
        logger.info(f"Dexcom sync complete. Added {added_count} new readings.")
    except Exception as e:
        logger.error(f"Dexcom sync failed: {e}")

def sync_tandem():
    if not TCONNECT_USER or not TCONNECT_PASS:
        logger.warning("Tandem credentials not set.")
        return

    try:
        logger.info("Syncing Tandem...")
        tconnect = TConnectApi(TCONNECT_USER, TCONNECT_PASS)
        api = tconnect.tandemsource
        
        metadata = api.pump_event_metadata()
        if not metadata:
            logger.warning("No Tandem pump metadata found.")
            return
        
        # Select the most recent device
        tconnect_device = None
        max_date_seen = None
        for pump in metadata:
            pump_date = arrow.get(pump['maxDateWithEvents'])
            if not tconnect_device or pump_date > max_date_seen:
                tconnect_device = pump
                max_date_seen = pump_date
        
        device_id = tconnect_device['tconnectDeviceId']
        logger.info(f"Using device {device_id} (Serial: {tconnect_device.get('serialNumber')}, Last Seen: {tconnect_device.get('maxDateWithEvents')})")
        
        # Sync window: last 3 days
        time_start = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        time_end = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        logger.info(f"Fetching Tandem events for device {device_id}...")
        # Fetch all events to ensure we catch everything for Mobi
        events = api.pump_events(device_id, min_date=time_start, max_date=time_end, fetch_all_event_types=True)
        
        db = SessionLocal()
        bolus_count = 0
        basal_count = 0
        latest_iob = None
        latest_iob_time = None
        latest_battery = None
        latest_battery_time = None

        for event in events:
            # Handle Boluses
            if isinstance(event, eventtypes.LidBolusCompleted):
                bolus_id = str(event.bolusid)
                exists = db.query(PumpBolus).filter(PumpBolus.bolus_id == bolus_id).first()
                if not exists:
                    dt = arrow.get(event.eventTimestamp).datetime.replace(tzinfo=None)
                    bolus = PumpBolus(
                        amount=event.insulindelivered,
                        bolus_id=bolus_id,
                        timestamp=dt
                    )
                    db.add(bolus)
                    bolus_count += 1
            
            # Handle Basal Rate Changes
            if isinstance(event, eventtypes.LidBasalRateChange):
                basal_id = str(event.raw.seqNum)
                exists = db.query(PumpBasal).filter(PumpBasal.basal_id == basal_id).first()
                if not exists:
                    dt = arrow.get(event.eventTimestamp).datetime.replace(tzinfo=None)
                    basal = PumpBasal(
                        rate=event.commandedbasalrate,
                        basal_id=basal_id,
                        timestamp=dt
                    )
                    db.add(basal)
                    basal_count += 1

            # Handle Battery Info
            if isinstance(event, eventtypes.LidDailyBasal):
                event_time = arrow.get(event.eventTimestamp).datetime.replace(tzinfo=None)
                if latest_battery_time is None or event_time > latest_battery_time:
                    latest_battery = int(100 * event.batteryChargePercent)
                    latest_battery_time = event_time

            # Track IOB (found on many event types, including LidDailyBasal)
            if hasattr(event, 'IOB'):
                event_time = arrow.get(event.eventTimestamp).datetime.replace(tzinfo=None)
                if latest_iob_time is None or event_time > latest_iob_time:
                    latest_iob = event.IOB
                    latest_iob_time = event_time

        # Record latest IOB entry
        if latest_iob is not None and latest_iob_time:
            # Only add if it's newer than the last one in DB
            last_db_iob = db.query(PumpIOB).order_by(PumpIOB.timestamp.desc()).first()
            if not last_db_iob or latest_iob_time > last_db_iob.timestamp:
                iob_entry = PumpIOB(
                    amount=latest_iob,
                    timestamp=latest_iob_time
                )
                db.add(iob_entry)

        # Record latest Battery entry
        if latest_battery is not None and latest_battery_time:
            last_db_status = db.query(PumpStatus).order_by(PumpStatus.timestamp.desc()).first()
            if not last_db_status or latest_battery_time > last_db_status.timestamp:
                status_entry = PumpStatus(
                    battery_percent=latest_battery,
                    timestamp=latest_battery_time
                )
                db.add(status_entry)

        db.commit()
        db.close()
        logger.info(f"Tandem sync complete. Boluses: {bolus_count}, Basals: {basal_count}, Battery: {latest_battery}%")
    except Exception as e:
        logger.error(f"Tandem sync failed: {e}")

def start_sync():
    scheduler = BackgroundScheduler()
    scheduler.add_job(sync_dexcom, 'interval', minutes=5)
    scheduler.add_job(sync_tandem, 'interval', minutes=5)
    scheduler.start()
    # Run once at startup
    sync_dexcom()
    sync_tandem()
