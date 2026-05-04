# Label Reader — Expo App

Mobile app for university mailrooms. Streams camera frames over WebSocket to your Django backend and displays the resolved building/location in real time.

---

## Setup

```bash
# Install dependencies
npm install

# Start the dev server
npx expo start
```

Then scan the QR code with **Expo Go** (iOS/Android) or press `i`/`a` for simulator.

---

## WebSocket Protocol

**Endpoint:** `ws://<your-server>:8000/ws/ocr`

**Sent by app → server** (JSON, every ~800ms while scanning):
```json
{ "image": "<base64-encoded JPEG string>" }
```
Images are resized to 640px wide before sending to keep payload small.

**Expected from server → app** (JSON):
```json
{ "building": "Science Hall 204", "confidence": 0.91 }
```

The app also handles these fallback shapes:
```json
{ "text": "any string" }      // shown as building, no confidence
{ "error": "message" }        // shown as error banner
"plain text string"           // shown as building, no confidence
```

---

## Changing the Server URL

Edit the constant at the top of `App.js`:

```js
const WS_URL = 'ws://localhost:8000/ws/ocr';
// For a real device on LAN, use your machine's local IP:
// const WS_URL = 'ws://192.168.1.42:8000/ws/ocr';
```

> **Note:** On a physical device, `localhost` refers to the phone itself, not your dev machine. Use your machine's LAN IP instead.

---

## UI

| Element | Behavior |
|---|---|
| **Connect** button | Opens WebSocket, turns green when live |
| **Big center button** | Starts/stops capture loop (blue = start, red square = stop) |
| **Clear** button | Dismisses the last result card |
| Status dot (top-right) | Grey = off, Yellow = connecting, Green = connected, Red = error |
| Result card | Slides up with building name + color-coded confidence |

---

## Dependencies

- `expo-camera` — live camera feed + `takePictureAsync`
- `expo-image-manipulator` — resize + base64 encode before sending
