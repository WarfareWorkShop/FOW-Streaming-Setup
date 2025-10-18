# Flames of War Streaming Setup

## Description

This repository collects the different experiments and prototypes required to build a streaming system for Flames of War matches. The code currently included covers basic features and serves as a starting point for future iterations.

## Project structure

- **backend/**: Flask application with hardened authentication, rate limits, and Flames of War-specific tactical endpoints.
- **frontend/src/App.js**: React tactical hub with session management, chat, list analyzer, virtual coach, and turn log.
- **frontend/src/VoiceInteraction.js**: Voice-recognition component integrated with the turn logging and chat flows.
- **frontend/imageprocessing.py**: Standalone script with OpenCV utilities for analyzing static images.
- **launcher.py**: Interactive launcher to install dependencies and start the servers.
- **configurator.py**: Assistant to create or update the project `.env` file.
- **tools/rolldice/***: Documentation and hardware prototypes for dice reading (not connected to the software).

## Current state of the features

### Key features

- Authentication with access and refresh JWTs, blacklist-based revocation, and protection against brute-force attacks.
- Authenticated `/api/chat` endpoint with content validations, block lists, and configurable rate limits.
- Tactical circuit with endpoints for scenario analysis, list evaluation, and contextual coaching.
- Persistent turn log to build a replay library and analyze post-match decisions.
- React interface with full login, tactical dashboard, integrated voice recognition, and shortcuts to external Flames of War tools.
- Flask-Migrate scripts and documentation to keep the database schema up to date.
- Automated tests for the core backend and frontend logic.

## Requirements

- Python 3.10+
- Node.js 18+
- SQLite (bundled with Python) or any SQLAlchemy-compatible database.
- Python dependencies listed in `backend/requirements.txt` (create a virtual environment and run `pip install -r requirements.txt`).

## AI configuration

The backend can connect to three different providers. Configure the environment variables before starting Flask:

- `DEFAULT_AI_PROVIDER`: `openai`, `anthropic`, or `lmstudio` (defaults to `openai`).
- `AI_REQUEST_TIMEOUT`: maximum wait time in seconds (defaults to `30`).

### Authentication and session management endpoints

The backend exposes JSON endpoints for user management. Responses use the `message` field to describe errors.

| Method & Route             | Description                                                                 | Security notes                                   |
| ------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------ |
| `POST /api/auth/register` | Registers a new user while enforcing password policies and optional CAPTCHA. | Set `RECAPTCHA_SECRET_KEY` to enable it.         |
| `POST /api/auth/login`    | Returns `accessToken`, `refreshToken`, and `expiresIn` when credentials are valid. | Blocks repeated failed attempts.                 |
| `POST /api/auth/refresh`  | Issues a new access token from the refresh token.                            | Send the refresh token in the `Authorization` header. |
| `POST /api/auth/logout`   | Revokes the current token by adding it to the blacklist.                     | Recommended when signing out from web clients.   |
| `GET /api/auth/me`        | Returns the `id`, `username`, and `email` of the authenticated user.         | Requires a valid access token.                   |

Tokens are issued with configurable expirations (`JWT_ACCESS_TOKEN_MINUTES`, `JWT_REFRESH_TOKEN_DAYS`). Every password change automatically revokes previously issued tokens.

### Tactical endpoints for Flames of War

All endpoints under `/api/tactics` require authentication and respect the limit defined in `TACTICS_RATE_LIMIT` (defaults to `20/minute`).

| Method & Route                       | Purpose                                                                                     |
| ----------------------------------- | ------------------------------------------------------------------------------------------- |
| `POST /api/tactics/scenario-advice` | Generates recommendations based on the structured battle state (turn, units, weather, terrain...). |
| `POST /api/tactics/army-list`       | Evaluates the synergy of an army list and suggests composition improvements.                |
| `POST /api/tactics/coach`           | Activates a coaching mode with a specific tactical role and returns personalized priorities and warnings. |
| `POST /api/tactics/logs`            | Saves a turn log with entries coming from the chat or voice input.                          |
| `GET /api/tactics/logs`             | Retrieves the most recent logs for the authenticated user.                                  |
| `DELETE /api/tactics/logs/<log_id>` | Deletes a previous log for the user.                                                        |

### Database configuration

The backend uses SQLite by default and creates a `site.db` file in the `backend` directory. You can start with this setup without making any additional changes. To use a different database (for example, PostgreSQL or MySQL), set the `DATABASE_URI` environment variable before launching the application. Examples:

- PostgreSQL: `export DATABASE_URI=postgresql+psycopg2://user:password@localhost:5432/fow`
- MySQL/MariaDB: `export DATABASE_URI=mysql+pymysql://user:password@localhost:3306/fow`

You can also define `SECRET_KEY` and `JWT_SECRET_KEY` if you want keys other than the defaults.

### Database migrations

The project integrates [Flask-Migrate](https://flask-migrate.readthedocs.io/) to manage schema evolution. Inside the `backend` directory you'll find scripts that simplify common commands:

- `scripts/db_init.sh`: initializes the migrations directory (only the first time).
- `scripts/db_migrate.sh "Message"`: generates a new migration with the given message.
- `scripts/db_upgrade.sh`: applies the pending migrations to the configured database.

All scripts assume they can be executed from any location and automatically set `FLASK_APP=app:create_app`.

### Test data and automatic bootstrapping

To create sample users and automate environment initialization, run:

```
cd backend
scripts/bootstrap.sh
```

The `bootstrap.sh` script applies migrations and runs `scripts/seed_users.py`, which creates sample users (`test_user` and `streamer`) when they don't already exist. If you need to create an additional user during seeding, set the `FIXTURE_CREATE_USER`, `FIXTURE_CREATE_EMAIL`, and optionally `FIXTURE_CREATE_PASSWORD` variables before running the script.

### Interactive assistants

If you prefer not to memorize commands, run `python launcher.py` from the repository root. The menu lets you install backend/frontend dependencies, start the servers, and open the configuration assistant. The latter invokes `configurator.py`, which guides you step by step through generating the `.env` file with the required variables (`SECRET_KEY`, AI providers, etc.). A backup is created automatically when a previous `.env` already exists.

## Configure the Frontend
- `OPENAI_API_KEY`: API key (required to use this provider).
- `OPENAI_MODEL`: model to use (defaults to `gpt-4o`).
- `OPENAI_BASE_URL`: base URL for the API (defaults to `https://api.openai.com/v1`).
- `OPENAI_TEMPERATURE`: generation temperature (defaults to `0.7`).

### Anthropic

- `ANTHROPIC_API_KEY`: API key (required to use this provider).
- `ANTHROPIC_MODEL`: model to use (defaults to `claude-3.7-Sonnet`).
- `ANTHROPIC_BASE_URL`: base URL for the API (defaults to `https://api.anthropic.com`).
- `ANTHROPIC_API_VERSION`: API version (defaults to `2023-06-01`).
- `ANTHROPIC_MAX_TOKENS`: maximum tokens per response (defaults to `1024`).
- `ANTHROPIC_TEMPERATURE`: generation temperature (defaults to `0.7`).

### LM Studio

- `LM_STUDIO_BASE_URL`: base URL for the local server (defaults to `http://localhost:1234/v1`).
- `LM_STUDIO_MODEL`: name of the model exposed by LM Studio (required to get useful responses).

## Getting started

### Interactive launcher

To simplify the first steps you can use the `launcher.py` script located in the repository root. You only need Python 3.10+ installed:

```bash
python launcher.py
```

The launcher displays a menu in Spanish where you can:

- Install backend dependencies (`pip install -r backend/requirements.txt`).
- Install frontend dependencies (`npm install`).
- Run the backend Flask server.
- Run the React development server.
- View a quick summary of the environment and the detected tools.

Each option explains how to stop the process (usually with `Ctrl+C`) to return to the main menu.

### Backend

```bash
cd backend
pip install -r requirements.txt
flask --app app run
```

Make sure you export the environment variables described in the previous section before starting.

### Frontend

```bash
cd frontend
npm install
npm start
```

## Automated tests

- Backend: `cd backend && pytest`
- Frontend: `cd frontend && npm test`

The `.github/workflows/ci.yml` workflow runs both suites on every pull request.

## Contributing

Contributions are welcome! Open an issue to discuss new ideas or submit a pull request with specific improvements.

## License

This project is licensed under the BSD-3-Clause License. See the `LICENSE` file for more details.
