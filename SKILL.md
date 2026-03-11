---
name: advanced-dispatcher
description: Route mid-session work to the right spawned model without changing the fixed main session. Use for coding, architecture, math, algorithms, web development, brainstorming, research, long-context reading, quick scripts, formatting, or multi-model tradeoff evaluation. Default to strict no-Claude routing; allow Claude only when the current prompt explicitly includes --force-claude.
---

# Advanced Dispatcher

Use this skill to classify work, dispatch it to the best spawned model, and return the result to the main session.

## Non-negotiable rules

- Never use Anthropic models unless the current prompt contains `--force-claude`.
- Reject legacy flags `--use-claude`, `--force-opus`, and `--no-opus`.
- Treat `--force-claude` as prompt-scoped, not session-scoped.
- Prefer deterministic routing over ad hoc judgment.
- Use `long` cache retention for `openai-codex/*` routes.
- Use `short` cache retention for `opencode-go/*` routes.

## Standard routing

Choose exactly one primary route:

- **Code & architecture** → `openai-codex/gpt-5.4`
- **Math & algorithms** → `opencode-go/glm-5`
- **Web dev & brainstorming** → `opencode-go/minimax-m2.5`
- **Research & long context** → `opencode-go/kimi-k2.5`
- **Quick scripts & formatting** → `openai-codex/gpt-5.3-codex-spark`

If a request spans categories, route by the highest-risk deliverable:

1. Architecture or production code wins.
2. Math or algorithm correctness beats brainstorming.
3. Long-context ingestion beats light formatting.
4. Formatting-only tasks stay on Spark.

## Tradeoff protocol

Trigger tradeoff mode when the user asks to:
- evaluate tradeoffs
- compare approaches, options, designs, or architectures
- choose between competing solutions
- judge which architecture or design is better

### Default tradeoff route

Generate proposals in parallel with:
- `opencode-go/glm-5`
- `openai-codex/gpt-5.3-codex`

Judge both proposals with:
- `openai-codex/gpt-5.4`

### Tradeoff route with `--force-claude`

Use Claude only for proposal generation:
- `anthropic/claude-sonnet-4-6`
- `anthropic/claude-opus-4-6`

Keep the judge on:
- `openai-codex/gpt-5.4`

Do not use Claude anywhere else in the flow.

## Session transitions

If the user shifts into a sustained new domain, summarize the active state with `openai-codex/gpt-5.3-codex-spark` and suggest a fresh session only when repeated cross-domain dispatching would be wasteful.

## Context discipline

- Fetch only the files needed for the routed task.
- Do not ingest entire repositories unless the task explicitly requires it.
- Treat one-off quick fixes as stateless unless the user asks to preserve them.

## Implementation contract

`dispatcher.py` is the routing source of truth. It must:

- produce deterministic `RoutePlan` objects
- expose route choice, cache retention, and rationale
- support parallel proposal generation plus a separate judge in tradeoff mode
- reject empty prompts, unknown domains, and legacy flags
- keep routing updates easy by centralizing model and trigger definitions

## Validation checklist

Before shipping updates:

1. Run `tests/test_dispatcher.py`.
2. Run one end-to-end smoke test for a tradeoff request.
3. Confirm Claude is unreachable unless `--force-claude` is present.
4. Confirm all OpenAI Codex routes use `long` retention.
5. Confirm all `opencode-go` routes use `short` retention.
