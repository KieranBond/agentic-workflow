"""Keep Pi model selectors out of the Claude Code evaluator."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.improve_description import _call_claude
from scripts.run_eval import run_eval, run_single_query
from scripts.run_loop import run_loop
from scripts.utils import validate_claude_model


class ModelBoundaryTests(unittest.TestCase):
    def test_accepts_native_ids_aliases_and_default(self) -> None:
        for model in (None, "sonnet", "opus", "haiku", "claude-sonnet-4-5-20250929"):
            with self.subTest(model=model):
                validate_claude_model(model)

    def test_rejects_pi_and_other_provider_selectors(self) -> None:
        models = (
            "openai-codex/gpt-6-astra",
            "anthropic/claude-sonnet-5",
            "gpt-6-astra",
            "gemini-2.5-pro",
            "claude-sonnet-5:high",
        )
        for model in models:
            with self.subTest(model=model), self.assertRaisesRegex(ValueError, "Claude Code"):
                validate_claude_model(model)

    def test_query_rejects_before_writing_or_spawning(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch("subprocess.Popen") as spawn:
            with self.assertRaisesRegex(ValueError, "Claude Code"):
                run_single_query("query", "skill", "description", 1, directory, "gpt-6-astra")
            spawn.assert_not_called()
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_batch_rejects_before_worker_pool(self) -> None:
        with patch("scripts.run_eval.ProcessPoolExecutor") as pool:
            with self.assertRaisesRegex(ValueError, "Claude Code"):
                run_eval([], "skill", "description", 1, 1, Path.cwd(), model="gpt-6-astra")
            pool.assert_not_called()

    def test_loop_rejects_before_reading_skill(self) -> None:
        with patch("scripts.run_loop.parse_skill_md") as read_skill:
            with self.assertRaisesRegex(ValueError, "Claude Code"):
                run_loop([], Path.cwd(), None, 1, 1, 1, 1, 0.5, 0, "gpt-6-astra", False)
            read_skill.assert_not_called()

    def test_improvement_rejects_before_spawning(self) -> None:
        with patch("subprocess.run") as spawn:
            with self.assertRaisesRegex(ValueError, "Claude Code"):
                _call_claude("prompt", "anthropic/claude-sonnet-5")
            spawn.assert_not_called()

    def test_native_model_is_forwarded_unchanged(self) -> None:
        with patch("subprocess.run") as spawn:
            spawn.return_value.returncode = 0
            spawn.return_value.stdout = "description"
            self.assertEqual(_call_claude("prompt", "sonnet"), "description")
            self.assertEqual(spawn.call_args.args[0][-2:], ["--model", "sonnet"])


if __name__ == "__main__":
    unittest.main()
