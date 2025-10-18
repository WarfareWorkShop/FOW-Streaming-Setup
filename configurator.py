"""Interactive helper to create or update the project's .env file."""

from __future__ import annotations

import secrets
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable


PROJECT_ROOT = Path(__file__).resolve().parent
ENV_FILE = PROJECT_ROOT / ".env"


@dataclass(frozen=True)
class ConfigField:
    """Representation of an environment variable requested from the user."""

    key: str
    prompt: str
    default: str | None = None
    required: bool = False
    note: str | None = None
    generator: Callable[[], str] | None = None


FIELDS: tuple[ConfigField, ...] = (
    ConfigField(
        key="SECRET_KEY",
        prompt="Clave secreta para Flask",
        required=True,
        note=(
            "Se utiliza para firmar cookies y tokens. Si dejas el campo en blanco "
            "se generará un valor aleatorio seguro."
        ),
        generator=lambda: secrets.token_urlsafe(32),
    ),
    ConfigField(
        key="DATABASE_URI",
        prompt="Cadena de conexión a la base de datos",
        default="sqlite:///instance/app.db",
        note="Acepta cualquier URI compatible con SQLAlchemy.",
    ),
    ConfigField(
        key="DEFAULT_AI_PROVIDER",
        prompt="Proveedor de IA predeterminado (openai/anthropic/lmstudio)",
        default="openai",
    ),
    ConfigField(
        key="OPENAI_API_KEY",
        prompt="Clave de API de OpenAI",
        note="Déjalo vacío si no vas a usar OpenAI por ahora.",
    ),
    ConfigField(
        key="OPENAI_MODEL",
        prompt="Modelo de OpenAI",
        default="gpt-3.5-turbo",
    ),
    ConfigField(
        key="ANTHROPIC_API_KEY",
        prompt="Clave de API de Anthropic",
        note="Déjalo vacío si no vas a usar Anthropic.",
    ),
    ConfigField(
        key="ANTHROPIC_MODEL",
        prompt="Modelo de Anthropic",
        default="claude-3-haiku-20240307",
    ),
    ConfigField(
        key="LM_STUDIO_BASE_URL",
        prompt="URL base para LM Studio",
        default="http://localhost:1234/v1",
    ),
    ConfigField(
        key="LM_STUDIO_MODEL",
        prompt="Modelo de LM Studio",
        default="local-model",
    ),
    ConfigField(
        key="AI_REQUEST_TIMEOUT",
        prompt="Tiempo de espera (segundos) para peticiones de IA",
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

    if field.note:
        print(f"\n📌 {field.note}")

    prompt_parts = [field.prompt]
    if default_display:
        prompt_parts.append(f"[{default_display}]")
    prompt_text = " ".join(prompt_parts) + ": "

    while True:
        try:
            user_input = input(prompt_text).strip()
        except EOFError:
            print("\nEntrada finalizada inesperadamente. Abortando.")
            raise SystemExit(1) from None
        except KeyboardInterrupt:
            print("\nInterrupción detectada. Abortando.")
            raise SystemExit(1) from None

        if user_input:
            return user_input

        if current:
            return current

        if field.default:
            return field.default

        if field.generator:
            generated = field.generator()
            print(f"🔐 Generado automáticamente {field.key}.")
            return generated

        if field.required:
            print("Este campo es obligatorio. Introduce un valor.")
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
    print(f"📁 Copia de seguridad creada en {backup}")


def write_env_file(path: Path, values: Dict[str, str]) -> None:
    """Write the collected values to disk."""

    header = [
        "# Archivo generado por configurator.py",
        "# Modifica los valores manualmente si lo necesitas.",
        "",
    ]
    body = [f"{key}={value}" for key, value in values.items()]
    content = "\n".join(header + body) + "\n"
    path.write_text(content, encoding="utf8")


def main() -> None:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("Este asistente requiere una terminal interactiva.")
        raise SystemExit(1)

    print("\n============================================")
    print(" Asistente de configuración de entorno (.env)")
    print("============================================\n")

    if ENV_FILE.exists():
        print(f"Se ha detectado un archivo existente: {ENV_FILE}")
        print("Se leerán los valores actuales y se creará una copia de seguridad antes de sobrescribir.")

    existing = read_existing_values(ENV_FILE)
    values = collect_values(FIELDS, existing)

    if ENV_FILE.exists():
        backup_file(ENV_FILE)

    write_env_file(ENV_FILE, values)
    print(f"\n✅ Archivo de configuración actualizado en {ENV_FILE}\n")


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
