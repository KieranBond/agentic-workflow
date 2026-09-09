"""Shared utilities for skill-creator scripts."""

from pathlib import Path


def validate_claude_model(model: str | None) -> None:
    """Reject known non-Claude selectors before an evaluator launches subprocesses.

    Args:
        model: Claude Code's native model selector, or None for its configured default.

    Raises:
        ValueError: The selector uses Pi syntax or names another provider's model.

    This checks the harness boundary, not upstream model availability.
    """
    if not model:
        return
    suffix = model.rsplit(":", 1)[-1]
    thinking_suffix = suffix in {"off", "minimal", "low", "medium", "high", "xhigh", "max"}
    if "/" in model or model.startswith(("gpt-", "gemini-")) or thinking_suffix:
        raise ValueError(
            f"Claude Code cannot use Pi/other-provider model selector {model!r}. "
            "Choose a Claude-native ID or alias, without a provider/ prefix or :thinking suffix."
        )


def parse_skill_md(skill_path: Path) -> tuple[str, str, str]:
    """Parse a SKILL.md file, returning (name, description, full_content)."""
    content = (skill_path / "SKILL.md").read_text()
    lines = content.split("\n")

    if lines[0].strip() != "---":
        raise ValueError("SKILL.md missing frontmatter (no opening ---)")

    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        raise ValueError("SKILL.md missing frontmatter (no closing ---)")

    name = ""
    description = ""
    frontmatter_lines = lines[1:end_idx]
    i = 0
    while i < len(frontmatter_lines):
        line = frontmatter_lines[i]
        if line.startswith("name:"):
            name = line[len("name:"):].strip().strip('"').strip("'")
        elif line.startswith("description:"):
            value = line[len("description:"):].strip()
            # Handle YAML multiline indicators (>, |, >-, |-)
            if value in (">", "|", ">-", "|-"):
                continuation_lines: list[str] = []
                i += 1
                while i < len(frontmatter_lines) and (frontmatter_lines[i].startswith("  ") or frontmatter_lines[i].startswith("\t")):
                    continuation_lines.append(frontmatter_lines[i].strip())
                    i += 1
                description = " ".join(continuation_lines)
                continue
            else:
                description = value.strip('"').strip("'")
        i += 1

    return name, description, content
