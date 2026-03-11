# Skill: Advanced Dispatcher & Cost Management

## Overview
This skill transforms OpenClaw into an intelligent task dispatcher. Because OpenClaw operates on a fixed-session architecture, it cannot natively swap its core "brain" mid-conversation. Instead, this skill allows your active session to spawn temporary, background runs using specific, cost-effective models based on the cognitive demand of your prompt. It prioritizes efficient routing to minimize API burn, executes multi-model debates for complex decisions, and aggressively manages its context window.

## Autonomous Behaviors (No Input Required)

Once this skill is active, OpenClaw operates as a manager, handling the following in the background:

### 1. The Dispatcher Pattern (Spawned Runs)
When you request a task that requires a different model than your current active session, OpenClaw will not attempt to process it with the current model. Instead, it dispatches a spawned run using the overrides below, processes the task in the background, and returns the result to your main chat:
* **Heavy Engineering & Architecture:** Dispatches to `openai-codex/gpt-5.3-codex`. Used for writing core logic, system design, database schemas, and deep debugging.
* **Research, Docs & Heavy Ingestion:** Dispatches to `opencode-go/kimi-k2.5`. Used for deep dives into academic concepts, reading massive API documentations, and analyzing reference images or UI mockups. It leverages a 256k context window and vision capabilities to handle massive payloads efficiently.
* **Creative Drafting & Content:** Dispatches to `opencode-go/minimax-m2.5`. Used for writing readable content, generating case studies, or brainstorming structural UI layouts.
* **Utility & Janitorial:** Dispatches to `openai-codex/gpt-5.3-codex-spark`. Used for regex, quick formatting, and background state summarizations.

### 2. Explicit Session Transitions
If you fundamentally shift workflows (e.g., moving entirely from an hour of "Coding" to an hour of "Research"), spawning constant background runs is inefficient. 
* **The Transition Rule:** OpenClaw will pause, use the `openai-codex/gpt-5.3-codex-spark` model to write a highly condensed summary of your current project state, save it to persistent memory, and explicitly ask you: *"Task domain shifted. Should I close this session so you can start a new fixed session with [Target Model]?"*

### 3. Surgical Context Management
To keep token costs low and response times fast:
* **Stateless Quick-Hits:** Single-turn questions or minor syntax fixes processed via spawned runs are treated as stateless and are not logged to your main persistent memory.
* **Surgical Fetching:** OpenClaw will only read the exact local files needed for a task, refusing to ingest entire repositories into its active context.

## The Tradeoff Protocol (Mixture of Experts)

When you explicitly ask OpenClaw to **"evaluate tradeoffs"**, **"compare approaches"**, or **"decide the best architecture"**, it triggers an automated multi-model debate via parallel spawned runs:
1. **Parallel Generation:** It spawns runs for both `anthropic/claude-sonnet-4-6` and `opencode-go/glm-5` simultaneously to generate competing architectural approaches from diverse model families.
2. **The Opus Judge:** It feeds both arguments into a final spawned run using `anthropic/claude-opus-4-6`.
3. **The Verdict:** Opus evaluates the merits of both sides and delivers a final, decisive recommendation back to your main chat.

## Manual Overrides & Flags

You retain absolute control. Use these flags anywhere in your prompt to bypass OpenClaw's autonomous routing logic:

* **`--use-claude`**
  * **Action:** Overrides standard routing and forces a spawned run using Anthropic strictly for the prompt mentioning this flag. 
  * **Smart Escalation:** It will default to `anthropic/claude-sonnet-4-6` as long as the task is under a certain reasoning threshold. However, if OpenClaw determines the task crosses a threshold of high cognitive complexity (see triggers below), it will automatically fall back to `anthropic/claude-opus-4-6`.
* **`--no-opus`**
  * **Action:** Modifies the Tradeoff Protocol. Use this when you want a parallel comparison but the comparison isn't worth burning the API credits on an Opus judgment.
  * **Result:** Bypasses the Opus spawned run entirely and simply outputs the Sonnet and GLM-5 arguments side-by-side for you to evaluate yourself.

## The Claude Escalation Threshold (Sonnet vs. Opus)

When the `--use-claude` flag is triggered, OpenClaw will only autonomously escalate the spawned run to the highly expensive `anthropic/claude-opus-4-6` if the request meets **at least one** of the following hard complexity triggers:

### 1. Multi-File Dependency (Scope)
* **Sonnet:** The task is isolated to 1–2 files (e.g., writing a single script, styling a UI component).
* **Opus Trigger:** The task requires OpenClaw to read, understand, or modify **3 or more interconnected files** (e.g., refactoring a database schema that impacts backend models, API routes, and frontend state simultaneously).

### 2. Algorithmic & Architectural Depth (Reasoning)
* **Sonnet:** Standard implementation tasks, consuming straightforward APIs, or standard debugging.
* **Opus Trigger:** The prompt explicitly asks for ground-up system architecture, complex algorithmic optimization, or resolving deep concurrency/race-condition bugs.

### 3. Context Payload (Token Weight)
* **Sonnet:** The combined token count of your prompt plus any locally fetched files or documentation is relatively light.
* **Opus Trigger:** The required context payload is massive, ensuring nothing is lost in the noise of a massive context window.