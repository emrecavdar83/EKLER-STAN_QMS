
from soguk_oda_utils import _now
from datetime import datetime
import pytz

def check_time():
    print(f"System Now: {datetime.now()}")
    print(f"Istanbul Now (pytz): {datetime.now(pytz.timezone('Europe/Istanbul'))}")
    print(f"_now() helper: {_now()}")

if __name__ == "__main__":
    check_time()
