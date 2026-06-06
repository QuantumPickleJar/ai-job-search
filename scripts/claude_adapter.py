#!/usr/bin/env python3
"""Adapt repository command specs into local Ollama prompts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from ai_job_search.model_provider import ModelRequest


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMANDS_DIR = REPO_ROOT / ".claude" / "commands"
SUPPORTED_COMMANDS = ("setup", "expand", "apply", "reset")
DEFAULT_SYSTEM_PROMPT = (
    "You are an assistant that follows the repository's command spec exactly. "
    "Always provide structured output and list proposed file changes explicitly."
)
SAFETY_GUARDRAILS = "\n".join(
    [
        "Safety rules:",
        "- Operate locally and do not require paid APIs or hosted model services.",
        "- Never expose Ollama publicly or suggest public port forwarding for port 11434.",
        "- Never print, create, or commit secrets, tokens, VPN keys, or .env credentials.",
        "- Treat model output as advisory and require operator review before modifying profile or application files.",
        "- Keep changes additive or idempotent when the command spec says to do so.",
    ]
)
MAX_PROMPT_CHARS = 32000


@dataclass(frozen=True)
class CommandPrompt:
    """Parsed prompt parts for a repository command spec."""

    command_name: str
    command_path: Path
    system_prompt: str
    user_prompt: str


def resolve_command_path(command_name: str, repo_root: Path = REPO_ROOT) -> Path:
    normalized = command_name.strip().lower()
    if normalized not in SUPPORTED_COMMANDS:
        supported = ", ".join(SUPPORTED_COMMANDS)
        raise ValueError(f"Unsupported command {command_name!r}. Expected one of: {supported}.")

    command_path = repo_root / ".claude" / "commands" / f"{normalized}.md"
    if not command_path.exists():
        raise FileNotFoundError(f"Command spec not found: {command_path}")
    return command_path


def load_command_prompt(command_name: str, repo_root: Path = REPO_ROOT) -> CommandPrompt:
    command_path = resolve_command_path(command_name, repo_root=repo_root)
    markdown = command_path.read_text(encoding="utf-8")
    system_prompt, user_prompt = _extract_prompt_sections(markdown)
    return CommandPrompt(
        command_name=command_name,
        command_path=command_path,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )


def build_model_request(
    command_name: str,
    *,
    runtime_context: str = "",
    transcript: list[str] | None = None,
    non_interactive: bool = False,
    repo_root: Path = REPO_ROOT,
) -> tuple[CommandPrompt, ModelRequest]:
    prompt = load_command_prompt(command_name, repo_root=repo_root)
    transcript_lines = transcript or []
    parts = [
        "Repository command workflow:",
        prompt.user_prompt,
    ]

    if runtime_context.strip():
        parts.extend(["", "Runtime context:", runtime_context.strip()])

    if transcript_lines:
        parts.extend(["", "Operator transcript:", "\n".join(transcript_lines)])

    # The runner uses a strict JSON contract so it can pause on questions and show
    # a computed diff before any write. The `patch` field intentionally carries the
    # full replacement text for a file; the runner derives the visible unified diff.
    parts.extend(
        [
            "",
            "Response contract:",
            "Return one JSON object with keys: summary, questions, proposed_changes, done.",
            "- summary: concise operator-facing status update.",
            "- questions: array of strings when the spec says to ask the user. Use an empty array otherwise.",
            "- proposed_changes: array of objects with path and patch. The patch must be the full replacement text for the file at path.",
            "- done: true only when the current command can stop safely.",
            "Do not assume any proposed change has been written until the transcript says it was applied.",
            "If the workflow cannot continue without operator input, put that input in questions and stop there.",
        ]
    )

    if non_interactive:
        parts.extend(
            [
                "",
                "Execution mode:",
                "This run is non-interactive. Return any pending questions and proposed changes, then stop.",
            ]
        )

    user_prompt = _truncate("\n".join(parts))
    system_prompt = _truncate(f"{prompt.system_prompt}\n\n{SAFETY_GUARDRAILS}")
    return prompt, ModelRequest(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.1,
        max_tokens=1200,
        response_format="json",
    )


def _extract_prompt_sections(markdown: str) -> tuple[str, str]:
    normalized = markdown.replace("\r\n", "\n").strip()
    explicit_system = _extract_explicit_section(normalized, "system")
    body = _remove_title(normalized)
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", body) if part.strip()]

    if explicit_system:
        system_prompt = explicit_system
        user_prompt = body
    elif paragraphs:
        first_paragraph = paragraphs[0]
        if _looks_like_system_prompt(first_paragraph):
            system_prompt = first_paragraph
            user_prompt = body[len(first_paragraph) :].strip() or body
        else:
            system_prompt = DEFAULT_SYSTEM_PROMPT
            user_prompt = body
    else:
        system_prompt = DEFAULT_SYSTEM_PROMPT
        user_prompt = normalized

    return system_prompt.strip(), user_prompt.strip()


def _extract_explicit_section(markdown: str, section_name: str) -> str:
    pattern = re.compile(
        rf"^##+\s+{re.escape(section_name)}\s*$\n(?P<body>.*?)(?=^##+\s+|\Z)",
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(markdown)
    if not match:
        return ""
    return match.group("body").strip()


def _looks_like_system_prompt(paragraph: str) -> bool:
    lowered = paragraph.lower()
    return lowered.startswith(("you are", "your goal is", "you are running", "you are orchestrating"))


def _remove_title(markdown: str) -> str:
    lines = markdown.splitlines()
    if lines and lines[0].startswith("#"):
        return "\n".join(lines[1:]).strip()
    return markdown


def _truncate(text: str, max_chars: int = MAX_PROMPT_CHARS) -> str:
    if len(text) <= max_chars:
        return text
    overflow = len(text) - max_chars
    return (
        f"{text[:max_chars].rstrip()}\n\n"
        f"[Truncated {overflow} trailing characters to keep the prompt under the local runner budget.]"
    )