#!/usr/bin/env python3
"""Validate package resources without requiring provider credentials."""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SKILLS = {
    "excalidraw",
    "gitlab-cli",
    "jira-cli",
    "mr-triage",
    "pr-review",
    "sentry",
    "skill-creator",
    "stop-slop",
    "subagent-delegation",
}
EXPECTED_AGENTS = {
    "review-correctness",
    "review-crossmodel",
    "review-design",
    "review-fresh-eyes",
    "review-performance",
    "review-security",
    "review-tests",
}
PROHIBITED_TEXT = {
    "Obsidian Security": "company-specific branding",
    "obsidiansec": "company-specific hostname or identifier",
    "plugins/obsidian-tools": "source-repository layout",
    "THRT-": "company-specific issue key",
    "/Users/": "machine-specific absolute path",
    "scripts/setup.sh": "obsolete global-agent setup",
}
PROHIBITED_PATH_PARTS = {"__pycache__", ".ruff_cache", ".pytest_cache", "node_modules"}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail(f"{path.relative_to(ROOT)} has no YAML frontmatter")
    try:
        block = text.split("---\n", 2)[1]
    except IndexError:
        fail(f"{path.relative_to(ROOT)} has unterminated YAML frontmatter")
    values: dict[str, str] = {}
    for line in block.splitlines():
        match = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*?)\s*$", line)
        if match:
            values[match.group(1)] = match.group(2).strip('"\'')
    return values


for path in ROOT.rglob("*"):
    if path.is_dir() and path.name in PROHIBITED_PATH_PARTS:
        fail(f"generated directory must not be committed: {path.relative_to(ROOT)}")
    if path.is_file() and path.suffix in {".pyc", ".pyo"}:
        fail(f"generated Python file must not be committed: {path.relative_to(ROOT)}")

package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
if package.get("version") != "0.1.0":
    fail("package.json version must match the release under test")
if package.get("pi", {}).get("skills") != ["./skills"]:
    fail("package.json must expose ./skills")
if package.get("pi", {}).get("subagents", {}).get("agents") != ["./agents"]:
    fail("package.json must expose ./agents through pi.subagents.agents")

skill_names: set[str] = set()
for path in sorted((ROOT / "skills").glob("*/SKILL.md")):
    meta = frontmatter(path)
    name = meta.get("name", "")
    if name != path.parent.name:
        fail(f"{path.relative_to(ROOT)} name {name!r} does not match its directory")
    if not meta.get("description"):
        fail(f"{path.relative_to(ROOT)} has no description")
    skill_names.add(name)
if skill_names != EXPECTED_SKILLS:
    fail(f"skill set mismatch: expected {sorted(EXPECTED_SKILLS)}, found {sorted(skill_names)}")

agent_names: set[str] = set()
for path in sorted((ROOT / "agents").glob("*.md")):
    meta = frontmatter(path)
    name = meta.get("name", "")
    if name != path.stem:
        fail(f"{path.relative_to(ROOT)} name {name!r} does not match its filename")
    if meta.get("model") != "inherit":
        fail(f"{path.relative_to(ROOT)} must default to model: inherit")
    if meta.get("inheritProjectContext") != "true":
        fail(f"{path.relative_to(ROOT)} must inherit repository instructions")
    agent_names.add(name)
if agent_names != EXPECTED_AGENTS:
    fail(f"agent set mismatch: expected {sorted(EXPECTED_AGENTS)}, found {sorted(agent_names)}")

for path in ROOT.rglob("*.json"):
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")

for path in ROOT.rglob("*.py"):
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        fail(f"invalid Python in {path.relative_to(ROOT)}: {exc}")

text_suffixes = {".md", ".json", ".py", ".sh", ".txt"}
for path in ROOT.rglob("*"):
    if path.resolve() == Path(__file__).resolve():
        continue
    if not path.is_file() or path.suffix not in text_suffixes:
        continue
    text = path.read_text(encoding="utf-8")
    for needle, reason in PROHIBITED_TEXT.items():
        if needle.lower() in text.lower():
            fail(f"{path.relative_to(ROOT)} contains {reason}: {needle!r}")
    if re.search(r"subagent_wait\s*\(", text):
        fail(f"{path.relative_to(ROOT)} invokes removed subagent_wait API")

print(f"Validated {len(skill_names)} skills and {len(agent_names)} review agents.")
