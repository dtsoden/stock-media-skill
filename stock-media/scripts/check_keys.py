"""Confirm both API keys load and work. Prints OK or FAILED, never a key."""
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stock_media_keys import SERVICES, get_key  # noqa: E402
from store_keys import test_key  # noqa: E402

failed = False
for service in SERVICES:
    ok, detail = test_key(service, get_key(service))
    print(f'{service}: {"OK" if ok else "FAILED"} ({detail})')
    failed |= not ok
sys.exit(1 if failed else 0)
