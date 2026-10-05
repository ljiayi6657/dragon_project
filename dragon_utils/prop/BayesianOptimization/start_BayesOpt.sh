#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
DEPS="$HOME/.cache/dragon-task2deps"
cd "$ROOT"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$DEPS:$ROOT" OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  python dragon_utils/prop/BayesianOptimization/BayesOpt.py "$@"
