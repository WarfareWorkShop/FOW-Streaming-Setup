# Flames of War Streaming Setup

## Overview

This repository gathers the different experiments and prototypes required to build a streaming system for Flames of War matches.
The code currently provides only the building blocks for future iterations and does **not** implement the full experience
described in earlier drafts of the project.

## Project structure

- **backend/**: Flask application with user registration/login and a chat endpoint that returns a placeholder response.
- **frontend/src/App.js**: Minimal React interface that sends text messages to the backend and renders the simulated reply.
- **frontend/src/VoiceInteraction.js**: Browser speech-recognition demo (not wired into the main app yet).
- **frontend/imageprocessing.py**: Standalone OpenCV script used to experiment with contour detection on static images.
- **launcher.py**: Interactive launcher to install dependencies and start the servers.
- **configurator.py**: Helper that creates or updates the project's `.env` file.
- **tools/lanzadados/***: Hardware notes and prototypes for dice reading (not connected to the software stack).

## Current functionality

### Implemented

- User registration and login backed by SQLite with JWT issuance.
- `/api/chat` endpoint that returns a mock response for frontend-backend integration tests.
- Simple React UI to send a message and display the mocked response.
- Voice recognition example using `webkitSpeechRecognition`.
- Image-processing helper that detects contours and saves a processed image to disk.

### TODO / Next steps

- **Real OpenAI integration**: call the API, handle credentials securely and surface errors to the client.
- **AI opponent gameplay**: define game flow, turn handling and persistence of match state.
- **Real-time image processing**: connect `imageprocessing.py` to the backend to automate dice/result detection.
- **End-to-end voice interaction**: wire `VoiceInteraction.js` into the API and support spoken responses.
- **Streaming configuration (OBS + Mist Server)**: provide actual configuration files/scripts and automation steps.
- **Advanced user & match management**: roles, invitations, matchmaking and session persistence.
- **Automated testing & deployment**: add backend/frontend test suites and CI/CD pipelines.

## Requirements

- Python 3.10+
- Node.js 18+
- SQLite (bundled with Python) or any SQLAlchemy-compatible database.

## Getting started

### Backend

```bash
cd backend
pip install -r requirements.txt
flask --app app run
```

> **TODO**: set environment variables for `SECRET_KEY`, `DATABASE_URI` and the OpenAI key once the real integration is in place.

### Interactive helpers

Run `python launcher.py` from the repository root for a guided experience. The menu lets you install backend/frontend dependencies, start the servers and open the configuration assistant. The latter triggers `configurator.py`, which walks you through generating a `.env` file with all the required variables (secret keys, AI providers, etc.). When a previous `.env` is found the tool automatically creates a backup before overwriting it.

### Frontend

```bash
cd frontend
npm install
npm start
```

> **TODO**: extend the React app to include voice controls, match state management and visual overlays.

## Contributing

Contributions are welcome! Please open an issue to discuss your idea or submit a pull request with concrete improvements.

## License

This project is licensed under the BSD-3-Clause License. See the `LICENSE` file for details.
