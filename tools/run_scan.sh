#!/usr/bin/env sh
# One-command garak scan against a local Ollama model, written up automatically.
#   cd redteam-log && sh tools/run_scan.sh            (default model llama3.2:3b)
#   MODEL=llama3.2:1b sh tools/run_scan.sh            (faster on 8 GB machines)
# Follows 00-setup/environment.md: venv in ~/redteam-venv, Python 3.11-3.13.
set -eu
cd "$(dirname "$0")/.."
MODEL="${MODEL:-llama3.2:3b}"
CAP="${CAP:-40}"
PROBES="promptinject.HijackHateHumans,encoding.InjectBase64,latentinjection.LatentInjectionResume"
VENV="$HOME/redteam-venv"
PREFIX="scan-$(date +%Y%m%d-%H%M)"
START=$(date +%s)

say() { printf '\n== %s\n' "$*"; }

# 1. A Python garak accepts
PY=""
for c in python3.13 python3.12 python3.11 /opt/homebrew/bin/python3.12 "$HOME/.homebrew/bin/python3.12" python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if (3,11) <= sys.version_info[:2] <= (3,13) else 1)' 2>/dev/null; then PY="$c"; break; fi
done
if [ -z "$PY" ] && [ ! -x "$VENV/bin/python" ]; then
  echo "Need Python 3.11-3.13. Run: brew install python@3.12   then run this script again."; exit 1
fi

# 2. venv + garak (skipped if already there)
if [ ! -x "$VENV/bin/garak" ]; then
  say "Creating $VENV and installing garak (one-off, a few minutes)"
  [ -x "$VENV/bin/python" ] || "$PY" -m venv "$VENV"
  "$VENV/bin/python" -m pip install -q --upgrade pip
  "$VENV/bin/python" -m pip install -q garak
fi
"$VENV/bin/garak" --version | head -1

# 3. Ollama running, model present
command -v ollama >/dev/null 2>&1 || { echo "Ollama not found. Run: brew install ollama"; exit 1; }
if ! curl -s -o /dev/null http://127.0.0.1:11434; then
  say "Starting ollama serve in the background"
  (ollama serve >/tmp/ollama-serve.log 2>&1 &)
  sleep 4
fi
ollama list | grep -q "^$MODEL" || { say "Pulling $MODEL"; ollama pull "$MODEL"; }
ollama run "$MODEL" "Reply with exactly: ready" | head -1

# 4. The scan
say "Scanning $MODEL ($CAP prompts per probe, 1 generation). Roughly 10-20 min on a MacBook Air."
printf 'run:\n  generations: 1\n  soft_probe_prompt_cap: %s\n' "$CAP" > /tmp/garak-cap.yaml
"$VENV/bin/garak" --target_type ollama.OllamaGeneratorChat --target_name "$MODEL" \
  --probes "$PROBES" --config /tmp/garak-cap.yaml --report_prefix "$PREFIX"

# 5. Keep the raw evidence and write the log
RUNS="$HOME/.local/share/garak/garak_runs"
mkdir -p 01-scans/raw
cp "$RUNS/$PREFIX.report.jsonl" "$RUNS/$PREFIX.report.html" 01-scans/raw/ 2>/dev/null || true
cp "$RUNS/$PREFIX.hitlog.jsonl" 01-scans/raw/ 2>/dev/null || true
MIN=$(( ( $(date +%s) - START ) / 60 ))
LOG=$("$VENV/bin/python" tools/garak_to_log.py "01-scans/raw/$PREFIX.report.jsonl" --minutes "$MIN")
say "Done. Log written to $LOG"
echo "Read it, fill in the three sections marked 'write this yourself', then commit 01-scans/."
