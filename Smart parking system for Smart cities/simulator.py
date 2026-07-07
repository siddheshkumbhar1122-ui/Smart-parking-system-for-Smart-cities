"""IoT sensor simulator that publishes entry/exit data to the local cloud API."""

import argparse
import json
import random
import time
from urllib.error import URLError
from urllib.request import Request, urlopen


def publish(endpoint: str, slot: int, occupied: bool):
    payload = json.dumps({"slot": slot, "occupied": occupied}).encode()
    request = Request(endpoint, data=payload, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=5) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description="Simulate smart parking IoT sensors")
    parser.add_argument("--url", default="http://127.0.0.1:8000/api/sensor-event")
    parser.add_argument("--interval", type=float, default=5)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    occupied = set()
    print(f"Publishing simulated sensor data to {args.url}")
    while True:
        slot = random.randint(1, 12)
        is_occupied = slot not in occupied
        try:
            result = publish(args.url, slot, is_occupied)
            occupied.add(slot) if is_occupied else occupied.discard(slot)
            print(f"Slot {slot:02d}: {'occupied' if is_occupied else 'available'} — {result['message']}")
        except URLError as error:
            print(f"Could not reach server: {error.reason}. Start server.py first.")
        if args.once:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
