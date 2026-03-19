import os
import logging
from datetime import datetime, timedelta
import arrow
from dotenv import load_dotenv
from pydexcom import Dexcom
from tconnectsync.api import TConnectApi
from tconnectsync.eventparser import events as eventtypes

# Configuration
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEXCOM_USER = os.getenv("DEXCOM_USER")
DEXCOM_PASS = os.getenv("DEXCOM_PASS")
TCONNECT_USER = os.getenv("TCONNECT_USER")
TCONNECT_PASS = os.getenv("TCONNECT_PASS")

def test_dexcom():
    print("\n--- Testing Dexcom Share ---")
    if not DEXCOM_USER or not DEXCOM_PASS:
        print("Error: Dexcom credentials not set.")
        return

    try:
        dexcom = Dexcom(username=DEXCOM_USER, password=DEXCOM_PASS)
        # get_glucose_readings doesn't have a minutes param in 0.5.1? 
        # Actually it takes max_count and minutes.
        readings = dexcom.get_glucose_readings(max_count=20, minutes=1440) # Last 24h
        print(f"Success! Fetched {len(readings)} readings.")
        for r in readings[:5]:
            print(f"Reading: {r.value} mg/dL at {r.datetime} ({r.trend_description})")
    except Exception as e:
        print(f"Dexcom failed: {e}")

def test_tandem():
    print("\n--- Testing Tandem Source ---")
    if not TCONNECT_USER or not TCONNECT_PASS:
        print("Error: Tandem credentials not set.")
        return

    try:
        tconnect = TConnectApi(TCONNECT_USER, TCONNECT_PASS)
        api = tconnect.tandemsource
        print("Authenticated with Tandem Source API.")
        
        metadata = api.pump_event_metadata()
        if not metadata:
            print("No pump metadata found.")
            return
        
        device_id = metadata[0]['tconnectDeviceId']
        print(f"Using device ID: {device_id}")

        # Try last 3 days
        time_start = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        time_end = datetime.now().strftime('%Y-%m-%d')

        print(f"Fetching pump events from {time_start} to {time_end}...")
        events = api.pump_events(device_id, min_date=time_start, max_date=time_end)
        
        boluses = []
        latest_iob = 0
        latest_iob_time = None

        for event in events:
            # Bolus
            if isinstance(event, eventtypes.LidBolusCompleted):
                boluses.append(event)
            
            # IOB tracking
            if hasattr(event, 'IOB'):
                latest_iob = event.IOB
                latest_iob_time = event.eventTimestamp

        print(f"Boluses found: {len(boluses)}")
        for b in boluses[:3]:
            print(f"Bolus: {b.insulindelivered} U at {b.eventTimestamp}")

        print(f"Latest IOB: {latest_iob} U at {latest_iob_time}")

    except Exception as e:
        print(f"Tandem failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dexcom()
    test_tandem()
