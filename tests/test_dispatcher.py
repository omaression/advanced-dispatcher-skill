import unittest

from dispatcher import ComplexitySignals, DispatcherRouter, RoutingError


class DispatcherRouterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.router = DispatcherRouter()

    def test_standard_domain_routes_to_expected_model(self) -> None:
        plan = self.router.route("Please implement endpoint", domain="coding")
        self.assertEqual(plan.mode, "standard")
        self.assertEqual(plan.primary_model, "openai-codex/gpt-5.3-codex")

    def test_tradeoff_defaults_to_no_opus_for_cost(self) -> None:
        plan = self.router.route(
            "Can you evaluate tradeoffs between these designs?", domain="coding"
        )
        self.assertEqual(plan.mode, "tradeoff-no-opus")
        self.assertEqual(
            plan.parallel_models,
            ("anthropic/claude-sonnet-4-6", "opencode-go/glm-5"),
        )
        self.assertIsNone(plan.judge_model)

    def test_tradeoff_with_no_opus_flag(self) -> None:
        plan = self.router.route(
            "compare approaches for service mesh --no-opus", domain="research"
        )
        self.assertEqual(plan.mode, "tradeoff-no-opus")
        self.assertIsNone(plan.judge_model)

    def test_tradeoff_escalates_to_opus_only_when_high_impact_and_complex(self) -> None:
        plan = self.router.route(
            "decide the best architecture for production compliance system",
            domain="coding",
            complexity=ComplexitySignals(
                interconnected_files=3,
                asks_ground_up_architecture=True,
            ),
        )
        self.assertEqual(plan.mode, "tradeoff")
        self.assertEqual(plan.judge_model, "anthropic/claude-opus-4-6")

    def test_tradeoff_force_opus(self) -> None:
        plan = self.router.route(
            "evaluate tradeoffs --force-opus", domain="coding"
        )
        self.assertEqual(plan.mode, "tradeoff")
        self.assertEqual(plan.judge_model, "anthropic/claude-opus-4-6")

    def test_use_claude_without_escalation(self) -> None:
        plan = self.router.route(
            "--use-claude please draft this single file refactor",
            domain="coding",
            complexity=ComplexitySignals(interconnected_files=3),
        )
        self.assertEqual(plan.mode, "override")
        self.assertEqual(plan.primary_model, "anthropic/claude-sonnet-4-6")

    def test_use_claude_escalates_to_opus_only_on_strong_signal_set(self) -> None:
        plan = self.router.route(
            "--use-claude build architecture",
            domain="coding",
            complexity=ComplexitySignals(
                interconnected_files=3,
                asks_ground_up_architecture=True,
            ),
        )
        self.assertEqual(plan.primary_model, "anthropic/claude-opus-4-6")

    def test_use_claude_force_opus(self) -> None:
        plan = self.router.route(
            "--use-claude --force-opus",
            domain="coding",
            complexity=ComplexitySignals(interconnected_files=0),
        )
        self.assertEqual(plan.primary_model, "anthropic/claude-opus-4-6")

    def test_invalid_domain_raises(self) -> None:
        with self.assertRaises(RoutingError):
            self.router.route("hello", domain="finance")

    def test_empty_prompt_raises(self) -> None:
        with self.assertRaises(RoutingError):
            self.router.route("   ", domain="coding")


if __name__ == "__main__":
    unittest.main()
