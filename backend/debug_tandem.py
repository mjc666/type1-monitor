import os
import logging
import json
from dotenv import load_dotenv
from tconnectsync.api import TConnectApi

load_dotenv()
logging.basicConfig(level=logging.INFO)

TCONNECT_USER = os.getenv("TCONNECT_USER")
TCONNECT_PASS = os.getenv("TCONNECT_PASS")

def debug_tandem():
    print("--- Tandem Deep Debug ---")
    tconnect = TConnectApi(TCONNECT_USER, TCONNECT_PASS)
    api = tconnect.tandemsource
    
    print(f"Pumper ID: {api.pumperId}")
    
    info = api.pumper_info()
    print(f"Pumper Info: {json.dumps(info, indent=2)}")
    
    metadata = api.pump_event_metadata()
    print(f"Pump Metadata: {json.dumps(metadata, indent=2)}")
    
    if metadata:
        for m in metadata:
            device_id = m['tconnectDeviceId']
            print(f"\nChecking device: {device_id} ({m.get('modelNumber')})")
            print(f"Min Date: {m.get('minDateWithEvents')}, Max Date: {m.get('maxDateWithEvents')}")
            
            # Try to fetch events from its reported max date
            max_date = m.get('maxDateWithEvents')
            if max_date:
                events = api.pump_events(device_id, min_date=max_date, max_date=max_date)
                print(f"Events on {max_date}: {len(events)}")

if __name__ == "__main__":
    debug_tandem()
