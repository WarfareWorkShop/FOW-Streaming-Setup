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
from pathlib import Path
from typing import Sequence


PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"


def clear_screen() -> None:
    """Limpia la terminal si es posible."""

    command = "cls" if os.name == "nt" else "clear"
    if shutil.which(command):  # pragma: no cover - depende del sistema operativo
        os.system(command)


def ensure_directory(path: Path, description: str) -> bool:
    """Verifica que exista el directorio requerido por una acción."""

    if not path.exists():
        print(f"\n⚠️  No se encontró {description}: {path}")
        return False
    return True


def run_command(command: Sequence[str], cwd: Path | None = None) -> bool:
    """Ejecuta un comando mostrando su salida en tiempo real."""

    command_display = " ".join(command)
    location = f" (en {cwd})" if cwd else ""
    print(f"\n➡️  Ejecutando: {command_display}{location}\n")

    try:
        subprocess.run(command, cwd=cwd, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"\n❌ El comando terminó con errores (código {exc.returncode}).")
        return False
    except FileNotFoundError:
        print("\n❌ Comando no encontrado. ¿Está instalado?")
        return False
    except KeyboardInterrupt:
        print("\n⏹️  Ejecución interrumpida por el usuario.")
        return False

    return True


def pip_command(*args: str) -> Sequence[str]:
    """Devuelve el comando pip asociado al intérprete actual."""

    return (sys.executable, "-m", "pip", *args)


def install_backend_dependencies() -> None:
    if not ensure_directory(BACKEND_DIR, "el directorio del backend"):
        return

    requirements = BACKEND_DIR / "requirements.txt"
    if not requirements.exists():
        print("\n⚠️  No se encontró el archivo requirements.txt del backend.")
        return

    print("\nInstalando dependencias del backend (Python)...")
    run_command(pip_command("install", "-r", "requirements.txt"), cwd=BACKEND_DIR)


def install_frontend_dependencies() -> None:
    if not ensure_directory(FRONTEND_DIR, "el directorio del frontend"):
        return

    npm = shutil.which("npm")
    if not npm:
        print("\n❌ No se encontró el comando npm. Instala Node.js para continuar.")
        return

    print("\nInstalando dependencias del frontend (Node.js)...")
    run_command((npm, "install"), cwd=FRONTEND_DIR)


def run_backend_server() -> None:
    if not ensure_directory(BACKEND_DIR, "el directorio del backend"):
        return

    print(
        "\nIniciando el servidor Flask del backend."
        "\nPulsa Ctrl+C para detenerlo y volver al menú."
    )

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
    if not ensure_directory(FRONTEND_DIR, "el directorio del frontend"):
        return

    npm = shutil.which("npm")
    if not npm:
        print("\n❌ No se encontró el comando npm. Instala Node.js para continuar.")
        return

    print(
        "\nIniciando el servidor de desarrollo del frontend."
        "\nPulsa Ctrl+C para detenerlo y volver al menú."
    )

    run_command((npm, "start"), cwd=FRONTEND_DIR)


def show_environment_summary() -> None:
    print("\nResumen rápido del entorno:")
    print(f"- Python: {sys.version.split()[0]} ({sys.executable})")

    try:
        pip_version = subprocess.check_output(
            pip_command("--version"),
            cwd=PROJECT_ROOT,
            text=True,
        ).strip()
    except subprocess.CalledProcessError:
        pip_version = "No se pudo obtener la versión de pip."

    print(f"- Pip: {pip_version}")

    npm = shutil.which("npm")
    if npm:
        try:
            npm_version = subprocess.check_output(
                (npm, "--version"),
                text=True,
            ).strip()
        except subprocess.CalledProcessError:
            npm_version = "No se pudo obtener la versión."
        print(f"- npm: {npm_version} ({npm})")
    else:
        print("- npm: no encontrado (instala Node.js si necesitas el frontend)")

    print(f"- Directorio del proyecto: {PROJECT_ROOT}")


def print_menu() -> None:
    print(
        """
============================================
 Launcher de Flames of War Streaming Setup
============================================

Elige una opción:
  1) Instalar dependencias del backend (Python)
  2) Lanzar servidor del backend
  3) Instalar dependencias del frontend (Node.js)
  4) Lanzar servidor del frontend
  5) Mostrar resumen del entorno
  0) Salir
""".strip()
    )


def main() -> None:
    clear_screen()
    print("Bienvenido/a al lanzador interactivo del proyecto.\n")
    show_environment_summary()

    while True:
        print_menu()
        try:
            choice = input("\nSelecciona una opción y pulsa Enter: ").strip()
        except EOFError:
            print("\nEntrada finalizada. ¡Hasta pronto!")
            break
        except KeyboardInterrupt:
            print("\n\nInterrupción detectada. ¡Hasta pronto!")
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
        elif choice == "0":
            print("\n¡Gracias por usar el lanzador! Hasta pronto.")
            break
        else:
            print("\nOpción no reconocida. Introduce un número del 0 al 5.")


if __name__ == "__main__":  # pragma: no cover - punto de entrada de script
    main()
