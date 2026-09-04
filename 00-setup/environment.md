# Environment setup — MacBook Air (Apple Silicon)

Verified against current docs, August 2026. Run these in order. Each block is copy-pasteable.

Fill in the "Result" lines as you go — this file is the record of what your machine actually has, which saves an hour of confusion in month three when something breaks.

---

## 0. Check what you already have

```bash
python3 --version
which python3
brew --version
```

**garak requires Python 3.11–3.13.** PyRIT requires 3.10–3.14. macOS often ships an older `python3`, so if the version printed above is below 3.11, do step 1. If it's 3.11, 3.12, or 3.13, skip to step 2.

> Result: python3 version = `________` · Homebrew installed = yes / no

---

## 1. Install a compatible Python (only if needed)

If Homebrew isn't installed:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Then follow the "Next steps" it prints — on Apple Silicon it will ask you to add Homebrew to your PATH. Then:

```bash
brew install python@3.12
```

Verify:

```bash
/opt/homebrew/bin/python3.12 --version
```

> Result: `________`

---

## 2. Create the virtual environment

Keeping this in your home directory (not inside the repo) means the repo stays clean and the venv survives repo moves.

```bash
/opt/homebrew/bin/python3.12 -m venv ~/redteam-venv
source ~/redteam-venv/bin/activate
python -m pip install --upgrade pip
python --version
```

You should see `(redteam-venv)` at the start of your prompt. **Every future session starts with that `source` line** — worth adding to your notes:

```bash
source ~/redteam-venv/bin/activate
```

> Result: venv created at `~/redteam-venv` · python version inside venv = `________`

---

## 3. Install garak and PyRIT

```bash
python -m pip install -U garak
python -m pip install -U pyrit
```

Verify both landed:

```bash
garak --version
python -c "import pyrit; print('pyrit ok')"
```

If `pip install pyrit` throws a dependency conflict, install it in a **separate** venv rather than fighting it — PyRIT pulls a large dependency tree and doesn't need to share an environment with garak:

```bash
deactivate
/opt/homebrew/bin/python3.12 -m venv ~/pyrit-venv
source ~/pyrit-venv/bin/activate
python -m pip install -U pyrit
```

> Result: garak version = `________` · pyrit installed = yes / separate venv / failed
> Any errors worth remembering: `________`

---

## 4. Install Ollama and pull a target model

Ollama is what gives you a local model to attack — no API key, no spend, no terms-of-service question about scanning it.

```bash
brew install ollama
```

Start the background service (leave this running, or use `brew services start ollama`):

```bash
ollama serve
```

In a **new terminal tab**, pull a small model. Pick based on your RAM:

```bash
# 8GB Mac — start here
ollama pull llama3.2:3b

# 16GB+ Mac — either of these is fine
ollama pull llama3.2:3b
ollama pull qwen2.5:7b
```

Confirm it answers:

```bash
ollama run llama3.2:3b "say hello in five words"
```

> Result: model pulled = `________` · responds = yes / no

---

## 5. Smoke test — the one that matters

Two steps. First prove garak runs at all, with no model involved:

```bash
source ~/redteam-venv/bin/activate
garak --model_type test.Blank --probes test.Test
```

That should complete in seconds. If it does, garak is working.

Now point it at your local model:

```bash
garak --model_type ollama --model_name llama3.2:3b --probes test.Test
```

This is the whole goal of setup day — **not** to find anything interesting, just to prove the pipeline runs end to end. garak writes a report file and prints its path at the end. Note that path here:

> Report written to: `________`
> Smoke test passed: yes / no

### If it fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `connection refused` | `ollama serve` isn't running | Start it in another tab |
| `model not found` | Name mismatch | `ollama list` and use the exact name shown |
| `command not found: garak` | venv not active | `source ~/redteam-venv/bin/activate` |
| Python version error on install | Wrong interpreter | Recreate the venv with 3.12 explicitly |

---

## 6. First real run (Monday, week 1)

Once the smoke test passes, this is the shape of an actual scan. `--generations 1` keeps it fast while you're learning:

```bash
garak --model_type ollama --model_name llama3.2:3b --probes promptinject --generations 1
```

Write it up in `01-scans/` using the template. Note that a newer flag spelling (`--target_type` / `--target_name`) also works in recent garak versions — if you see that in docs, it's the same thing.

---

## Running notes

Keep appending here — every "wait, why did that break" moment is worth two lines.

- `YYYY-MM-DD` —
