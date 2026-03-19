from sync_engine import sync_dexcom, sync_tandem
import logging

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    print("Starting manual sync...")
    sync_dexcom()
    sync_tandem()
    print("Sync complete.")
