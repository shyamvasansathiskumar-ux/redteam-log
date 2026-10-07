# OWASP Top 10 for Agentic Applications (2026) → MITRE ATLAS mapping

The LLM Top 10 in [mapping.md](mapping.md) covers what goes wrong inside a model. This list covers what goes wrong once the model can act: call tools, keep memory, and work through multi-step plans. OWASP published it on 9 December 2025. ATLAS techniques are checked against the ATLAS data (v5.6.0).

Each entry follows the same parts as mapping.md: the risk in one sentence, the techniques, where the mapping is clean and where it isn't, a real case, how to test it, controls, the NIST AI RMF hook, and one line for a risk owner. One entry at a time.

## Progress

| # | OWASP Agentic risk | ATLAS techniques | Done |
|---|---|---|---|
| ASI01 | Agent Goal Hijack | AML.T0051.001, AML.T0051.002, AML.T0094, AML.T0053 | ✅ |
| ASI02 | Tool Misuse and Exploitation | | |
| ASI03 | Identity and Privilege Abuse | | |
| ASI04 | Agentic Supply Chain Compromise | | |
| ASI05 | Unexpected Code Execution | | |
| ASI06 | Memory and Context Poisoning | | |
| ASI07 | Insecure Inter-Agent Communication | | |
| ASI08 | Cascading Failures | | |
| ASI09 | Human-Agent Trust Exploitation | | |
| ASI10 | Rogue Agents | | |

---

## ASI01:2026 — Agent Goal Hijack

**The risk, in one sentence.** Someone changes what an agent is trying to achieve, through its instructions, its inputs or its decision path, so it carries out a goal the operator never set.

**How it differs from LLM01.** Prompt injection (LLM01) is the *mechanism*. Goal hijack is the *outcome* when the injected text reaches a system that can act. A hijacked chatbot says something wrong once. A hijacked agent keeps working towards the new goal across every remaining step, using every tool it has.

**ATLAS techniques.** ATLAS has no single "goal hijack" technique. The risk is a chain, and each link has its own ID:

| Link in the chain | ATLAS technique | Notes |
|---|---|---|
| Plant the instruction where the agent will read it | `AML.T0093` Prompt Infiltration via Public-Facing Application | A support ticket, an email, a web page, a PR comment |
| The agent reads it as an instruction | `AML.T0051.001` LLM Prompt Injection: Indirect | The core of almost every real ASI01 case |
| ...or it fires on a later event | `AML.T0051.002` Triggered | Planted now, executed when a user or schedule wakes the agent |
| ...or it waits to slip past a control | `AML.T0094` Delay Execution of LLM Instructions | "When the user next asks...", used to get past per-turn tool restrictions |
| The new goal turns into actions | `AML.T0053` AI Agent Tool Invocation | Where the hijack stops being text and starts doing things |
| Typical payoff | `AML.T0086` Exfiltration via AI Agent Tool Invocation | Not the only one; destruction (`AML.T0101`) is the other common payoff |

**Where the mapping is clean, and where it isn't.**

- *Clean:* every ATLAS case below maps end to end. ATLAS describes the attacker's path well.
- *Not clean, part 1:* the boundary with **ASI06 Memory and Context Poisoning** (`AML.T0080`). If the injected goal is written into memory or stays in a long thread, it outlives the session, and then it's context poisoning. The rule I'm using here: ASI01 when the goal changes within one task, ASI06 when the change persists past it.
- *Not clean, part 2:* ATLAS needs an adversary. An agent can drift off its goal with nobody attacking it, by widening a task's scope or overriding a constraint on its own. That's the no-adversary gap documented in [ai-incident-atlas](https://github.com/shyamvasansathiskumar-ux/ai-incident-atlas). OWASP's wording ("someone changes") leaves the same gap, so both frameworks miss those cases.

**Real cases in ATLAS.**

- `AML.CS0039` *Living Off AI: Prompt Injection via Jira Service Management* (Cato Networks, June 2025). An external user files a support ticket containing instructions. An internal engineer's AI agent, connected to Jira through MCP, processes the ticket with internal privileges and follows them. Procedure: T0093 → T0051.001 → T0053 → T0086. This is OWASP's own ASI01 example scenario, in a real product.
- `AML.CS0038` *Planting Instructions for Delayed Automatic AI Agent Tool Invocation* (Embrace the Red, Feb 2024). Gemini blocked tool calls in any turn where untrusted data had entered context. Instructions that said "on the next turn, do X" got past that rule. Procedure: T0051.001 → T0094 → T0053.

**How to test it.** garak tests a bare model, so it covers the injection link but not the agent:

```bash
garak --target_type ollama --target_name llama3.2:3b --probes latentinjection --generations 1
```

A high hit rate on `latentinjection` means the model will follow instructions hidden in a document. That's the precondition for ASI01, not ASI01 itself. To test the full chain you need an agent with a tool. The next step for this log is a minimal agent with one harmless tool (writing to a file), fed a poisoned document, to check whether the tool call happens.

**Controls a governance team would write down.**

- **Declare the task, then check against it.** Every agent run gets a stated objective. Each tool call is checked against that objective before it executes. This is the "agent hook" control OWASP recommends.
- **Separate instructions from data at the boundary.** Content from tickets, email, the web and tool output is labelled untrusted and can't add instructions. Flag text in those channels that looks like instructions.
- **Least privilege per task, not per agent.** An agent triaging tickets doesn't need write access to the repository, even if the same agent sometimes does other work.
- **A human approves any consequential action that comes from untrusted input.** The approval screen shows where the instruction came from, not only what the agent wants to do.
- **Log the reasoning trace alongside tool calls.** After a hijack, you need to see which input changed the plan.

**NIST AI RMF hook.** MAP 3.5 (human oversight processes are defined) and MANAGE 2.4 (mechanisms exist to supersede, disengage or deactivate a system acting outside its intended use). GOVERN 1.3 sets the risk tolerance: which actions an agent may take on untrusted input at all.

**One line for a non-technical risk owner.** *"If our agent reads a customer's message, that customer can try to give our agent orders, so the agent must only act on goals we set, and check every action against them."*

---

Sources: [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) · [MITRE ATLAS data](https://github.com/mitre-atlas/atlas-data) · [Cato Networks, Jira MCP PoC](https://www.catonetworks.com/blog/cato-ctrl-poc-attack-targeting-atlassians-mcp/) · [Embrace the Red, delayed tool invocation](https://embracethered.com/blog/posts/2024/llm-context-pollution-and-delayed-automated-tool-invocation/)
