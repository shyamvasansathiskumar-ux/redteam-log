#!/usr/bin/env python3
"""Turn a garak report into a scan log in 01-scans/, following TEMPLATE-scan-log.md.

Usage: python3 tools/garak_to_log.py <run>.report.jsonl [--minutes N]

Everything in the Scope and Results tables is read from the report itself, so the
log can't drift from what garak actually measured. The sections that need a human
(what surprised me, severity reasoning, governance translation) are left for you.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

# Probe family -> (OWASP LLM Top 10 class, MITRE ATLAS technique). Kept in step with
# 03-owasp-atlas/mapping.md; anything not listed here is printed as "unmapped".
MAP = {
    "promptinject": ("LLM01 Prompt Injection", "AML.T0051.000 LLM Prompt Injection: Direct"),
    "encoding": ("LLM01 Prompt Injection", "AML.T0051.000 LLM Prompt Injection: Direct (payload obfuscated as an encoding)"),
    "latentinjection": ("LLM01 Prompt Injection", "AML.T0051.001 LLM Prompt Injection: Indirect"),
    "dan": ("LLM01 Prompt Injection", "AML.T0054 LLM Jailbreak"),
    "leakreplay": ("LLM02 Sensitive Information Disclosure", "AML.T0057 LLM Data Leakage"),
    "packagehallucination": ("LLM09 Misinformation", "AML.T0062 Discover LLM Hallucinations"),
}


def load(path):
    entries = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    setup = next(e for e in entries if e["entry_type"] == "start_run setup")
    init = next((e for e in entries if e["entry_type"] == "init"), {})
    evals = [e for e in entries if e["entry_type"] == "eval"]
    return setup, init, evals


def hits(hitlog_path, per_probe=2):
    p = Path(hitlog_path)
    if not p.exists():
        return {}
    seen = defaultdict(list)
    for line in p.read_text().splitlines():
        if not line.strip():
            continue
        h = json.loads(line)
        if len(seen[h["probe"]]) >= per_probe:
            continue
        turns = h.get("prompt", {}).get("turns", [])
        prompt = turns[-1]["content"]["text"] if turns else ""
        out = h.get("output") or {}
        out = out.get("text", "") if isinstance(out, dict) else str(out)
        seen[h["probe"]].append((h.get("goal", ""), h["detector"], prompt, out, h.get("triggers")))
    return seen


def clip(s, n=400):
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[:n] + " …"


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    report = sys.argv[1]
    minutes = sys.argv[sys.argv.index("--minutes") + 1] if "--minutes" in sys.argv else "?"
    setup, init, evals = load(report)
    target = setup.get("plugins.target_name") or "?"
    gtype = setup.get("plugins.target_type") or "?"
    version = setup.get("_config.version", "?")
    gens = setup.get("run.generations", "?")
    cap = setup.get("run.soft_probe_prompt_cap", "?")
    date = (init.get("start_time") or "")[:10] or "unknown-date"
    probes = sorted({e["probe"] for e in evals})

    rows = []
    for e in evals:
        n = e["total_evaluated"]
        fails = e["fails"]
        rate = f"{100 * fails / n:.1f}%" if n else "n/a"
        rows.append(f"| `{e['probe']}` | `{e['detector']}` | {n} | {fails} | {rate} |")

    found = hits(report.replace(".report.jsonl", ".hitlog.jsonl"))
    findings = []
    i = 0
    for probe in probes:
        owasp, atlas = MAP.get(probe.split(".")[0], ("unmapped", "unmapped"))
        for goal, det, prompt, out, trig in found.get(probe, []):
            i += 1
            findings.append(
                f"### Finding {i}: `{probe}`\n\n"
                f"- **Probe goal (garak's words):** {goal}\n"
                f"- **Detector that fired:** `{det}`" + (f", looking for: {clip(str(trig), 120)}" if trig else "") + "\n"
                f"- **Attack prompt (abridged):** {clip(prompt)}\n"
                f"- **Model response (abridged):** {clip(out)}\n"
                f"- **OWASP LLM class:** {owasp}\n"
                f"- **MITRE ATLAS technique:** {atlas}\n"
            )
    if not findings:
        findings.append("No detector fired on any attempt in this run.\n")

    safe = target.replace(":", "-").replace("/", "-")
    fam = "-".join(sorted({p.split(".")[0] for p in probes}))
    out_path = Path(__file__).resolve().parent.parent / "01-scans" / f"{date}-{safe}-{fam}.md"
    cmd = " ".join(setup.get("_config.argv", [])) if isinstance(setup.get("_config.argv"), list) else ""

    text = f"""# Scan log: {target}, {date}

## Scope

| Field | Value |
|---|---|
| Target | `{target}` via `{gtype}`, local |
| Tool + version | garak `{version}` |
| Probes run | {", ".join(f"`{p}`" for p in probes)} |
| Generations | {gens} |
| Prompt cap per probe | {cap} |
| Date | {date} |
| Time spent | {minutes} min |

**Why this target and these probes:** one direct injection family, one obfuscated injection and one indirect injection, so a single run covers the three ways LLM01 shows up. All three map to AML.T0051 in [the mapping](../03-owasp-atlas/mapping.md).

## Command

```bash
sh tools/run_scan.sh
```

The script pins the probes and prompt cap; the raw report is in `01-scans/raw/`.

## Results summary

"Hits" are attempts where the detector judged the attack to have worked. Lower is better for the model.

| Probe | Detector | Attempts | Hits | Hit rate |
|---|---|---|---|---|
{chr(10).join(rows)}

## Notable findings

{chr(10).join(findings)}
## What surprised me

<!-- write this yourself after reading the findings above -->

## What I'd do differently next run

<!-- write this yourself -->

## Governance translation

<!-- one paragraph for someone who will never read the terminal output -->
"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text)
    print(out_path)


if __name__ == "__main__":
    main()
