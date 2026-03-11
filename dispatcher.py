"""Routing engine for the Advanced Dispatcher skill.

Strictly cost-aware routing:
- Anthropic usage only via explicit protocols/flags.
- Opus usage is aggressively gated and requires explicit high-complexity/high-impact
  evidence (or an explicit force flag).
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


MODEL_ID_PATTERN = re.compile(r"^[a-z0-9-]+/[a-z0-9.-]+$")


class ModelCatalog:
    """Canonical model ids used by the skill."""

    CODING = "openai-codex/gpt-5.3-codex"
    RESEARCH = "opencode-go/kimi-k2.5"
    CREATIVE = "opencode-go/minimax-m2.5"
    UTILITY = "openai-codex/gpt-5.3-codex-spark"
    FALLBACK = "opencode-go/glm-5"

    SONNET = "anthropic/claude-sonnet-4-6"
    OPUS = "anthropic/claude-opus-4-6"
    GLM = "opencode-go/glm-5"


TRADEOFF_PATTERNS = (
    re.compile(r"\bevaluate\s+tradeoffs?\b", re.IGNORECASE),
    re.compile(r"\bcompare\s+approaches\b", re.IGNORECASE),
    re.compile(r"\bdecide\s+the\s+best\s+architecture\b", re.IGNORECASE),
)

_HIGH_IMPACT_PATTERNS = (
    re.compile(r"\bproduction\b", re.IGNORECASE),
    re.compile(r"\bsafety[- ]critical\b", re.IGNORECASE),
    re.compile(r"\bcompliance\b", re.IGNORECASE),
    re.compile(r"\birreversible\b", re.IGNORECASE),
    re.compile(r"\bmulti[- ]quarter\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class ComplexitySignals:
    interconnected_files: int = 0
    asks_ground_up_architecture: bool = False
    asks_heavy_algorithmic_reasoning: bool = False
    massive_context_payload: bool = False

    @property
    def triggered_count(self) -> int:
        return sum(
            [
                self.interconnected_files >= 3,
                self.asks_ground_up_architecture,
                self.asks_heavy_algorithmic_reasoning,
                self.massive_context_payload,
            ]
        )

    @property
    def should_escalate_to_opus(self) -> bool:
        """Aggressive cost gate: require strong evidence before using Opus.

        Rules:
        - Escalate if >=2 escalation signals are true, OR
        - Escalate if interconnected files >=5 (very broad scope).
        """
        return self.triggered_count >= 2 or self.interconnected_files >= 5


@dataclass(frozen=True)
class RoutePlan:
    mode: str
    primary_model: str | None
    parallel_models: tuple[str, ...] = ()
    judge_model: str | None = None
    reason: str = ""


class RoutingError(ValueError):
    pass


class DispatcherRouter:
    """Pure routing logic for the Advanced Dispatcher skill."""

    _FLAG_USE_CLAUDE = "--use-claude"
    _FLAG_NO_OPUS = "--no-opus"
    _FLAG_FORCE_OPUS = "--force-opus"

    def route(
        self,
        prompt: str,
        *,
        domain: str,
        complexity: ComplexitySignals | None = None,
    ) -> RoutePlan:
        if not prompt.strip():
            raise RoutingError("prompt must not be empty")

        domain_key = domain.strip().lower()
        if domain_key not in {"coding", "research", "creative", "utility"}:
            raise RoutingError(
                "domain must be one of: coding, research, creative, utility"
            )

        complexity = complexity or ComplexitySignals()
        use_claude = self._FLAG_USE_CLAUDE in prompt
        no_opus = self._FLAG_NO_OPUS in prompt
        force_opus = self._FLAG_FORCE_OPUS in prompt

        if self._is_tradeoff_request(prompt):
            return self._plan_tradeoff(
                prompt=prompt,
                complexity=complexity,
                no_opus=no_opus,
                force_opus=force_opus,
            )

        if use_claude:
            target = (
                ModelCatalog.OPUS
                if (force_opus or complexity.should_escalate_to_opus)
                else ModelCatalog.SONNET
            )
            reason = (
                "explicit --use-claude override with strict Opus gate"
                if target == ModelCatalog.SONNET
                else "explicit --use-claude override escalated to Opus"
            )
            return self._single(target, reason=reason, mode="override")

        standard_model = self._domain_to_model(domain_key)
        return self._single(
            standard_model,
            reason=f"{domain_key} routing",
            mode="standard",
        )

    def _plan_tradeoff(
        self,
        *,
        prompt: str,
        complexity: ComplexitySignals,
        no_opus: bool,
        force_opus: bool,
    ) -> RoutePlan:
        parallel = (ModelCatalog.SONNET, ModelCatalog.GLM)

        if no_opus:
            self._validate_models(parallel)
            return RoutePlan(
                mode="tradeoff-no-opus",
                primary_model=None,
                parallel_models=parallel,
                judge_model=None,
                reason="tradeoff request with --no-opus",
            )

        should_use_opus = force_opus or (
            complexity.should_escalate_to_opus and self._is_high_impact(prompt)
        )
        if not should_use_opus:
            self._validate_models(parallel)
            return RoutePlan(
                mode="tradeoff-no-opus",
                primary_model=None,
                parallel_models=parallel,
                judge_model=None,
                reason="tradeoff defaulted to no-opus for cost efficiency",
            )

        self._validate_models((*parallel, ModelCatalog.OPUS))
        return RoutePlan(
            mode="tradeoff",
            primary_model=None,
            parallel_models=parallel,
            judge_model=ModelCatalog.OPUS,
            reason="tradeoff escalated to Opus under strict gate",
        )

    @staticmethod
    def _is_tradeoff_request(prompt: str) -> bool:
        return any(pattern.search(prompt) for pattern in TRADEOFF_PATTERNS)

    @staticmethod
    def _is_high_impact(prompt: str) -> bool:
        return any(pattern.search(prompt) for pattern in _HIGH_IMPACT_PATTERNS)

    @staticmethod
    def _domain_to_model(domain_key: str) -> str:
        mapping = {
            "coding": ModelCatalog.CODING,
            "research": ModelCatalog.RESEARCH,
            "creative": ModelCatalog.CREATIVE,
            "utility": ModelCatalog.UTILITY,
        }
        model = mapping[domain_key]
        DispatcherRouter._validate_models((model,))
        return model

    @staticmethod
    def _single(model: str, *, reason: str, mode: str) -> RoutePlan:
        DispatcherRouter._validate_models((model,))
        return RoutePlan(mode=mode, primary_model=model, reason=reason)

    @staticmethod
    def _validate_models(models: Iterable[str]) -> None:
        bad = [model for model in models if not MODEL_ID_PATTERN.match(model)]
        if bad:
            raise RoutingError(f"invalid model id format: {', '.join(bad)}")
