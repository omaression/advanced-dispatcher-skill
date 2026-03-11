# Publish Notes

This repository keeps source, tests, and release history. The ClawHub publishable package is the **lean copy** under:

- `publish/advanced-dispatcher-skill/`

Do **not** publish from the repo root.

## Why

The lean publish directory keeps the package ClawHub-friendly and minimal. It contains only the files needed at runtime:

- `SKILL.md`
- `dispatcher.py`
- `LICENSE`

Tests and repo-only maintenance files stay outside the published package.

## Prepare the publish copy

From the repo root:

```bash
mkdir -p publish/advanced-dispatcher-skill publish/dist
cp SKILL.md publish/advanced-dispatcher-skill/
cp dispatcher.py publish/advanced-dispatcher-skill/
cp LICENSE publish/advanced-dispatcher-skill/
```

## Validate/package

```bash
python3 /usr/lib/node_modules/openclaw/skills/skill-creator/scripts/package_skill.py ./publish/advanced-dispatcher-skill ./publish/dist
```

## Publish to ClawHub

This skill was previously published under the slug:

- `advanced-dispatcher-skill`

Keep using the same slug for updates.

Example:

```bash
clawhub publish ./publish/advanced-dispatcher-skill \
  --slug advanced-dispatcher-skill \
  --name "Advanced Dispatcher" \
  --version 0.3.0 \
  --changelog "Rebuild as a stricter ClawHub-friendly dispatcher. Update routing to GPT-5.4 for code/architecture, GLM-5 for math/algorithms, Minimax M2.5 for web dev/brainstorming, Kimi K2.5 for research/long context, and GPT-5.3 Codex Spark for quick scripts/formatting. Tradeoff evaluation now uses GLM-5 + GPT-5.3-Codex with GPT-5.4 as judge, and Claude is only allowed through prompt-scoped --force-claude."
```

## Auth

```bash
clawhub login
clawhub whoami
```
