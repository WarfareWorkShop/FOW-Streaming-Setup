"""Interactive helper to create or update the project's .env file."""

from __future__ import annotations

import secrets
import sys
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Callable, Dict, Iterable

from i18n import (
    determine_language_from_cli,
    format_language_list,
    translate,
)


PROJECT_ROOT = Path(__file__).resolve().parent
ENV_FILE = PROJECT_ROOT / ".env"

LANGUAGE, REMAINING_ARGS = determine_language_from_cli()
sys.argv = [sys.argv[0], *REMAINING_ARGS]
t = partial(translate, language=LANGUAGE)


@dataclass(frozen=True)
class ConfigField:
    """Representation of an environment variable requested from the user."""

    key: str
    prompt_key: str
    default: str | None = None
    required: bool = False
    note_key: str | None = None
    generator: Callable[[], str] | None = None


FIELDS: tuple[ConfigField, ...] = (
    ConfigField(
        key="SECRET_KEY",
        prompt_key="configurator.fields.secret_key.prompt",
        required=True,
        note_key="configurator.fields.secret_key.note",
        generator=lambda: secrets.token_urlsafe(32),
    ),
    ConfigField(
        key="DATABASE_URI",
        prompt_key="configurator.fields.database_uri.prompt",
        default="sqlite:///instance/app.db",
        note_key="configurator.fields.database_uri.note",
    ),
    ConfigField(
        key="DEFAULT_AI_PROVIDER",
        prompt_key="configurator.fields.default_ai_provider.prompt",
        default="openai",
    ),
    ConfigField(
        key="OPENAI_API_KEY",
        prompt_key="configurator.fields.openai_api_key.prompt",
        note_key="configurator.fields.openai_api_key.note",
    ),
    ConfigField(
        key="OPENAI_MODEL",
        prompt_key="configurator.fields.openai_model.prompt",
        default="gpt-3.5-turbo",
    ),
    ConfigField(
        key="ANTHROPIC_API_KEY",
        prompt_key="configurator.fields.anthropic_api_key.prompt",
        note_key="configurator.fields.anthropic_api_key.note",
    ),
    ConfigField(
        key="ANTHROPIC_MODEL",
        prompt_key="configurator.fields.anthropic_model.prompt",
        default="claude-3-haiku-20240307",
    ),
    ConfigField(
        key="LM_STUDIO_BASE_URL",
        prompt_key="configurator.fields.lm_studio_base_url.prompt",
        default="http://localhost:1234/v1",
    ),
    ConfigField(
        key="LM_STUDIO_MODEL",
        prompt_key="configurator.fields.lm_studio_model.prompt",
        default="local-model",
    ),
    ConfigField(
        key="AI_REQUEST_TIMEOUT",
        prompt_key="configurator.fields.ai_request_timeout.prompt",
        default="30",
    ),
)


def read_existing_values(path: Path) -> Dict[str, str]:
    """Parse a simple .env file with KEY=VALUE lines."""

    values: Dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()

    return values


def prompt_value(field: ConfigField, existing: Dict[str, str]) -> str | None:
    """Prompt the user for a configuration value."""

    current = existing.get(field.key)
    default_display = current or field.default or ""

    if field.note_key:
        note = t(field.note_key)
        print(f"\n📌 {note}")

    prompt_parts = [t(field.prompt_key)]
    if default_display:
        prompt_parts.append(f"[{default_display}]")
    prompt_text = " ".join(prompt_parts) + ": "

    while True:
        try:
            user_input = input(prompt_text).strip()
        except EOFError:
            print(t("configurator.input_abort_eof"))
            raise SystemExit(1) from None
        except KeyboardInterrupt:
            print(t("configurator.input_abort_interrupt"))
            raise SystemExit(1) from None

        if user_input:
            return user_input

        if current:
            return current

        if field.default:
            return field.default

        if field.generator:
            generated = field.generator()
            print(t("configurator.field_generated", key=field.key))
            return generated

        if field.required:
            print(t("configurator.field_required"))
            continue

        return None


def collect_values(fields: Iterable[ConfigField], existing: Dict[str, str]) -> Dict[str, str]:
    """Ask the user to fill in every requested field."""

    collected: Dict[str, str] = {}
    for field in fields:
        value = prompt_value(field, existing)
        if value is None:
            continue
        collected[field.key] = value
    return collected


def backup_file(path: Path) -> None:
    """Create a .bak copy of the previous file version."""

    backup = path.with_name(path.name + ".bak")
    backup.write_text(path.read_text(encoding="utf8"), encoding="utf8")
    print(t("configurator.backup_created", path=backup))


def write_env_file(path: Path, values: Dict[str, str]) -> None:
    """Write the collected values to disk."""

    header = t("configurator.file_header").splitlines() + [""]
    body = [f"{key}={value}" for key, value in values.items()]
    content = "\n".join(header + body) + "\n"
    path.write_text(content, encoding="utf8")


def main() -> None:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print(t("configurator.non_tty"))
        raise SystemExit(1)

    print(t("configurator.banner"), end="")
    print(t("configurator.language_hint", languages=format_language_list(LANGUAGE)))

    if ENV_FILE.exists():
        print(t("configurator.existing_file", path=ENV_FILE))
        print(t("configurator.existing_file_warning"))

    existing = read_existing_values(ENV_FILE)
    values = collect_values(FIELDS, existing)

    if ENV_FILE.exists():
        backup_file(ENV_FILE)

    write_env_file(ENV_FILE, values)
    print(t("configurator.completed", path=ENV_FILE))


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
