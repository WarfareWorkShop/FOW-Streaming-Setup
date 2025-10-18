"""Launcher interactivo para facilitar el uso del proyecto.

Este script ofrece un menú sencillo en castellano pensado para personas
con poca experiencia técnica. Permite instalar las dependencias y lanzar
los servidores de backend y frontend con unos pocos pasos.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from functools import partial
from pathlib import Path
from typing import Sequence

from i18n import determine_language_from_cli, format_language_list, translate


PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
CONFIGURATOR_PATH = PROJECT_ROOT / "configurator.py"

LANGUAGE, REMAINING_ARGS = determine_language_from_cli()
sys.argv = [sys.argv[0], *REMAINING_ARGS]
t = partial(translate, language=LANGUAGE)


def clear_screen() -> None:
    """Limpia la terminal si es posible."""

    command = "cls" if os.name == "nt" else "clear"
    if shutil.which(command):  # pragma: no cover - depende del sistema operativo
        os.system(command)


def ensure_directory(path: Path, description: str) -> bool:
    """Verifica que exista el directorio requerido por una acción."""

    if not path.exists():
        print(t("launcher.missing_directory", description=description, path=path))
        return False
    return True


def run_command(command: Sequence[str], cwd: Path | None = None) -> bool:
    """Ejecuta un comando mostrando su salida en tiempo real."""

    command_display = " ".join(command)
    location = (
        f" ({t('launcher.run_command.location', path=cwd)})" if cwd else ""
    )
    print(t("launcher.run_command.executing", command=command_display, location=location))

    try:
        subprocess.run(command, cwd=cwd, check=True)
    except subprocess.CalledProcessError as exc:
        print(t("launcher.run_command.error_code", code=exc.returncode))
        return False
    except FileNotFoundError:
        print(t("launcher.run_command.not_found"))
        return False
    except KeyboardInterrupt:
        print(t("launcher.run_command.interrupted"))
        return False

    return True


def pip_command(*args: str) -> Sequence[str]:
    """Devuelve el comando pip asociado al intérprete actual."""

    return (sys.executable, "-m", "pip", *args)


def install_backend_dependencies() -> None:
    if not ensure_directory(BACKEND_DIR, t("launcher.descriptions.backend_directory")):
        return

    requirements = BACKEND_DIR / "requirements.txt"
    if not requirements.exists():
        print(t("launcher.backend_requirements_missing"))
        return

    print(t("launcher.install_backend_start"))
    run_command(pip_command("install", "-r", "requirements.txt"), cwd=BACKEND_DIR)


def install_frontend_dependencies() -> None:
    if not ensure_directory(FRONTEND_DIR, t("launcher.descriptions.frontend_directory")):
        return

    npm = shutil.which("npm")
    if not npm:
        print(t("launcher.frontend_npm_missing"))
        return

    print(t("launcher.install_frontend_start"))
    run_command((npm, "install"), cwd=FRONTEND_DIR)


def run_backend_server() -> None:
    if not ensure_directory(BACKEND_DIR, t("launcher.descriptions.backend_directory")):
        return

    print(t("launcher.run_backend_start"))

    command = (
        sys.executable,
        "-m",
        "flask",
        "--app",
        "backend.app:create_app",
        "run",
        "--debug",
    )

    run_command(command, cwd=PROJECT_ROOT)


def run_frontend_server() -> None:
    if not ensure_directory(FRONTEND_DIR, t("launcher.descriptions.frontend_directory")):
        return

    npm = shutil.which("npm")
    if not npm:
        print(t("launcher.frontend_npm_missing"))
        return

    print(t("launcher.run_frontend_start"))

    run_command((npm, "start"), cwd=FRONTEND_DIR)


def run_configurator() -> None:
    if not CONFIGURATOR_PATH.exists():
        print(t("launcher.configurator_missing"))
        return

    print(t("launcher.configurator_start"))

    run_command((sys.executable, str(CONFIGURATOR_PATH)), cwd=PROJECT_ROOT)


def show_environment_summary() -> None:
    print(t("launcher.environment_summary_title"))
    print(
        t(
            "launcher.environment_summary.python",
            version=sys.version.split()[0],
            executable=sys.executable,
        )
    )

    try:
        pip_version = subprocess.check_output(
            pip_command("--version"),
            cwd=PROJECT_ROOT,
            text=True,
        ).strip()
    except subprocess.CalledProcessError:
        print(t("launcher.environment_summary.pip_error"))
    else:
        print(t("launcher.environment_summary.pip", version=pip_version))

    npm = shutil.which("npm")
    if npm:
        try:
            npm_version = subprocess.check_output(
                (npm, "--version"),
                text=True,
            ).strip()
        except subprocess.CalledProcessError:
            print(t("launcher.environment_summary.npm_error"))
        else:
            print(
                t(
                    "launcher.environment_summary.npm_version",
                    version=npm_version,
                    path=npm,
                )
            )
    else:
        print(t("launcher.environment_summary.npm_missing"))

    print(t("launcher.environment_summary.project_dir", path=PROJECT_ROOT))


def print_menu() -> None:
    for line in t("launcher.menu.lines"):
        print(line)


def main() -> None:
    clear_screen()
    print(t("launcher.menu.welcome"))
    print(t("launcher.language_hint", languages=format_language_list(LANGUAGE)))
    show_environment_summary()

    while True:
        print_menu()
        try:
            choice = input(t("launcher.menu.prompt")).strip()
        except EOFError:
            print(t("launcher.farewell_eof"))
            break
        except KeyboardInterrupt:
            print(t("launcher.farewell_interrupt"))
            break

        if choice == "1":
            install_backend_dependencies()
        elif choice == "2":
            run_backend_server()
        elif choice == "3":
            install_frontend_dependencies()
        elif choice == "4":
            run_frontend_server()
        elif choice == "5":
            show_environment_summary()
        elif choice == "6":
            run_configurator()
        elif choice == "0":
            print(t("launcher.menu.goodbye"))
            break
        else:
            print(t("launcher.menu.invalid"))


if __name__ == "__main__":  # pragma: no cover - punto de entrada de script
    main()
