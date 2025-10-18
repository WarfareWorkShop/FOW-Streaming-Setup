# Flames of War Streaming Setup

## Overview

This repository gathers the different experiments and prototypes required to build a streaming system for Flames of War matches.
The code currently provides only the building blocks for future iterations and does **not** implement the full experience
described in earlier drafts of the project.

## Project structure

- **backend/**: Flask application with authentication, advanced match management, dice processing and integrations with OpenAI, Anthropic and LM Studio.
- **frontend/src/App.js**: Control panel that centralises authentication, AI matches, dice scanning and tactical chat.
- **frontend/src/VoiceInteraction.js**: Live speech recognition component fully wired into the main UI.
- **backend/dice_service.py**: Service that processes dice images and produces overlays.
- **tools/streaming/***: Ready-to-use OBS/MistServer configuration files and deployment scripts.
- **tools/lanzadados/***: Hardware notes and prototypes for dice readers.

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
