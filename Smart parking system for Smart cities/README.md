# Smart Parking System for Smart Cities

A working IoT-style parking prototype built for the college project brief. It detects simulated vehicle entry/exit, shows live space availability, supports reservation/cancellation, and keeps a real-time activity feed.

## Run in VS Code

1. Open this folder in VS Code.
2. Open **Terminal → Run Task → Run Smart Parking System**.
3. Visit **http://127.0.0.1:8000** in a browser.

You can also start it directly with `python app.py`.

No package installation is required; the application uses Python's standard library.

To generate continuous IoT sensor data, open a second terminal and run:

```powershell
python simulator.py
```

Or click **Simulate sensor** in the dashboard for a single entry/exit event.

## Features

- Live counts for available, occupied, and reserved parking spaces
- Interactive two-zone floor map
- Book and cancel individual parking spaces
- Random vehicle entry/exit sensor simulation
- REST API representing the cloud-processing layer
- Activity timeline and automatic five-second UI refresh
- Responsive interface for desktop and mobile
- Importable Node-RED flow and IBM Cloud environment template
- Unit tests for booking, cancellation, and sensor events

## Architecture

```text
Python IoT Simulator ──POST──> Local Cloud API ──JSON──> Web Dashboard
        (sensor)                 (server.py)            (HTML/CSS/JS)

IBM Watson IoT ──> Node-RED ──POST──> Local Cloud API   [optional]
```

The local API replaces IBM Watson IoT during demonstration, allowing the project to work without an IBM Cloud account. `node-red/flows.json` can be imported into Node-RED and configured with IBM IoT credentials later.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/status` | Current slots, totals, and recent activity |
| GET | `/api/health` | Service health check |
| POST | `/api/slots/{id}/book` | Reserve an available slot |
| POST | `/api/slots/{id}/cancel` | Cancel a reservation |
| POST | `/api/sensor-event` | Publish `{\"slot\": 1, \"occupied\": true}` |
| POST | `/api/simulate` | Generate one random sensor event |

## Test

Run **Terminal → Run Task → Run Tests**, or:

```powershell
python -m unittest discover -s tests -v
```

## College demonstration flow

1. Explain that each parking slot has an occupancy sensor.
2. Run the dashboard and point out live slot totals.
3. Reserve an available slot with a driver and vehicle number.
4. Click **Simulate sensor** or run `simulator.py` to show IoT updates.
5. Explain that the REST API is the cloud layer; the included Node-RED flow connects the same app to IBM Watson IoT.
