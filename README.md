# Advanced Dispatcher

A strict, ClawHub-friendly mid-session routing skill for OpenClaw.

## Purpose

- route work to the best spawned model without changing the fixed main session
- keep routing predictable, cheap, and testable
- prevent accidental Claude usage
- stay compatible with strict skill packaging and validation

## Routing table

| Task class | Primary model | Cache retention |
|---|---|---|
| Code & architecture | `openai-codex/gpt-5.4` | `long` |
| Math & algorithms | `opencode-go/glm-5` | `short` |
| Web dev & brainstorming | `opencode-go/minimax-m2.5` | `short` |
| Research & long context | `opencode-go/kimi-k2.5` | `short` |
| Quick scripts & formatting | `openai-codex/gpt-5.3-codex-spark` | `long` |

## Tradeoff routing

### Default

Generate proposals in parallel with:
- `opencode-go/glm-5`
- `openai-codex/gpt-5.3-codex`

Judge with:
- `openai-codex/gpt-5.4`

### With `--force-claude`

Use Claude only for proposal generation:
- `anthropic/claude-sonnet-4-6`
- `anthropic/claude-opus-4-6`

Judge remains:
- `openai-codex/gpt-5.4`

## Trigger language

Tradeoff mode should trigger on requests like:
- "evaluate tradeoffs"
- "compare approaches/options/designs/architectures"
- "choose between these solutions"
- "which architecture is better?"

Do not trigger tradeoff mode just because the prompt contains a vague standalone "compare".

## Flag policy

- supported: `--force-claude`
- rejected: `--use-claude`, `--force-opus`, `--no-opus`
- Claude must never appear in a route unless `--force-claude` is present

## Files

- `SKILL.md` — operating instructions
- `dispatcher.py` — deterministic route planner
- `tests/test_dispatcher.py` — unit tests and smoke coverage

## Validation commands

```bash
python3 -m unittest tests/test_dispatcher.py -v
python3 /usr/lib/node_modules/openclaw/skills/skill-creator/scripts/package_skill.py . ./dist
```
