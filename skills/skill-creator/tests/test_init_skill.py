"""Tests for safe skill scaffolding paths."""

import tempfile
import unittest
from pathlib import Path

from scripts.init_skill import create_skill_at_path, validate_skill_name


class SkillNameValidationTests(unittest.TestCase):
    def test_accepts_hyphen_case_names(self) -> None:
        for name in ("skill", "skill-2", "v2-skill"):
            with self.subTest(name=name):
                self.assertEqual(validate_skill_name(name), name)

    def test_rejects_unsafe_or_malformed_names(self) -> None:
        names = (
            "../escape",
            "/tmp/escape",
            "two--hyphens",
            "-leading",
            "trailing-",
            "Uppercase",
            "has_underscore",
            "a" * 65,
            "{skill}",
        )
        for name in names:
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate_skill_name(name)

    def test_rejects_traversal_before_creating_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory) / "skills"
            with self.assertRaises(ValueError):
                create_skill_at_path("../escape", base)
            self.assertFalse(base.exists())
            self.assertFalse((Path(directory) / "escape").exists())

    def test_creates_valid_skill_under_requested_base(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory) / "skills"
            created = create_skill_at_path("safe-skill", base)
            self.assertEqual(created, base.resolve() / "safe-skill")
            self.assertTrue((created / "SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
