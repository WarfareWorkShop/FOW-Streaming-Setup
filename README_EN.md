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

### Highlights

- Authentication with strengthened password policies and JWT issuance.
- Match API featuring AI opponents, invitations between users and detailed event logs.
- Integrated image processing to detect dice hits and generate overlay previews.
- End-to-end voice interaction: browser transcription, automatic action submission and spoken responses via Speech Synthesis.
- Tactical chat with support for OpenAI, Anthropic and LM Studio backends.
- React dashboard with match state visualisation, combat history and auxiliary tools.
- OBS/MistServer configurations plus automation scripts to recreate the streaming stack.
- Backend and frontend test suites complemented by a GitHub Actions workflow.

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

Set the following environment variables before launching Flask (a `.env` file is supported):

- `SECRET_KEY`: secret used by Flask and JWT.
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` or `LM_STUDIO_BASE_URL` depending on the provider you plan to use.
- `DATABASE_URI` if you want to replace the default SQLite database.

### Interactive helpers

Run `python launcher.py` from the repository root for a guided experience. The menu lets you install backend/frontend dependencies, start the servers and open the configuration assistant. The latter triggers `configurator.py`, which walks you through generating a `.env` file with all the required variables (secret keys, AI providers, etc.). When a previous `.env` is found the tool automatically creates a backup before overwriting it.

### Frontend

```bash
cd frontend
npm install
npm start
```

The React panel already ships with voice controls, match tracking and live overlays. Use `npm test` to run the frontend test suite.

## Automated tests

- Backend: `cd backend && pytest`
- Frontend: `cd frontend && npm test`

The `.github/workflows/ci.yml` workflow runs both suites on every pull request.

## Contributing

Contributions are welcome! Please open an issue to discuss your idea or submit a pull request with concrete improvements.

## License

This project is licensed under the BSD-3-Clause License. See the `LICENSE` file for details.
