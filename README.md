# Label Reader
### Intelligent Mail Label Scanning for University Mailrooms

**Stack:** React Native (Expo) • Django • PostgreSQL + pg_trgm • EasyOCR • OpenCV • RapidFuzz

---

## 📋 To Do

| Priority | Task | Notes |
|----------|------|-------|
| High | Polish code into clean code |
| High | Modularize the React Native app codebase | Break App.js into focused components and services |
| High | Add CI/CD pipeline with main branch protection | Require PRs, block merges on failed pipeline |
| High | Integration & unit testing with Pytest | Cover OCR pipeline, DB lookups, WebSocket handlers |
| Medium | Create/Use more Pydantic models on/for returns |

---

## Overview

Label Reader is a mobile-first application designed to assist university mailroom staff in quickly identifying package recipients and their campus locations. By pointing a device camera at a shipping label, the app extracts the recipient name via OCR and returns the correct building and room number in real time.

This solves a practical problem: new mailroom employees often lack the institutional knowledge to map every name to a campus location. Label Reader closes that gap instantly.

---

## Features

- Live camera feed with real-time frame capture and processing
- EasyOCR-powered text extraction with OpenCV preprocessing
- PostgreSQL trigram similarity search (`pg_trgm`) for fast fuzzy name matching
- RapidFuzz post-processing for additional confidence scoring
- WebSocket communication between the mobile client and Django backend
- Confidence-colored result card indicating match quality
- Dark-themed mobile UI with animated scan frame overlay

---

## Architecture

### Data Flow

1. React Native captures a frame from the camera every N seconds
2. Frame is resized to 640px wide, encoded as base64 JPEG, and sent via WebSocket
3. Django receives the payload and passes the image to the OCR pipeline
4. OpenCV preprocesses the image; EasyOCR extracts raw text lines
5. Django filters noise and queries PostgreSQL line-by-line using `pg_trgm` similarity
6. RapidFuzz re-scores results; best match returned as JSON
7. Mobile app displays building, room, and confidence score to the user

### Tech Stack

| Layer | Technology | Role |
|-------|------------|------|
| Mobile Frontend | React Native (Expo) | Camera capture, WebSocket client, UI |
| Backend Framework | Python / Django | Request routing, OCR orchestration, API |
| OCR Engine | EasyOCR + OpenCV | Text extraction and image preprocessing |
| Fuzzy Matching | RapidFuzz (Fuzz) | Post-DB confidence scoring |
| Database | PostgreSQL + pg_trgm | Name lookup with trigram similarity search |

---

## WebSocket Protocol

**Endpoint:**
```
ws://<host>:8000/ws/ocr
```

### Client → Server
```json
{ "image": "<base64-encoded JPEG string>" }
```

### Server → Client
```json
{ "name": "Solveig Olsen", "building": "Arts Center", "room": "204", "department": "Music", "confidence": 0.91 }
```
```json
{ "error": "No match found" }
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- PostgreSQL 14+ with the `pg_trgm` extension enabled
- Expo CLI — `npm install -g expo-cli`

### Backend Setup

```bash
git clone https://github.com/your-org/label-reader.git
cd label-reader/backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in DB credentials
python manage.py migrate
python manage.py runserver
```

### Enable pg_trgm

Run the following in your PostgreSQL database:

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

### Mobile App Setup

```bash
cd label-reader/mobile
npm install
# Edit the WS_URL constant in App.js to your backend LAN IP
npx expo start
```

> **Note:** For physical device testing, replace `localhost` with your machine's LAN IP address (e.g. `192.168.x.x`) in the WebSocket URL constant. Both devices must be on the same network.

---

## Database Schema

### `person` table

```sql
CREATE TABLE person (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    building    TEXT,
    room        TEXT,
    department  TEXT
);
```


```sql
CREATE INDEX person_name_trgm_idx ON person USING GIN (name gin_trgm_ops);
```

---

## Deployment

- **Backend** — Railway (verify EasyOCR model size fits within plan limits)
- **Database** — Railway PostgreSQL add-on or managed Postgres (Supabase, Neon, etc.)
- **Mobile** — Distribute via Expo Go for internal testing; build with `eas build` for production

---

## Project Structure

```
label-reader/
├── backend/
│   ├── ocr_services/          # EasyOCR + OpenCV pipeline
│   ├── socket_handlers/       # Django Channels WebSocket consumers
│   ├── db/                    # asyncpg DB helpers & lookupName
│   ├── person/                # Django app: models, views, admin
│   └── manage.py
└── mobile/
    ├── App.js                 # Main entry (to be modularised)
    ├── app.json               # Expo config + permissions
    └── assets/
```

---
