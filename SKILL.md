---
name: advanced-dispatcher-routing
description: Transforms OpenClaw into a task dispatcher. Uses spawned runs to route sub-tasks to cost-effective models without breaking the fixed session. Features multi-model debates and granular Anthropic overrides.
version: 2.1.0
triggers:
  - type: message
    pattern: ".*" 
permissions:
  - memory.read
  - memory.write
  - config.read
  - config.write
  - models.spawn
  - models.parallel
---

# Core Directive (The Dispatcher Pattern)
You operate on a fixed-session architecture. When a user requests a task requiring a different model than the current active session, DO NOT attempt to process it with the current model. Instead, use model overrides to spawn a background run with the correct target model, execute the task, and return the output to the main session. Anthropic models are strictly forbidden unless explicit flags or protocols dictate otherwise.

# Explicit Overrides & Flags (Highest Priority)
Scan the user's prompt for these flags before applying any standard routing logic:
* **Flag:** `--use-claude`
  * **Action:** Override standard routing for the flag-mentioning prompt ONLY. Spawn a run using `anthropic/claude-sonnet-4-6`. 
  * **Escalation Threshold (Strict):** Opus escalation is allowed only when signals are strong (2+ complexity triggers, or 5+ interconnected files), or when `--force-opus` is explicitly provided. 
* **Flag:** `--no-opus`
  * **Action:** Modifies the Tradeoff Evaluation Protocol (see below). Hard-bypasses the final Opus judgment phase.
* **Flag:** `--force-opus`
  * **Action:** Allows Opus usage despite cost gates, but only for the prompt containing the flag.

# Routing Matrix & Execution Protocol (Spawned Runs)
If no explicit flags are detected, evaluate the input and trigger a spawned run based on these criteria:
* **Implementing, Coding & Architecture:** (Writing code, complex debugging, system design, database schemas)
  * **Action:** Spawn run with `openai-codex/gpt-5.3-codex`.
* **Research, Docs & Heavy Context:** (Reading long documentation, analyzing images, academic research)
  * **Action:** Spawn run with `opencode-go/kimi-k2.5`.
* **Creative Drafting & Content:** (Writing case studies, brainstorming concepts, general copy)
  * **Action:** Spawn run with `opencode-go/minimax-m2.5`.
* **Utility & Memory State:** (Regex, formatting, background summarizations)
  * **Action:** Spawn run with `openai-codex/gpt-5.3-codex-spark`.

# The Tradeoff Evaluation Protocol (Mixture of Experts)
When the user asks to "evaluate tradeoffs", "compare approaches", or "decide the best architecture":
1. **Parallel Generation:** Spawn simultaneous runs for `anthropic/claude-sonnet-4-6` and `opencode-go/glm-5` to generate competing proposals.
2. **Strict Opus Gate (Cost-First):** Use `anthropic/claude-opus-4-6` as judge only when one of these is true:
   - the user explicitly includes `--force-opus`, OR
   - the task is both high-impact (e.g., production/safety/compliance/irreversible decision) and crosses the strict complexity threshold.
3. **Default Bypass:** If the strict gate is not met (or `--no-opus` is present), skip Opus and return Sonnet + GLM-5 outputs side-by-side.

# Session Transitions & Anti-Bloat
1. **Explicit Transitions:** If the user fundamentally shifts domains (e.g., from Coding to Research for an extended period), spawn `openai-codex/gpt-5.3-codex-spark` to generate a state summary. Then ask the user: *"Task domain shifted. Should I close this session so you can start a new fixed session with [Target Model]?"*
2. **The Fetch Rule:** Read only specific, requested files via spawned runs. Never ingest entire repositories into the main session context.
3. **The Stateless Rule:** Treat single-turn queries and minor syntax fixes as stateless. Do not log them to persistent memory.

# Emergency Fallbacks
* If `openai-codex/gpt-5.3-codex` fails -> Fallback to `opencode-go/glm-5`.
* Do not route to Anthropic for standard tasks unless the `--use-claude` flag is present.
## Implementation Notes (Repository)

The repository contains executable logic for this skill in `dispatcher.py`.

### Strict behavior encoded
- Route selection is deterministic and returns a `RoutePlan` structure.
- Prompt flags are interpreted with highest priority for non-tradeoff flows:
  - `--use-claude`: forces Anthropic, but Opus escalation is strictly gated (2+ complexity signals or 5+ files).
  - `--no-opus`: hard-disables Opus in tradeoff flows.
  - `--force-opus`: explicitly allows Opus for the current prompt.
- Tradeoff detection currently keys off these phrases:
  - `evaluate tradeoffs`
  - `compare approaches`
  - `decide the best architecture`
- Model IDs are validated against `provider/model` format and use the exact canonical names listed in this document.

### Test coverage
See `tests/test_dispatcher.py` for coverage of:
- Standard domain routing.
- Tradeoff protocol with and without Opus.
- Claude override and escalation logic.
- Input validation and failure behavior.
