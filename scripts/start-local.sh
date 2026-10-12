#!/usr/bin/env bash
set -euo pipefail
ROOT="$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/backend${PYTHONPATH:+:$PYTHONPATH}"
# uv reads environment values without sourcing executable shell configuration.
uv run --env-file .env python -m researchpilot.persistence
exec uv run --env-file .env python -m uvicorn researchpilot.api:create_app \
  --factory --host 127.0.0.1 --port 8000 --no-access-log
