#!/usr/bin/env python3
"""Run repository Claude command specs locally through the Ollama provider."""

from __future__ import annotations

import argparse
import difflib
import html
import json
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import sys
import textwrap
from typing import Callable
import urllib.error
import urllib.parse
import urllib.request

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ai_job_search.model_provider import ModelProviderError, ModelRequest, ModelResponse
from ai_job_search.providers import OllamaProvider
from scripts.claude_adapter import REPO_ROOT as ADAPTER_REPO_ROOT
from scripts.claude_adapter import SUPPORTED_COMMANDS, build_model_request


PromptFn = Callable[[str], str]
PrintFn = Callable[[str], None]
WebFetcher = Callable[[str], str]


@dataclass(frozen=True)
class TerminalUI:
    """Small dependency-free terminal UI for interactive command runs."""

    print_func: PrintFn
    enabled: bool = True
    width: int = 78

    def banner(self, command_name: str) -> None:
        if not self.enabled:
            return
        self._box(["Local Ollama Command Runner", f"Workflow: /{command_name}"])

    def turn(self, turn_number: int) -> None:
        self.section(f"Turn {turn_number}")

    def section(self, title: str) -> None:
        if not self.enabled:
            return
        line = f"[{title}]"
        self.print_func(line)

    def message(self, title: str, body: str) -> None:
        if not self.enabled:
            return
        self.section(title)
        for wrapped_line in self._wrap(body):
            self.print_func(wrapped_line)

    def list_items(self, title: str, items: list[str], prefix: str = "- ") -> None:
        if not self.enabled or not items:
            return
        self.section(title)
        for item in items:
            wrapped = self._wrap(item, initial_indent=prefix, subsequent_indent="  ")
            for line in wrapped:
                self.print_func(line)

    def _box(self, lines: list[str]) -> None:
        border = "+" + "-" * (self.width - 2) + "+"
        self.print_func(border)
        for line in lines:
            wrapped_lines = self._wrap(line) or [""]
            for wrapped in wrapped_lines:
                inner = wrapped[: self.width - 4]
                self.print_func(f"| {inner.ljust(self.width - 4)} |")
        self.print_func(border)

    def _wrap(
        self,
        text: str,
        *,
        initial_indent: str = "",
        subsequent_indent: str = "",
    ) -> list[str]:
        return textwrap.wrap(
            text,
            width=max(self.width - 2, 20),
            initial_indent=initial_indent,
            subsequent_indent=subsequent_indent,
            replace_whitespace=False,
            drop_whitespace=False,
        ) or [initial_indent.rstrip()]


@dataclass(frozen=True)
class ProposedChange:
    path: str
    patch: str


@dataclass(frozen=True)
class RunnerResponse:
    summary: str
    questions: list[str]
    proposed_changes: list[ProposedChange]
    done: bool


@dataclass(frozen=True)
class CompileCheckResult:
    """Result of deterministic LaTeX/PDF checks for /apply outputs."""

    ran: bool
    ok: bool
    messages: list[str]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run .claude command workflows locally against Ollama.")
    parser.add_argument("--yes", action="store_true", help="Apply confirmed file writes without prompting.")
    parser.add_argument(
        "--plain",
        action="store_true",
        help="Disable the terminal UI and print plain line-oriented output.",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Show the model response and proposed diffs, then exit without asking questions or writing files.",
    )
    parser.add_argument("--model", help="Override OLLAMA_MODEL for this run.")
    parser.add_argument("--base-url", help="Override OLLAMA_BASE_URL for this run.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command_name in SUPPORTED_COMMANDS:
        command_parser = subparsers.add_parser(command_name, help=f"Run the /{command_name} workflow locally.")
        if command_name == "apply":
            job_source = command_parser.add_mutually_exclusive_group(required=True)
            job_source.add_argument("--job-file", help="Path to the captured job JSON file.")
            job_source.add_argument("--job-url", help="HTTP(S) URL of a job posting page to fetch as input.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    provider = OllamaProvider(model=args.model, base_url=args.base_url)
    return run_command(
        args.command,
        provider=provider,
        repo_root=ADAPTER_REPO_ROOT,
        non_interactive=args.non_interactive,
        assume_yes=args.yes,
        plain_output=args.plain,
        job_file=getattr(args, "job_file", None),
        job_url=getattr(args, "job_url", None),
    )


def run_command(
    command_name: str,
    *,
    provider: OllamaProvider,
    repo_root: Path = ADAPTER_REPO_ROOT,
    non_interactive: bool = False,
    assume_yes: bool = False,
    plain_output: bool = False,
    job_file: str | None = None,
    job_url: str | None = None,
    input_func: PromptFn = input,
    print_func: PrintFn = print,
    max_turns: int = 6,
    web_fetcher: WebFetcher | None = None,
) -> int:
    runtime_context = _build_runtime_context(
        command_name,
        repo_root=repo_root,
        job_file=job_file,
        job_url=job_url,
        web_fetcher=web_fetcher or fetch_job_posting_text,
    )
    transcript: list[str] = []
    ui = TerminalUI(print_func=print_func, enabled=not plain_output)

    ui.banner(command_name)

    for turn_number in range(1, max_turns + 1):
        ui.turn(turn_number)
        _, request = build_model_request(
            command_name,
            runtime_context=runtime_context,
            transcript=transcript,
            non_interactive=non_interactive,
            repo_root=repo_root,
        )

        try:
            response = provider.complete(request)
        except ModelProviderError as exc:
            print_func(f"ERROR: {exc}")
            return 1

        parsed = parse_runner_response(response)
        if parsed.summary:
            ui.message("Summary", parsed.summary)
            print_func(parsed.summary)

        if parsed.questions:
            ui.list_items("Questions", parsed.questions, prefix="? ")
            if non_interactive:
                for question in parsed.questions:
                    print_func(f"QUESTION: {question}")
                return 0

            for question in parsed.questions:
                answer = input_func(f"{question}\n> ")
                transcript.append(f"Question: {question}\nAnswer: {answer}")
            continue

        if parsed.proposed_changes:
            ui.section("Proposed Changes")
            _print_proposed_changes(parsed.proposed_changes, repo_root=repo_root, print_func=print_func)

            if non_interactive:
                return 0

            if assume_yes or _confirm_changes(input_func):
                written_paths = apply_proposed_changes(parsed.proposed_changes, repo_root=repo_root)
                transcript.append("Applied proposed changes:\n" + "\n".join(f"- {path}" for path in written_paths))
                ui.list_items("Applied Changes", written_paths)
                print_func("Applied changes:")
                for path in written_paths:
                    print_func(f"- {path}")

                if command_name == "apply":
                    compile_result = run_apply_compile_checks(written_paths, repo_root=repo_root)
                    if compile_result.ran:
                        ui.list_items("Compile Checks", compile_result.messages)
                        for message in compile_result.messages:
                            print_func(message)
                        transcript.append("Compile checks:\n" + "\n".join(f"- {message}" for message in compile_result.messages))
                        if not compile_result.ok:
                            return 1
            else:
                transcript.append("Operator declined the proposed changes.")
                ui.message("Write Status", "Operator declined the proposed changes. No files were written.")
                print_func("No files were changed.")

            if parsed.done:
                return 0
            continue

        if parsed.done:
            return 0

    print_func("ERROR: Runner stopped after too many turns without reaching a safe completion point.")
    return 1


def parse_runner_response(response: ModelResponse) -> RunnerResponse:
    text = response.text.strip()
    if not text:
        return RunnerResponse(summary="", questions=[], proposed_changes=[], done=True)

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return RunnerResponse(summary=text, questions=[], proposed_changes=[], done=True)

    if not isinstance(payload, dict):
        return RunnerResponse(summary=text, questions=[], proposed_changes=[], done=True)

    summary = payload.get("summary")
    if not isinstance(summary, str):
        summary = ""

    raw_questions = payload.get("questions", [])
    questions: list[str] = []
    if isinstance(raw_questions, list):
        for item in raw_questions:
            if isinstance(item, str) and item.strip():
                questions.append(item.strip())

    raw_changes = payload.get("proposed_changes", [])
    proposed_changes: list[ProposedChange] = []
    if isinstance(raw_changes, list):
        for item in raw_changes:
            if not isinstance(item, dict):
                continue
            path = item.get("path")
            patch = item.get("patch")
            if isinstance(path, str) and path.strip() and isinstance(patch, str):
                proposed_changes.append(ProposedChange(path=path.strip(), patch=patch))

    done = bool(payload.get("done", not questions and not proposed_changes))
    return RunnerResponse(
        summary=summary.strip(),
        questions=questions,
        proposed_changes=proposed_changes,
        done=done,
    )


def apply_proposed_changes(changes: list[ProposedChange], *, repo_root: Path) -> list[str]:
    written_paths: list[str] = []
    for change in changes:
        target = _resolve_repo_path(change.path, repo_root=repo_root)
        current_text = target.read_text(encoding="utf-8") if target.exists() else ""
        if current_text == change.patch:
            written_paths.append(str(target.relative_to(repo_root)).replace("\\", "/"))
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(change.patch, encoding="utf-8")
        written_paths.append(str(target.relative_to(repo_root)).replace("\\", "/"))
    return written_paths


def _build_runtime_context(
    command_name: str,
    *,
    repo_root: Path,
    job_file: str | None,
    job_url: str | None,
    web_fetcher: WebFetcher,
) -> str:
    context_lines = [f"Command: /{command_name}"]
    if command_name == "apply":
        if bool(job_file) == bool(job_url):
            raise ValueError("The /apply workflow requires exactly one of --job-file or --job-url.")

        if job_file:
            job_path = Path(job_file)
            if not job_path.is_absolute():
                job_path = (Path.cwd() / job_path).resolve()
            if not job_path.exists():
                raise FileNotFoundError(f"Job file not found: {job_path}")
            job_text = job_path.read_text(encoding="utf-8")
            relative_job_path = _describe_path(job_path, repo_root=repo_root)
            context_lines.extend(
                [
                    f"Job file: {relative_job_path}",
                    "Job file contents:",
                    job_text,
                ]
            )
        else:
            assert job_url is not None
            fetched_text = web_fetcher(job_url)
            context_lines.extend(
                [
                    f"Job URL: {job_url}",
                    "Fetched job posting text:",
                    fetched_text,
                ]
            )
    return "\n".join(context_lines)


def fetch_job_posting_text(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"Unsupported job URL scheme: {url}")

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ai-job-search-local-runner/1.0",
            "Accept": "text/html, text/plain;q=0.9, */*;q=0.1",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read(1_000_000)
            content_type = response.headers.get("Content-Type", "")
            charset = response.headers.get_content_charset() or "utf-8"
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Unable to fetch job URL {url}: {exc}") from exc

    if "pdf" in content_type.lower():
        raise RuntimeError("PDF job URLs are not supported by the local runner fetch path. Save the posting as text or JSON first.")

    decoded = body.decode(charset, errors="replace")
    if "html" in content_type.lower() or "<html" in decoded.lower():
        text = _html_to_text(decoded)
    else:
        text = decoded

    normalized = text.strip()
    if not normalized:
        raise RuntimeError(f"Fetched job URL {url} but extracted no visible text.")

    return normalized[:50_000]


def run_apply_compile_checks(written_paths: list[str], *, repo_root: Path) -> CompileCheckResult:
    tex_targets: list[Path] = []
    for relative_path in written_paths:
        target = _resolve_repo_path(relative_path, repo_root=repo_root)
        if target.suffix.lower() != ".tex":
            continue
        if target.parts[-2:-1] == ("cv",) or target.parts[-2:-1] == ("cover_letters",):
            tex_targets.append(target)

    if not tex_targets:
        return CompileCheckResult(ran=False, ok=True, messages=[])

    messages: list[str] = []
    overall_ok = True

    for tex_path in tex_targets:
        compile_result = _compile_tex_document(tex_path)
        messages.extend(compile_result.messages)
        overall_ok = overall_ok and compile_result.ok

    messages.append("Human review is still required even when compilation and page counts pass.")
    return CompileCheckResult(ran=True, ok=overall_ok, messages=messages)


def _compile_tex_document(tex_path: Path) -> CompileCheckResult:
    engine, expected_pages = _latex_engine_for(tex_path)
    try:
        result = subprocess.run(
            [engine, "-interaction=nonstopmode", tex_path.name],
            cwd=tex_path.parent,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return CompileCheckResult(
            ran=True,
            ok=False,
            messages=[f"{engine} is not installed or not on PATH, so {tex_path.name} could not be compiled."],
        )

    label = str(tex_path.relative_to(REPO_ROOT)).replace("\\", "/") if tex_path.is_relative_to(REPO_ROOT) else tex_path.name
    output_tail = _last_nonempty_lines(result.stdout + "\n" + result.stderr, limit=8)
    pdf_path = tex_path.with_suffix(".pdf")

    if result.returncode != 0 or not pdf_path.exists():
        messages = [f"{label}: {engine} failed with exit code {result.returncode}."]
        if output_tail:
            messages.append(f"{label}: compiler output tail -> {output_tail}")
        return CompileCheckResult(ran=True, ok=False, messages=messages)

    page_count = _count_pdf_pages(pdf_path)
    if page_count is None:
        return CompileCheckResult(
            ran=True,
            ok=False,
            messages=[f"{label}: compiled with {engine}, but PDF page count could not be determined."],
        )

    if page_count != expected_pages:
        return CompileCheckResult(
            ran=True,
            ok=False,
            messages=[
                f"{label}: compiled with {engine}, but page count is {page_count} and expected {expected_pages}.",
            ],
        )

    return CompileCheckResult(
        ran=True,
        ok=True,
        messages=[f"{label}: compiled with {engine}; PDF page count {page_count}/{expected_pages} passed."],
    )


def _latex_engine_for(tex_path: Path) -> tuple[str, int]:
    if "cover_letters" in tex_path.parts:
        return "xelatex", 1
    return "lualatex", 2


def _count_pdf_pages(pdf_path: Path) -> int | None:
    try:
        from pypdf import PdfReader  # type: ignore

        return len(PdfReader(str(pdf_path)).pages)
    except Exception:
        data = pdf_path.read_bytes()
        matches = re.findall(rb"/Type\s*/Page\b", data)
        return len(matches) or None


def _html_to_text(markup: str) -> str:
    text = re.sub(r"<script\b.*?</script>", " ", markup, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<style\b.*?</style>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _last_nonempty_lines(text: str, *, limit: int) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " | ".join(lines[-limit:])


def _print_proposed_changes(changes: list[ProposedChange], *, repo_root: Path, print_func: PrintFn) -> None:
    for change in changes:
        target = _resolve_repo_path(change.path, repo_root=repo_root)
        relative_path = str(target.relative_to(repo_root)).replace("\\", "/")
        before = target.read_text(encoding="utf-8") if target.exists() else ""
        after = change.patch
        diff_lines = difflib.unified_diff(
            before.splitlines(),
            after.splitlines(),
            fromfile=f"a/{relative_path}",
            tofile=f"b/{relative_path}",
            lineterm="",
        )
        print_func(f"Proposed change for {relative_path}:")
        rendered = "\n".join(diff_lines)
        print_func(rendered if rendered else "(no textual changes)")


def _confirm_changes(input_func: PromptFn) -> bool:
    answer = input_func("Apply these changes? [y/N]\n> ").strip().lower()
    return answer in {"y", "yes"}


def _resolve_repo_path(path_value: str, *, repo_root: Path) -> Path:
    candidate = Path(path_value)
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        resolved = (repo_root / candidate).resolve()

    repo_root_resolved = repo_root.resolve()
    if repo_root_resolved not in resolved.parents and resolved != repo_root_resolved:
        raise ValueError(f"Refusing to access path outside the repository root: {path_value}")
    return resolved


def _describe_path(path: Path, *, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path.resolve())


if __name__ == "__main__":
    sys.exit(main())