#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}/.."

cd "${PROJECT_ROOT}"

export FLASK_APP=app:create_app

MESSAGE="Auto generated migration"
if (($# > 0)); then
    MESSAGE="$1"
    shift
fi

flask db migrate -m "$MESSAGE" "$@"
