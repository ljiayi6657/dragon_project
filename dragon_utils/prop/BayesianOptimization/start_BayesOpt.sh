#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
DEPS="$HOME/.cache/dragon-task2deps"
if [[ "${BAYESOPT_TMUX:-0}" != "1" && "${1:-}" == "--calls" ]]; then
  CMD="$(printf '%q ' env BAYESOPT_TMUX=1 bash "$0" "$@")"
  if tmux has-session -t '=BayesOpt' 2>/dev/null; then
    DEAD="$(tmux display-message -p -t '=BayesOpt:main.0' '#{pane_dead}')"
    if [[ "$DEAD" != "1" ]]; then
      echo "BayesOpt controller is already active: tmux attach -t BayesOpt" >&2
      exit 1
    fi
    tmux respawn-pane -k -t '=BayesOpt:main.0' "$CMD"
  else
    tmux new-session -d -s BayesOpt -n main "$CMD"
    tmux set-option -w -t '=BayesOpt:main' remain-on-exit on
  fi
  tmux clear-history -t '=BayesOpt:main.0'
  echo "Controller: tmux attach -t BayesOpt (BayesOpt:main.0)"
  exit 0
fi
cd "$ROOT"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$DEPS:$ROOT" OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  python dragon_utils/prop/BayesianOptimization/BayesOpt.py "$@"
