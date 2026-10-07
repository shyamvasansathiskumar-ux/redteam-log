# OWASP LLM Top 10 (2025) → MITRE ATLAS mapping

All ten 2025 classes, each mapped to the ATLAS techniques that actually apply, checked against the ATLAS data (v5.6.0). Every entry has the same parts: the class in one sentence, the techniques, why the distinction matters, how to probe it with garak, the controls a governance team would write down, the NIST AI RMF hook, and one line for a non-technical risk owner.

Sources to work from: the [OWASP GenAI Top 10](https://genai.owasp.org/llm-top-10/) entry for the class, and the [MITRE ATLAS matrix](https://atlas.mitre.org/) for the technique.

## Progress

| # | OWASP class (2025) | ATLAS technique | Done |
|---|---|---|---|
| LLM01 | Prompt Injection | AML.T0051 | ✅ |
| LLM02 | Sensitive Information Disclosure | AML.T0024 | ✅ |
| LLM03 | Supply Chain | AML.T0010 | ✅ |
| LLM04 | Data and Model Poisoning | AML.T0020, AML.T0018.000 | ✅ |
| LLM05 | Improper Output Handling | AML.T0050, AML.T0077 | ✅ |
| LLM06 | Excessive Agency | AML.T0053, AML.T0101 *(adversary only, see entry)* | ✅ |
| LLM07 | System Prompt Leakage | AML.T0056, AML.T0083 | ✅ |
| LLM08 | Vector and Embedding Weaknesses | AML.T0070, AML.T0071, AML.T0066 | ✅ |
| LLM09 | Misinformation | AML.T0062, AML.T0060 *(adversary half only)* | ✅ |
| LLM10 | Unbounded Consumption | AML.T0029, AML.T0034 | ✅ |

A note on versions: OWASP published a 2026 Top 10 on 6 August 2026 (reordered, with System Prompt Leakage renamed Hidden Context Exposure). This file stays on the 2025 numbering so the mappings above stay comparable; a 2026 crosswalk is next. Risks that only exist once a model can act are mapped separately in [agentic-mapping.md](agentic-mapping.md) (OWASP Top 10 for Agentic Applications).

---

## LLM01:2025 — Prompt Injection

**The class, in one sentence.** User input manipulates the model into ignoring its original instructions, causing behaviour the system designer didn't intend and didn't authorise.

**ATLAS technique.** `AML.T0051` — LLM Prompt Injection, with three sub-techniques:

- `AML.T0051.000` — **Direct**: the attacker types the injected instruction themselves.
- `AML.T0051.001` — **Indirect**: the instruction arrives through content the model ingests (a web page, a document, a retrieved chunk), so the attacker never touches the prompt box.
- `AML.T0051.002` — **Triggered**: the injection sits planted in the victim's environment and fires on a user action or event, typically against agents. Added to ATLAS after this entry was first written.

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

## LLM02:2025 — Sensitive Information Disclosure

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

## LLM03:2025 — Supply Chain

**The class, in one sentence.** The risk isn't in what an attacker types to the model — it's in what got baked into the system before a single prompt was ever sent: a compromised base model, a poisoned dataset, a malicious fine-tune, or a tampered dependency in the ML stack.

**ATLAS technique.** `AML.T0010` — AI Supply Chain Compromise, with six sub-techniques:

- `AML.T0010.000` — **Hardware**: the physical infrastructure the model trains or runs on is compromised.
- `AML.T0010.001` — **AI Software**: the libraries, frameworks, or serialization formats in the ML stack itself carry a compromise (a classic example: a `.pkl` model file that executes arbitrary code on load, because Python's pickle format was never designed to be a safe way to distribute untrusted data).
- `AML.T0010.002` — **Data**: the training or fine-tuning dataset is poisoned or tampered with before the model ever sees it.
- `AML.T0010.003` — **Model**: a pretrained model itself — downloaded from a hub, forked from a base — is the compromised artifact, backdoored before it ever reaches you.
- `AML.T0010.004` — **Container Registry**: the container images the model is packaged and shipped in are tampered with.
- `AML.T0010.005` — **AI Agent Tool**: a tool an agent is wired to call is itself the compromised component — the newest sub-technique, and the one that matters most as agent deployments grow.

*Note on the last two:* several published OWASP→ATLAS crosswalks still list only four sub-techniques here. `.004` and `.005` are current in the live matrix — `.005` in particular closes the gap between this class and agentic risk, and is worth watching as agent tool ecosystems (MCP servers, plugin registries) become a real distribution channel.

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

**The class, in one sentence.** Someone changes what the model learns, through pre-training data, fine-tuning data or the weights themselves, so that it behaves the way they want later, often only when a trigger shows up.

**ATLAS techniques.**

- `AML.T0020` — **Poison Training Data**: modify the dataset or its labels so the trained model carries a hidden behaviour.
- `AML.T0018.000` — **Manipulate AI Model: Poison AI Model**: change the weights directly, or through fine-tuning, without touching the original dataset.
- `AML.T0019` — **Publish Poisoned Datasets** and `AML.T0058` — **Publish Poisoned Models**: put the poisoned artefact somewhere victims will download it.
- `AML.T0043.004` — **Craft Adversarial Data: Insert Backdoor Trigger**: the input that wakes the planted behaviour up at inference time.

**Why the distinction matters.** LLM03 asked *where did this model come from?* LLM04 asks *what did it learn while it was there?* A model from a perfectly trusted source can still be poisoned if one of the datasets it was fine-tuned on was. And a backdoor that only fires on a trigger phrase passes every normal evaluation, because normal evaluations don't contain the trigger. That is why poisoning is so hard to catch with behavioural testing alone.

**How to probe it.** Black-box scanning can't prove a model is clean, because you'd have to guess the trigger. What garak *can* do is surface memorised training data, which tells you what the model was exposed to:

```bash
garak --model_type ollama --model_name llama3.2:3b --probes leakreplay --generations 1
```

For a model you fine-tune yourself, the real test is provenance: hash the dataset, keep a held-out set you built, and compare behaviour before and after the fine-tune.

**Controls a governance team would actually write down.**

- Know every dataset that touched the model: source, version, hash, who approved it.
- Fine-tune only on data you can trace, and keep a clean held-out evaluation set the training pipeline can never write to.
- Treat a third-party fine-tune or LoRA adapter as code from a stranger, because that is effectively what it is.
- Re-run the same evaluation suite after every fine-tune and investigate any behaviour change, not only regressions.

**NIST AI RMF hook.** MAP (knowing what data entered the system, MAP 4.1) and MEASURE (detecting behaviour changes between versions, MEASURE 2.7).

**One line for a non-technical risk owner.** *"A model can be taught a secret trick during training that only shows up when someone says the password, and normal testing will never find it."*

---

## LLM05:2025 — Improper Output Handling

**The class, in one sentence.** The application takes what the model wrote and passes it to something else (a browser, a shell, a database, another tool) without checking it, so model output becomes code that runs.

**ATLAS techniques.**

- `AML.T0050` — **Command and Scripting Interpreter**: model output ends up executed by a shell or interpreter.
- `AML.T0077` — **LLM Response Rendering**: the client renders model output, for example a markdown image, and the rendering itself leaks data to an attacker's server.

**Why the distinction matters.** LLM01 is about what goes *into* the model; LLM05 is about what comes *out* and where it goes next. The model doesn't need to be attacked for this to bite. In [ai-incident-atlas incident 09](https://github.com/shyamvasansathiskumar-ux/ai-incident-atlas/blob/main/incidents/09-claude-code-home-directory-deletion.md) the model simply wrote `~/` at the end of an `rm -rf`, and nothing between the model and the shell looked at it. Classic web bugs (XSS, SQL injection, SSRF) come back to life the moment model output is treated as trusted.

**How to probe it.** garak has probes for both routes, rendering and execution:

```bash
garak --model_type ollama --model_name llama3.2:3b --probes web_injection --generations 1
garak --model_type ollama --model_name llama3.2:3b --probes exploitation --generations 1
```

`web_injection` covers markdown image exfiltration and XSS payloads; `exploitation` checks whether the model will emit SQL and template-injection strings.

**Controls a governance team would actually write down.**

- Treat model output exactly like user input: encode it for its destination (HTML-escape, parameterise SQL, never pass it to `eval`).
- Allowlist the domains a rendered response can load images or links from.
- For agents, validate commands *after* shell expansion, on the resolved paths, before they run.
- Run anything model-generated in a sandbox with the least privilege it needs.

**NIST AI RMF hook.** MEASURE 2.7 (security and resilience evaluated) and MANAGE (runtime controls between output and execution).

**One line for a non-technical risk owner.** *"Whatever the AI writes, our system has to check it the way it would check something typed by a stranger, because sometimes that's effectively what it is."*

---

## LLM06:2025 — Excessive Agency

**The class, in one sentence.** The model can do more than its job needs (more functions, more permissions or more autonomy), so any mistake or manipulation does more damage than it should.

**ATLAS techniques.**

- `AML.T0053` — **AI Agent Tool Invocation**: using an agent's tools for the adversary's ends.
- `AML.T0086` — **Exfiltration via AI Agent Tool Invocation**: tools used to move data out.
- `AML.T0101` — **Data Destruction via AI Agent Tool Invocation**: tools used to destroy data (added 25 November 2025).

**Why the distinction matters.** This is the class where ATLAS and OWASP part ways. OWASP's own description lists non-malicious triggers, such as hallucination or a badly worded benign prompt, alongside prompt injection. Every ATLAS technique above begins "Adversaries may...". So the most common real-world version of this class, an agent doing damage *with no attacker*, has no ATLAS mapping at all. I've written six such incidents up in [ai-incident-atlas](https://github.com/shyamvasansathiskumar-ux/ai-incident-atlas/blob/main/analysis/no-adversary-failures.md), with five proposed checklist entries (NA-01 to NA-05) to run alongside ATLAS.

**How to probe it.** A model on its own has no agency to test; this class needs an agent with tools. garak's `agent_breaker` probe family targets agentic setups, and the real test is an audit of permissions rather than a prompt:

1. List every tool the agent can call and every credential it can read.
2. For each, write down the most destructive thing it could do.
3. Compare that list with what the task actually needs. The difference is the finding.

**Controls a governance team would actually write down.**

- Least functionality: give the agent only the tools the task needs (read-only by default).
- Least privilege: credentials bound to one environment; a staging agent cannot name production.
- Human approval for anything irreversible (delete, send, pay, publish), enforced by the tool layer, not requested in the prompt.
- Stop and freeze implemented as revoked permissions, never as instructions.

**NIST AI RMF hook.** GOVERN 6.1 (third-party risk), MAP 3.5 (human oversight defined) and MANAGE 2.4 (mechanisms to disengage or deactivate).

**One line for a non-technical risk owner.** *"The question isn't whether the AI will make a mistake, it's how much one mistake can destroy, and that's decided by what we let it touch."*

---

## LLM07:2025 — System Prompt Leakage

**The class, in one sentence.** The hidden instructions behind an application leak, and the real damage comes from what people put in them: API keys, internal rules, or security logic that was never meant to be seen.

**ATLAS techniques.**

- `AML.T0056` — **Extract LLM System Prompt**: getting the model to reveal its system prompt.
- `AML.T0069.002` — **Discover LLM System Information: System Prompt**: the reconnaissance version, learning how the system is set up.
- `AML.T0083` — **Credentials from AI Agent Configuration**: the payoff when secrets were stored where the model can see them.

**Why the distinction matters.** OWASP's own framing is the useful part: the leak of the prompt is rarely the vulnerability. The vulnerability is designing a system whose security depends on the prompt staying secret. A system prompt should be treated as public. If revealing it gives anyone a key, a bypass or a list of what is filtered, the design is wrong. Note that the 2026 Top 10 renamed this class *Hidden Context Exposure*, widening it beyond the system prompt itself.

**How to probe it.**

```bash
garak --model_type ollama --model_name llama3.2:3b --probes sysprompt_extraction --generations 1
```

**Controls a governance team would actually write down.**

- No secrets, credentials or connection strings in prompts, ever. They belong in the tool layer.
- No security decisions (who can see what) enforced by prompt instructions; enforce them in code.
- Assume the system prompt will be published and review it on that basis.

**NIST AI RMF hook.** MAP (where sensitive configuration lives) and MEASURE 2.7.

**One line for a non-technical risk owner.** *"Assume anyone can read the AI's instructions, so nothing in them should be a secret or a lock."*

---

## LLM08:2025 — Vector and Embedding Weaknesses

**The class, in one sentence.** The retrieval layer of a RAG system (the vector database and what is in it) can be poisoned, can leak data across users, or can be mined for what it contains.

**ATLAS techniques.**

- `AML.T0070` — **RAG Poisoning**: planting content in what the system retrieves from.
- `AML.T0071` — **False RAG Entry Injection**: content crafted to be read as a separate, trusted retrieved document.
- `AML.T0066` — **Retrieval Content Crafting**: content written to be retrieved for specific queries.
- `AML.T0064` — **Gather RAG-Indexed Targets**: finding out which sources the system indexes.
- `AML.T0085.000` — **Data from AI Services: RAG Databases**: pulling data out of the vector store.

**Why the distinction matters.** RAG is usually sold as the safe alternative to fine-tuning: you don't change the model, you just give it documents. But every document is a potential instruction (that's LLM01 again, indirect injection) and every user shares the same index unless someone built access control into retrieval. ATLAS is unusually detailed here, with five techniques for one OWASP class, which says something about how much real attack activity targets this layer.

**How to probe it.** garak's `latentinjection` probes test whether instructions hidden inside documents get followed:

```bash
garak --model_type ollama --model_name llama3.2:3b --probes latentinjection --generations 1
```

Testing cross-user leakage needs a real RAG pipeline with two users, which is the next thing to build in this repo.

**Controls a governance team would actually write down.**

- Enforce access control at retrieval time: a user can only retrieve chunks they could open as documents.
- Know and approve every source that feeds the index, and log what gets ingested.
- Treat retrieved text as data, never as instructions, and strip or flag instruction-like content.

**NIST AI RMF hook.** MAP 4.1 (third-party data in the pipeline) and MANAGE 4.1 (monitoring what enters the index after deployment).

**One line for a non-technical risk owner.** *"Our AI answers from a library of documents, and anyone who can get a page into that library can change what it says."*

---

## LLM09:2025 — Misinformation

**The class, in one sentence.** The model states false things with confidence, and people or systems act on them.

**ATLAS techniques.**

- `AML.T0062` — **Discover LLM Hallucinations**: finding the false entities (packages, URLs, people) a model reliably invents.
- `AML.T0060` — **Publish Hallucinated Entities**: registering those invented names so the hallucination now points at the attacker. "Slopsquatting" is the package version of this.

**Why the distinction matters.** This is the second class, after LLM06, where most real harm has no adversary. A model inventing a legal case, a medical dose or a company policy is a failure on its own. ATLAS only covers the case where an attacker *exploits* the hallucination. That case is real and dangerous (an invented `pip install` name an attacker has since registered is a supply-chain attack), but it's the narrower half. In 2026 OWASP moved Misinformation up two places, driven partly by incident data.

**How to probe it.** garak covers both halves:

```bash
garak --model_type ollama --model_name llama3.2:3b --probes packagehallucination --generations 1
garak --model_type ollama --model_name llama3.2:3b --probes misleading,snowball --generations 1
```

`packagehallucination` checks invented package names (the attacker's half); `misleading` and `snowball` check whether the model goes along with false premises and compounds its own errors.

**Controls a governance team would actually write down.**

- Ground answers in retrieved sources and show the source; no source, no factual claim.
- Never install a package an AI suggested without checking that it exists and who publishes it.
- For high-stakes domains (health, legal, finance), human review before anything is acted on.

**NIST AI RMF hook.** MEASURE 2.5 and 2.6 (validity and safety evaluated) and GOVERN (who is accountable when a customer acts on a false answer).

**One line for a non-technical risk owner.** *"The AI sounds equally sure whether it's right or wrong, so anything that matters needs a source or a person behind it."*

---

## LLM10:2025 — Unbounded Consumption

**The class, in one sentence.** Nothing limits how much someone can use the model, so they can run up the bill, slow it down for everyone, or query it enough to copy it.

**ATLAS techniques.**

- `AML.T0029` — **Denial of AI Service**: flooding the system to degrade or stop it.
- `AML.T0034` — **Cost Harvesting**, with three sub-techniques: `.000` Excessive Queries, `.001` Resource-Intensive Queries, `.002` Agentic Resource Consumption.
- `AML.T0024.002` — **Exfiltration via AI Inference API: Extract AI Model**: enough queries to train a working copy.

**Why the distinction matters.** In normal software a flood is a nuisance; with LLMs every request costs real money, and an agent can be pushed into fanning out dozens of tool calls from one prompt. `AML.T0034.002` exists precisely for that agentic case. OWASP moved this class up four places in 2026. The same missing control, a budget per user and per task, also slows down model extraction, which is a different-sounding risk entirely.

**How to probe it.** This is mostly a load and quota test rather than a garak probe: send increasing volumes and long-context requests, and see where (or whether) the system says no. garak's `divergence` probe checks one related failure, prompts that make a model generate without stopping:

```bash
garak --model_type ollama --model_name llama3.2:3b --probes divergence --generations 1
```

**Controls a governance team would actually write down.**

- Rate limits and token budgets per user, per key and per task, with hard caps rather than alerts only.
- Caps on agent tool calls per request and on recursion depth.
- Cost alerts that page a person, not just a dashboard.
- Watch for extraction patterns: many systematically varied queries from one source.

**NIST AI RMF hook.** MANAGE 4.1 (post-deployment monitoring) and MEASURE 2.7.

**One line for a non-technical risk owner.** *"Every question the AI answers costs us money, so without a limit, one person can spend our whole budget, or slowly copy what we built."*
