# Gps_QuecpythonCode

# EC200U MQTT GPS Tracker

## Overview

This project implements a GPS-based IoT device using the EC200U module. It acquires GPS coordinates, packages the data as JSON, and publishes it securely over MQTT to **AWS IoT Core** using **TLS authentication**.

Key Features:

- GPS acquisition with retry logic using the `Locator` module.
- Secure MQTT communication using SSL certificates.
- Publishes real-time location data to AWS IoT Core.
- Power control via GPIO signaling (DONE pin).

---

## Project Metadata

- **Project Name**: `EC200U_MQTT_GPS`
- **Version**: `1.0.0`
- **Device ID**: `99`

---

## Hardware Requirements

| Component         | Description                                   |
|------------------|-----------------------------------------------|
| EC200U Module     | LTE Cat.1 communication module with Python API |
| GPS Module        | Integrated or external GNSS receiver          |
| DONE Pin Circuit  | GPIO-controlled power latch or timer circuit  |
| AWS IoT Account   | For secure MQTT endpoint and credentials      |

---

## Software Dependencies

- `umqtt`: Lightweight MQTT library for EC200U Python
- `checkNet`: Network readiness utility
- `log`: Logging module
- `utime`: Time management
- `ujson`: JSON serialization
- `Locator`: Custom GPS interface
  
## MQTT Configuration

| Parameter       | Value                                                             |
|----------------|-------------------------------------------------------------------|
| Broker Address  | `a1tgjydixa0qkm-ats.iot.us-east-1.com` (AWS IoT Core endpoint)    |
| Port            | `8883` (MQTT over TLS)                                           |
| Client ID       | `iotconsole-83e0cb3d-3b1f-46ae-984f-d9cdbc01c2f2`                |
| Topic           | `GPS/DATA`                                                       |

### Sample MQTT Payload

```json
{
  "Device_id": 99,
  "Latitude": 37.7749,
  "Longitude": -122.4194,
  "Timestamp": "2025-05-31 14:35:22"
}
