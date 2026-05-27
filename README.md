# Label Reader
### Intelligent Mail Label Scanning for University Mailrooms

**Stack:** React Native (Expo) • FastAPI • PostgreSQL + pg_trgm • EasyOCR • OpenCV

---

## 📋 To Do

| Priority | Task | Notes |
|----------|------|-------|
| High | Polish code into clean code | |
| High | Modularize the React Native app codebase | Break screens into focused components and services |
| High | Add CI/CD pipeline with main branch protection | Require PRs, block merges on failed pipeline |
| Medium | Create/Use more Pydantic models on/for returns | |

---

## Overview

Label Reader is a mobile-first application designed to assist university mailroom staff in quickly identifying package recipients and their campus locations. By pointing a device camera at a shipping label, the app extracts the recipient name via OCR and returns the correct building and room number in real time.

This solves a practical problem: new mailroom employees often lack the institutional knowledge to map every name to a campus location. Label Reader closes that gap instantly.

---

## Features

- Live camera feed with real-time frame capture and processing
- EasyOCR-powered text extraction with OpenCV preprocessing
- PostgreSQL trigram similarity search (`pg_trgm`) for fast fuzzy name matching
- WebSocket communication between the mobile client and FastAPI backend
- Confidence-colored result card indicating match quality
- Dark-themed mobile UI with animated scan frame overlay

---

## Architecture

### Data Flow

1. React Native captures a frame from the camera on button press
2. Frame is resized to 640px wide, encoded as base64 JPEG, and sent via WebSocket
3. FastAPI receives the payload and passes the image to the OCR pipeline
4. OpenCV preprocesses the image; EasyOCR extracts raw text lines
5. FastAPI filters noise and queries PostgreSQL line-by-line using `pg_trgm` similarity
6. Mobile app displays building, room, department, and confidence score to the user

### Tech Stack

| Layer | Technology | Role |
|-------|------------|------|
| Mobile Frontend | React Native (Expo) | Camera capture, WebSocket client, UI |
| Backend Framework | Python / FastAPI | Request routing, OCR orchestration, API |
| OCR Engine | EasyOCR + OpenCV | Text extraction and image preprocessing |
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
- **Database** — Postgres via Supabase
- **Mobile** — Distribute via Expo Go for internal testing; build with `eas build` for production

---

## Project Structure

```
label-reader/
├── FastAPI/
│   ├── ocr_services/          # EasyOCR + OpenCV pipeline
│   ├── socket_handlers/       # FastAPI WebSocket handlers
│   └── db/                    # asyncpg DB helpers & name lookup
└── mobile/
    ├── assets/
    ├── components/
    ├── hooks/
    ├── screens/
    ├── App.js                 # Main entry
    └── app.json               # Expo config + permissions
```

---
