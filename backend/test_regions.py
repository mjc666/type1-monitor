import os
import logging
from dotenv import load_dotenv
from pydexcom import Dexcom

# Configuration
load_dotenv()
logging.basicConfig(level=logging.INFO)

DEXCOM_USER = os.getenv("DEXCOM_USER")
DEXCOM_PASS = os.getenv("DEXCOM_PASS")

def test_dexcom():
    print("\n--- Testing Dexcom Regions ---")
    for region in ["us", "ous"]:
        print(f"Trying region: {region}")
        try:
            dexcom = Dexcom(username=DEXCOM_USER, password=DEXCOM_PASS, region=region)
            reading = dexcom.get_current_glucose_reading()
            if reading:
                print(f"Success ({region})! Current: {reading.value} mg/dL")
                return
            else:
                print(f"Authenticated ({region}), but no current reading.")
        except Exception as e:
            print(f"Region {region} failed: {e}")

if __name__ == "__main__":
    test_dexcom()
