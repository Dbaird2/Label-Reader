# Label Reader
### Intelligent Mail Label Scanning for University Mailrooms

**Stack:** React Native (Expo) • FastAPI • PostgreSQL + pg_trgm • EasyOCR • OpenCV • OpenAI

---

## 📋 To Do

| Priority | Task | Notes |
|----------|------|-------|
| High | Polish code into clean code | |
| High | Modularize the React Native app codebase | Break screens into focused components and services |
| Medium | Create/Use more Pydantic models on/for returns | |

---

## Overview

Label Reader is a mobile-first application designed to assist university mailroom staff in quickly identifying package recipients and their campus locations. By pointing a device camera at a shipping label, the app extracts the recipient name via OCR and returns the correct building and room number in real time.

This solves a practical problem: new mailroom employees often lack the institutional knowledge to map every name to a campus location. When a name isn't found locally, the app uses an AI Agent to correct OCR errors automatically. Label Reader closes that gap instantly.

---

## Features

- Live camera feed with real-time frame capture and processing
- EasyOCR-powered text extraction with OpenCV preprocessing
- PostgreSQL trigram similarity search (`pg_trgm`) for fast fuzzy name matching
- **AI Agent fallback** — OpenAI-powered name correction when OCR doesn't match local database
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
6. **If no local match:** FastAPI invokes OpenAI to correct the OCR-extracted name
   - Agent receives the raw OCR text and attempts to fix common OCR errors
   - Returns the corrected name, which is then re-queried against the database
7. Mobile app displays building, room, department, and confidence score to the user

### Tech Stack

| Layer | Technology | Role |
|-------|------------|------|
| Mobile Frontend | React Native (Expo) | Camera capture, WebSocket client, UI |
| Backend Framework | Python / FastAPI | Request routing, OCR orchestration, API |
| OCR Engine | EasyOCR + OpenCV | Text extraction and image preprocessing |
| AI Agent | OpenAI GPT | OCR error correction and name normalization |
| Database | PostgreSQL + pg_trgm | Name lookup with trigram similarity search |

---

## WebSocket Protocol

### Client → Server
```json
{ "image": "<base64-encoded JPEG string>" }
```

### Server → Client (Local Match)
```json
{ "name": "Solveig Olsen", "building": "Arts Center", "room": "204", "department": "Music", "confidence": 0.91 }
```

### Server → Client (AI-Corrected Match)
```json
{ "name": "Sofia Olsson", "building": "Science Hall", "room": "118", "department": "Chemistry", "confidence": 0.78, "source": "ai_corrected" }
```

### Server → Client (No Match)
```json
{ "error": "No match found" }
```

---

## AI Agent — Name Correction

When OCR extraction doesn't match any names in the local database, FastAPI invokes OpenAI to correct the extracted text:

1. Receives the raw OCR text (e.g., "lvi Olsen", "Sophia 01sson")
2. Uses GPT to intelligently correct common OCR errors and normalize the name
3. Re-queries the database with the corrected name
4. Returns the match with building and room information

**Note:** Directory lookups via university systems are blocked by Cloudflare on Railway's IP range, so the agent relies purely on OCR error correction rather than external directory queries.

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
- **AI Agent** — OpenAI API (API key required in environment)
- **Mobile** — Distribute via Expo Go for internal testing; build with `eas build` for production

---

## Project Structure

```
label-reader/
├── FastAPI/
│   ├── ocr_services/          # EasyOCR + OpenCV pipeline
│   ├── services/              # OpenAI-powered name correction
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