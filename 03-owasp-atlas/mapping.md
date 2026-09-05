# OWASP LLM Top 10 (2025) → MITRE ATLAS mapping

One entry per week, filled in during the Friday bridge session. This is deliberately **not** pre-filled — the mapping is the learning, and a table someone else completed teaches nothing. LLM01 and LLM02 below are worked through as examples of the depth each entry should reach.

Sources to work from: the [OWASP GenAI Top 10](https://genai.owasp.org/llm-top-10/) entry for the class, and the [MITRE ATLAS matrix](https://atlas.mitre.org/) for the technique.

## Progress

| # | OWASP class (2025) | ATLAS technique | Done |
|---|---|---|---|
| LLM01 | Prompt Injection | AML.T0051 | ✅ worked example below |
| LLM02 | Sensitive Information Disclosure | AML.T0024 | ✅ worked example below |
| LLM03 | Supply Chain | AML.T0010 | ✅ worked example below |
| LLM04 | Data and Model Poisoning | | ☐ |
| LLM05 | Improper Output Handling | | ☐ |
| LLM06 | Excessive Agency | | ☐ |
| LLM07 | System Prompt Leakage | | ☐ |
| LLM08 | Vector and Embedding Weaknesses | | ☐ |
| LLM09 | Misinformation | | ☐ |
| LLM10 | Unbounded Consumption | | ☐ |

Ten classes, one per Friday — the table finishes around week 10, which lands right as the week-12 audit needs it.

---

## LLM01:2025 — Prompt Injection · *worked example*

**The class, in one sentence.** User input manipulates the model into ignoring its original instructions, causing behaviour the system designer didn't intend and didn't authorise.

**ATLAS technique.** `AML.T0051` — LLM Prompt Injection, with two sub-techniques:

- `AML.T0051.000` — **Direct**: the attacker types the injected instruction themselves.
- `AML.T0051.001` — **Indirect**: the instruction arrives through content the model ingests (a web page, a document, a retrieved chunk), so the attacker never touches the prompt box.

**Why the distinction matters.** Direct injection is a misuse problem — the person attacking is the person typing. Indirect injection is a *supply chain of text* problem: any content the system reads becomes executable instruction. Systems with retrieval or browsing are exposed to the second even when the first is well defended, and the two need different controls.

**How to probe it.** garak's `promptinject` probe family covers the direct case:

```bash
garak --model_type ollama --model_name llama3.2:3b --probes promptinject --generations 1
```

Indirect injection generally needs a system with retrieval to test properly — worth revisiting once you're scanning something with a document pipeline rather than a bare model.

**Controls a governance team would actually write down.**

- Treat all retrieved and user-supplied content as untrusted input, never as instruction.
- Enforce privilege separation — the model's *tools* should be permission-bounded so a successful injection still can't reach anything sensitive.
- Require human approval for consequential actions rather than trusting the model's intent classification.
- Log and monitor for instruction-override patterns.

**NIST AI RMF hook.** Sits under MEASURE (identify and track the risk) and MANAGE (respond and mitigate). If you write this up as a risk assessment, that's the framing a reviewer will expect.

**One line for a non-technical risk owner.** *"Anything our AI reads can potentially tell it what to do, so we can't let it read untrusted content and hold sensitive permissions at the same time."*

---

## LLM02:2025 — Sensitive Information Disclosure · *worked example*

**The class, in one sentence.** The model reveals information it shouldn't — data memorised from training, secrets sitting in its context, or private details about other users — because nothing in the system stops it from repeating what it knows.

**ATLAS technique.** `AML.T0024` — Exfiltration via AI Inference API, with three sub-techniques:

- `AML.T0024.000` — **Infer Training Data Membership**: figuring out whether a specific piece of data was in the training set at all — a privacy leak even without extracting the data itself.
- `AML.T0024.001` — **Invert AI Model**: reconstructing actual training data by carefully analysing what the model outputs over many queries.
- `AML.T0024.002` — **Extract AI Model**: querying the model enough times to effectively steal a working copy of it.

**Why the distinction matters.** LLM01 was about an attacker's input changing model behaviour. LLM02 is different — nothing is being hijacked. The model is being asked ordinary-looking questions, repeatedly and patiently, until it reveals something it was never supposed to expose. That means LLM01-style defences (filtering malicious-looking input) don't help here, because nothing about the query looks malicious. The fix has to be about what data the model was ever exposed to and what it's allowed to say — not about catching "bad" input.

**How to probe it.** garak's `propile` probe tests exactly this — whether a model will leak PII it may have memorised, using prompts that combine a name with increasing amounts of known detail:

```bash
garak --model_type ollama --model_name llama3.2:3b --probes propile --generations 1
```

**Controls a governance team would actually write down.**

- Minimise what sensitive data ever reaches training or context in the first place — you can't leak what was never there.
- Apply output filtering for known-sensitive patterns (PII, secrets, internal identifiers) before a response reaches the user.
- Monitor for the query patterns membership-inference and model-inversion attacks actually use — many small, systematically varied queries against the same subject.
- Treat "the model refused once" as insufficient evidence of safety — test that it genuinely doesn't retain the information, not just that it declined politely.

**NIST AI RMF hook.** Sits under MAP (understanding what data the system was ever exposed to, and why) and MEASURE (testing whether that exposure is actually retrievable).

**One line for a non-technical risk owner.** *"If sensitive data ever touched this model — through training or just being pasted into its context — assume a patient enough attacker can get it back out."*

---

## LLM03:2025 — Supply Chain · *worked example*

**The class, in one sentence.** The risk isn't in what an attacker types to the model — it's in what got baked into the system before a single prompt was ever sent: a compromised base model, a poisoned dataset, a malicious fine-tune, or a tampered dependency in the ML stack.

**ATLAS technique.** `AML.T0010` — AI Supply Chain Compromise, with four sub-techniques:

- `AML.T0010.000` — **Hardware**: the physical infrastructure the model trains or runs on is compromised.
- `AML.T0010.001` — **AI Software**: the libraries, frameworks, or serialization formats in the ML stack itself carry a compromise (a classic example: a `.pkl` model file that executes arbitrary code on load, because Python's pickle format was never designed to be a safe way to distribute untrusted data).
- `AML.T0010.002` — **Data**: the training or fine-tuning dataset is poisoned or tampered with before the model ever sees it.
- `AML.T0010.003` — **Model**: a pretrained model itself — downloaded from a hub, forked from a base — is the compromised artifact, backdoored before it ever reaches you.

**Why the distinction matters.** LLM01 and LLM02 are both *runtime* risks — something happens while the model is answering a live prompt. Supply chain risk is a *pre-runtime* risk: it's already decided by the time you type anything. That changes where the fix has to live. You cannot prompt-engineer your way out of a poisoned model or a backdoored dependency — by the time you're at the chat window, it's too late. This is also the class most people skip, because it doesn't feel like "AI security" in the way jailbreaking does — it looks like ordinary software supply chain hygiene, just applied to models and datasets instead of npm packages.

**How to probe it.** This is the first class in the table where garak genuinely isn't the right tool — garak probes a model's *behavior* at inference time; it has no way to inspect where the model file came from or whether it was tampered with before you loaded it. The actual checks here are provenance and integrity, not prompting:

- Verify model weights are distributed in `safetensors` format, not pickle (`.bin`/`.pt` via `pickle` can execute arbitrary code on load — `safetensors` is a data-only format that can't).
- Check the model card / repo for a maintainer signature or published hash, and diff the hash of what you downloaded against it.
- Run `pip-audit` (or equivalent) against the environment `garak` and `PyRIT` themselves sit in — the scanning tool's own dependency tree is part of your supply chain too.
- For any dataset used in fine-tuning: know its source, and treat an unvetted scraped dataset the same way you'd treat unvetted code — read before you run.

**Controls a governance team would actually write down.**

- Maintain a model bill-of-materials (base model, version, source, training-data provenance) the same way software teams maintain an SBOM.
- Pin and hash-verify model and dependency versions — no floating "latest" in anything that touches production inference.
- Prefer `safetensors` over pickle-based checkpoints; treat any `.pkl`/`.bin` model file from an untrusted source as arbitrary code, not data.
- Vet third-party fine-tunes and LoRA adapters before deployment — a fine-tune can reintroduce a backdoor a base model didn't have.

**NIST AI RMF hook.** Sits under GOVERN (establishing who is accountable for vetting third-party models and data before they enter the pipeline) and MAP (understanding what's actually in the system's supply chain in the first place — you can't govern what you haven't mapped).

**One line for a non-technical risk owner.** *"We don't just have to trust what the model says — we have to trust where the model came from, and most teams never check."*

---

## LLM04:2025 — Data and Model Poisoning

---

## LLM05:2025 — Improper Output Handling

---

## LLM06:2025 — Excessive Agency

---

## LLM07:2025 — System Prompt Leakage

---

## LLM08:2025 — Vector and Embedding Weaknesses

---

## LLM09:2025 — Misinformation

---

## LLM10:2025 — Unbounded Consumption
