from __future__ import annotations

import json
from pathlib import Path

from ai_job_search.model_provider import ModelResponse
from scripts import agent_runner


REPO_ROOT = Path(__file__).resolve().parents[1]


class FakeProvider:
    def __init__(self, payloads: list[dict[str, object]]) -> None:
        self.payloads = payloads
        self.requests = []

    def complete(self, request):
        self.requests.append(request)
        payload = self.payloads.pop(0)
        return ModelResponse(text=json.dumps(payload))


def test_setup_loads_matching_command_spec_and_composes_request(capsys) -> None:
    provider = FakeProvider(
        [
            {
                "summary": "Inventory complete.",
                "questions": [],
                "proposed_changes": [],
                "done": True,
            }
        ]
    )

    exit_code = agent_runner.run_command("setup", provider=provider, repo_root=REPO_ROOT)

    captured = capsys.readouterr()
    request = provider.requests[0]
    assert exit_code == 0
    assert "Local Ollama Command Runner" in captured.out
    assert "Workflow: /setup" in captured.out
    assert "Inventory complete." in captured.out
    assert request.response_format == "json"
    assert "There are three paths into setup" in request.user_prompt
    assert "Never expose Ollama publicly" in request.system_prompt


def test_apply_includes_job_file_contents_in_runtime_context(tmp_path) -> None:
    repo_root = tmp_path
    command_dir = repo_root / ".claude" / "commands"
    command_dir.mkdir(parents=True)
    (command_dir / "apply.md").write_text(
        "# /apply\n\nYou are orchestrating a workflow.\n\n## Step 0\nRead the job file.\n",
        encoding="utf-8",
    )
    job_file = repo_root / "job.json"
    job_file.write_text('{"company":"Example Co","title":"Developer"}', encoding="utf-8")
    provider = FakeProvider(
        [
            {
                "summary": "Loaded job file.",
                "questions": [],
                "proposed_changes": [],
                "done": True,
            }
        ]
    )

    exit_code = agent_runner.run_command(
        "apply",
        provider=provider,
        repo_root=repo_root,
        job_file=str(job_file),
    )

    request = provider.requests[0]
    assert exit_code == 0
    assert '"company":"Example Co"' in request.user_prompt
    assert "Job file:" in request.user_prompt


def test_apply_fetches_job_url_into_runtime_context(tmp_path) -> None:
    repo_root = tmp_path
    command_dir = repo_root / ".claude" / "commands"
    command_dir.mkdir(parents=True)
    (command_dir / "apply.md").write_text(
        "# /apply\n\nYou are orchestrating a workflow.\n\n## Step 0\nRead the job posting.\n",
        encoding="utf-8",
    )
    provider = FakeProvider(
        [
            {
                "summary": "Loaded job URL.",
                "questions": [],
                "proposed_changes": [],
                "done": True,
            }
        ]
    )
    fetched_urls = []

    def fake_fetch(url: str) -> str:
        fetched_urls.append(url)
        return "Example Co Senior Developer Copenhagen .NET Docker"

    exit_code = agent_runner.run_command(
        "apply",
        provider=provider,
        repo_root=repo_root,
        job_url="https://example.com/jobs/123",
        web_fetcher=fake_fetch,
    )

    request = provider.requests[0]
    assert exit_code == 0
    assert fetched_urls == ["https://example.com/jobs/123"]
    assert "Job URL: https://example.com/jobs/123" in request.user_prompt
    assert "Example Co Senior Developer Copenhagen .NET Docker" in request.user_prompt


def test_proposed_patch_is_diffed_and_waits_for_confirmation(tmp_path, capsys) -> None:
    repo_root = tmp_path
    command_dir = repo_root / ".claude" / "commands"
    command_dir.mkdir(parents=True)
    (command_dir / "expand.md").write_text(
        "# /expand\n\nYou are enriching the candidate profile.\n\n## Step 0\nAsk for confirmation before writing.\n",
        encoding="utf-8",
    )
    profile_file = repo_root / "profile.md"
    profile_file.write_text("old line\n", encoding="utf-8")
    provider = FakeProvider(
        [
            {
                "summary": "One change proposed.",
                "questions": [],
                "proposed_changes": [
                    {
                        "path": "profile.md",
                        "patch": "old line\nnew line\n",
                    }
                ],
                "done": True,
            }
        ]
    )
    prompts = []

    def deny(prompt: str) -> str:
        prompts.append(prompt)
        return "n"

    exit_code = agent_runner.run_command(
        "expand",
        provider=provider,
        repo_root=repo_root,
        input_func=deny,
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert prompts == ["Apply these changes? [y/N]\n> "]
    assert "--- a/profile.md" in captured.out
    assert "+new line" in captured.out
    assert profile_file.read_text(encoding="utf-8") == "old line\n"


def test_plain_output_skips_terminal_ui(capsys) -> None:
    provider = FakeProvider(
        [
            {
                "summary": "Plain output only.",
                "questions": [],
                "proposed_changes": [],
                "done": True,
            }
        ]
    )

    exit_code = agent_runner.run_command(
        "setup",
        provider=provider,
        repo_root=REPO_ROOT,
        plain_output=True,
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Plain output only." in captured.out
    assert "Local Ollama Command Runner" not in captured.out


def test_apply_runs_compile_hook_after_confirmed_tex_write(tmp_path, monkeypatch, capsys) -> None:
    repo_root = tmp_path
    command_dir = repo_root / ".claude" / "commands"
    command_dir.mkdir(parents=True)
    (command_dir / "apply.md").write_text(
        "# /apply\n\nYou are orchestrating a workflow.\n\n## Step 0\nDraft documents.\n",
        encoding="utf-8",
    )
    job_file = repo_root / "job.json"
    job_file.write_text('{"company":"Example Co","title":"Developer"}', encoding="utf-8")
    provider = FakeProvider(
        [
            {
                "summary": "Drafts ready.",
                "questions": [],
                "proposed_changes": [
                    {
                        "path": "cv/main_example.tex",
                        "patch": "\\documentclass{article}\n\\begin{document}\nHello\n\\end{document}\n",
                    }
                ],
                "done": True,
            }
        ]
    )

    def fake_compile(written_paths: list[str], *, repo_root: Path):
        assert written_paths == ["cv/main_example.tex"]
        return agent_runner.CompileCheckResult(
            ran=True,
            ok=True,
            messages=["cv/main_example.tex: compiled with lualatex; PDF page count 2/2 passed."],
        )

    monkeypatch.setattr(agent_runner, "run_apply_compile_checks", fake_compile)

    exit_code = agent_runner.run_command(
        "apply",
        provider=provider,
        repo_root=repo_root,
        job_file=str(job_file),
        input_func=lambda prompt: "y",
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "compiled with lualatex; PDF page count 2/2 passed." in captured.out