"""Smart Parking System - dependency-free local web server and REST API."""

from __future__ import annotations

import json
import mimetypes
import random
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).parent
WEB_ROOT = ROOT / "web"


@dataclass
class Slot:
    id: int
    zone: str
    status: str = "available"
    booked_by: str = ""
    vehicle: str = ""


class ParkingState:
    """Thread-safe state shared by the UI and simulated IoT sensors."""

    def __init__(self, total: int = 12):
        self.lock = threading.Lock()
        self.slots = [Slot(i, "A" if i <= 6 else "B") for i in range(1, total + 1)]
        for number in (2, 5, 8, 11):
            if number <= total:
                self.slots[number - 1].status = "occupied"
                self.slots[number - 1].vehicle = "Detected by sensor"
        self.activity: list[dict] = []
        self._log("System online", "All parking sensors connected")

    def _log(self, title: str, detail: str):
        self.activity.insert(0, {
            "time": datetime.now().strftime("%H:%M:%S"),
            "title": title,
            "detail": detail,
        })
        del self.activity[12:]

    def snapshot(self) -> dict:
        with self.lock:
            slots = [asdict(slot) for slot in self.slots]
            counts = {name: sum(s.status == name for s in self.slots)
                      for name in ("available", "occupied", "booked")}
            return {"slots": slots, "counts": counts, "total": len(slots),
                    "activity": list(self.activity), "updated": datetime.now().isoformat()}

    def book(self, slot_id: int, name: str, vehicle: str) -> tuple[bool, str]:
        with self.lock:
            slot = self._find(slot_id)
            if not slot or slot.status != "available":
                return False, "That slot is no longer available."
            slot.status, slot.booked_by, slot.vehicle = "booked", name, vehicle.upper()
            self._log("Slot booked", f"{slot.zone}-{slot.id:02d} reserved for {vehicle.upper()}")
            return True, "Booking confirmed."

    def cancel(self, slot_id: int) -> tuple[bool, str]:
        with self.lock:
            slot = self._find(slot_id)
            if not slot or slot.status != "booked":
                return False, "Only booked slots can be cancelled."
            vehicle = slot.vehicle
            slot.status, slot.booked_by, slot.vehicle = "available", "", ""
            self._log("Booking cancelled", f"Slot {slot.zone}-{slot.id:02d} released ({vehicle})")
            return True, "Booking cancelled."

    def sensor_event(self, slot_id: int, occupied: bool) -> tuple[bool, str]:
        with self.lock:
            slot = self._find(slot_id)
            if not slot:
                return False, "Unknown slot."
            previous = slot.status
            if occupied:
                slot.status = "occupied"
                slot.booked_by = ""
                slot.vehicle = slot.vehicle or "Detected by sensor"
            else:
                slot.status, slot.booked_by, slot.vehicle = "available", "", ""
            action = "Vehicle entered" if occupied else "Vehicle exited"
            self._log(action, f"Sensor updated {slot.zone}-{slot.id:02d} ({previous} → {slot.status})")
            return True, f"Sensor event accepted for slot {slot_id}."

    def random_event(self) -> tuple[bool, str]:
        candidates = [s.id for s in self.slots if s.status != "booked"]
        slot_id = random.choice(candidates)
        current = self.slots[slot_id - 1].status
        return self.sensor_event(slot_id, current == "available")

    def _find(self, slot_id: int) -> Slot | None:
        return next((s for s in self.slots if s.id == slot_id), None)


STATE = ParkingState()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args):
        return

    def _json(self, payload: dict, status: int = 200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict:
        size = int(self.headers.get("Content-Length", "0"))
        try:
            return json.loads(self.rfile.read(size) or b"{}")
        except json.JSONDecodeError:
            return {}

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/status":
            return self._json(STATE.snapshot())
        if path == "/api/health":
            return self._json({"status": "ok", "service": "smart-parking"})
        self._serve_static(path)

    def do_POST(self):
        path = urlparse(self.path).path
        data = self._body()
        try:
            if path == "/api/simulate":
                ok, message = STATE.random_event()
            elif path == "/api/sensor-event":
                ok, message = STATE.sensor_event(int(data.get("slot", 0)), bool(data.get("occupied")))
            elif path.startswith("/api/slots/"):
                parts = path.strip("/").split("/")
                slot_id, action = int(parts[2]), parts[3]
                if action == "book":
                    name = str(data.get("name", "")).strip()
                    vehicle = str(data.get("vehicle", "")).strip()
                    if not name or not vehicle:
                        return self._json({"ok": False, "message": "Name and vehicle number are required."}, 400)
                    ok, message = STATE.book(slot_id, name, vehicle)
                elif action == "cancel":
                    ok, message = STATE.cancel(slot_id)
                else:
                    raise ValueError("Unknown action")
            else:
                return self._json({"ok": False, "message": "Endpoint not found."}, 404)
            return self._json({"ok": ok, "message": message, "data": STATE.snapshot()}, 200 if ok else 409)
        except (ValueError, IndexError):
            self._json({"ok": False, "message": "Invalid request."}, 400)

    def _serve_static(self, path: str):
        relative = "index.html" if path == "/" else path.lstrip("/")
        target = (WEB_ROOT / relative).resolve()
        if WEB_ROOT.resolve() not in target.parents or not target.is_file():
            return self._json({"message": "Not found"}, 404)
        content = target.read_bytes()
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def run(host: str = "127.0.0.1", port: int = 8000):
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Smart Parking System running at http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
