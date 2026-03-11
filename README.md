# Skill: Advanced Dispatcher & Cost Management

## Overview
This skill transforms OpenClaw into an intelligent task dispatcher. Because OpenClaw operates on a fixed-session architecture, it cannot natively swap its core "brain" mid-conversation. Instead, this skill allows your active session to spawn temporary, background runs using specific, cost-effective models based on the cognitive demand of your prompt. It prioritizes efficient routing to minimize API burn, executes multi-model debates for complex decisions, and aggressively manages its context window.

## Intent-Driven Behaviors (Scoped Activation)

When a message explicitly signals routing intent (dispatcher flags, tradeoff requests, or explicit "route/dispatch this" wording), OpenClaw operates as a manager and handles the following in the background:

### 1. The Dispatcher Pattern (Spawned Runs)
When you request a task that requires a different model than your current active session, OpenClaw will not attempt to process it with the current model. Instead, it dispatches a spawned run using the overrides below, processes the task in the background, and returns the result to your main chat:
* **Heavy Engineering & Architecture:** Dispatches to `openai-codex/gpt-5.3-codex`. Used for writing core logic, system design, database schemas, and deep debugging.
* **Research, Docs & Heavy Ingestion:** Dispatches to `opencode-go/kimi-k2.5`. Used for deep dives into academic concepts, reading massive API documentations, and analyzing reference images or UI mockups. It leverages a 256k context window and vision capabilities to handle massive payloads efficiently.
* **Creative Drafting & Content:** Dispatches to `opencode-go/minimax-m2.5`. Used for writing readable content, generating case studies, or brainstorming structural UI layouts.
* **Utility & Janitorial:** Dispatches to `openai-codex/gpt-5.3-codex-spark`. Used for regex, quick formatting, and background state summarizations.

### 2. Explicit Session Transitions
If you fundamentally shift workflows (e.g., moving entirely from an hour of "Coding" to an hour of "Research"), spawning constant background runs is inefficient. 
* **The Transition Rule:** OpenClaw will pause, use the `openai-codex/gpt-5.3-codex-spark` model to write a highly condensed **ephemeral** summary of your current project state, and explicitly ask you: *"Task domain shifted. Should I close this session so you can start a new fixed session with [Target Model]?"*

### 3. Surgical Context Management
To keep token costs low and response times fast:
* **Stateless Quick-Hits:** Single-turn questions or minor syntax fixes processed via spawned runs are treated as stateless and are not logged to your main persistent memory.
* **Surgical Fetching:** OpenClaw will only read the exact local files needed for a task, refusing to ingest entire repositories into its active context.

## The Tradeoff Protocol (Mixture of Experts)

When you explicitly ask OpenClaw to **"evaluate tradeoffs"**, **"compare approaches"**, or **"decide the best architecture"**, it triggers an automated multi-model debate via parallel spawned runs (this is an explicit protocol exception to the default Anthropic block):
1. **Parallel Generation:** It spawns runs for both `anthropic/claude-sonnet-4-6` and `opencode-go/glm-5` simultaneously to generate competing architectural approaches from diverse model families.
2. **Strict Opus Gate (Default Off):** It only uses `anthropic/claude-opus-4-6` when the task is clearly high-impact and highly complex, or when you explicitly pass `--force-opus`.
3. **Default Behavior:** Without that strict gate, it skips Opus and returns Sonnet + GLM-5 outputs side-by-side to minimize cost.

## Manual Overrides & Flags

You retain absolute control. Use these flags anywhere in your prompt to bypass OpenClaw's autonomous routing logic:

* **`--use-claude`**
  * **Action:** Overrides standard routing and forces a spawned run using Anthropic strictly for the prompt mentioning this flag. 
  * **Smart Escalation:** It will default to `anthropic/claude-sonnet-4-6` as long as the task is under a certain reasoning threshold. However, if OpenClaw determines the task crosses a threshold of high cognitive complexity (see triggers below), it will automatically fall back to `anthropic/claude-opus-4-6`.
* **`--no-opus`**
  * **Action:** Hard-disables Opus in tradeoff flows.
  * **Result:** Outputs Sonnet and GLM-5 arguments side-by-side for direct user evaluation.
* **`--force-opus`**
  * **Action:** Explicitly permits Opus for the current prompt, bypassing normal cost gates.

## The Claude Escalation Threshold (Sonnet vs. Opus)

When the `--use-claude` flag is triggered, OpenClaw will only autonomously escalate the spawned run to the highly expensive `anthropic/claude-opus-4-6` if the request meets a **strict** threshold: **at least two triggers**, or an extreme scope signal (5+ interconnected files).

### 1. Multi-File Dependency (Scope)
* **Sonnet:** The task is isolated to 1–2 files (e.g., writing a single script, styling a UI component).
* **Opus Contribution:** This counts as one escalation signal at 3+ interconnected files; by itself it does not auto-trigger Opus unless scope is extreme (5+ files).

### 2. Algorithmic & Architectural Depth (Reasoning)
* **Sonnet:** Standard implementation tasks, consuming straightforward APIs, or standard debugging.
* **Opus Trigger:** The prompt explicitly asks for ground-up system architecture, complex algorithmic optimization, or resolving deep concurrency/race-condition bugs.

### 3. Context Payload (Token Weight)
* **Sonnet:** The combined token count of your prompt plus any locally fetched files or documentation is relatively light.
* **Opus Trigger:** The required context payload is massive, ensuring nothing is lost in the noise of a massive context window.
---

## Local Reference Implementation (Added)

This repository now includes a strict, testable routing engine that mirrors this document:

- `dispatcher.py`
  - Implements deterministic route planning via `DispatcherRouter.route(...)`.
  - Enforces scoped activation in code (`should_dispatch(...)`) so ordinary out-of-scope prompts are rejected unless explicitly overridden for direct unit usage.
  - Enforces explicit domain inputs: `coding`, `research`, `creative`, `utility`.
  - Implements tradeoff protocol detection (`evaluate tradeoffs`, `compare approaches`, `decide the best architecture`).
  - Supports explicit flags `--use-claude`, `--no-opus`, and `--force-opus` exactly as documented.
  - Implements strict Claude escalation via `ComplexitySignals` (requires 2+ triggers, or extreme scope at 5+ interconnected files).
  - Validates model IDs against the provider/model convention (`provider/model-name`) before returning plans.
- `tests/test_dispatcher.py`
  - Unit tests for standard routes, tradeoff mode, no-opus mode, Claude escalation behavior, and invalid input handling.



## Runtime Credentials / Provider Access

This dispatcher intentionally calls multiple external providers (`openai-codex`, `opencode-go`, `anthropic`) via spawned runs.

### Chosen deployment profile (original implementation): Option A

I originally implemented this skill for **platform-managed provider access**. That means the host platform provides model entitlements and runtime auth wiring, while the skill package itself does not ship secrets.

- **Primary assumption:** Platform-managed access for OpenAI Codex and Opencode models.
- **Anthropic status:** I do have an Anthropic API key available, but Anthropic usage is intentionally constrained to strict exception paths only.

If platform provider access is missing, route planning can still succeed, but spawned execution will fail with policy/auth errors.

### Cost target of the suggested implementation

The goal is the most cost-effective practical setup:

- **Opencode Go plan:** about **$10** (baseline high-volume routing surface).
- **GPT Pro:** about **$20** (core coding/architecture throughput).
- **Anthropic spend:** keep this as low as possible by invoking Anthropic only when profoundly needed (explicit `--use-claude` or strict tradeoff protocol gating).

## Security & ClawHub Review Notes

This skill is intentionally hardened for marketplace review:

- **No persistent write privileges required:** skill metadata requests only `models.spawn` and `models.parallel`.
- **Scoped trigger pattern:** activation is narrowed to routing flags and explicit dispatcher/tradeoff intent, not every message.
- **Code-backed claims:** documented behavior is implemented in `dispatcher.py` and verified in `tests/test_dispatcher.py`.

### Canonical model IDs used by code

- `openai-codex/gpt-5.3-codex`
- `opencode-go/kimi-k2.5`
- `opencode-go/minimax-m2.5`
- `openai-codex/gpt-5.3-codex-spark`
- `opencode-go/glm-5`
- `anthropic/claude-sonnet-4-6`
- `anthropic/claude-opus-4-6`
