from __future__ import annotations

import json
from pathlib import Path

from ai_job_search.apply_from_file import generate_cover_letter_draft
from ai_job_search.model_provider import ModelProviderConnectionError, ModelRequest, ModelResponse


class FakeProvider:
    def __init__(self, text: str) -> None:
        self.text = text

    def complete(self, request: ModelRequest) -> ModelResponse:
        assert request.response_format == "text"
        assert "cover letter" in request.system_prompt.lower()
        return ModelResponse(text=self.text)


class FailingProvider:
    def complete(self, request: ModelRequest) -> ModelResponse:
        raise ModelProviderConnectionError("Ollama is not reachable")


def test_generate_cover_letter_draft_writes_markdown(tmp_path: Path) -> None:
    job_path = tmp_path / "job.json"
    job_path.write_text(
        json.dumps({
            "title": "Backend Developer",
            "company": "Example Co",
            "location": "Copenhagen",
            "source_url": "https://example.test/jobs/1",
            "description_text": "Build APIs.",
        }),
        encoding="utf-8",
    )

    fit = {
        "cover_letter_angle": "You are a backend-focused developer.",
        "matched_skills": ["Python", "APIs"],
        "missing_skills": ["Kubernetes"],
        "risks": ["Need to verify Python experience"],
    }

    output_dir = tmp_path / "applications" / "example-co-backend-developer"
    generate_cover_letter_draft(job_path, fit, FakeProvider("Dear Hiring Manager,\n\nTailored letter."), repo_root=tmp_path, output_dir=output_dir)

    draft_path = output_dir / "generated" / "cover-letter-draft.md"
    assert draft_path.exists()
    assert "Dear Hiring Manager" in draft_path.read_text(encoding="utf-8")


def test_generate_cover_letter_draft_writes_fallback_when_provider_fails(tmp_path: Path) -> None:
    job_path = tmp_path / "job.json"
    job_path.write_text(
        json.dumps({
            "title": "Senior Platform Engineer",
            "company": "Forterra",
            "location": "Remote",
            "source_url": "https://example.test/jobs/forterra",
            "description_text": "Build and scale backend systems.",
        }),
        encoding="utf-8",
    )

    profile_dir = tmp_path / "profile"
    profile_dir.mkdir(parents=True, exist_ok=True)
    (profile_dir / "resume_facts.md").write_text(
        """# Resume Facts

- Name: Vincent Morrill
- C#
- .NET Core
- SQL
- Enterprise application development
- Unit testing
""",
        encoding="utf-8",
    )

    fit = {
        "matched_skills": ["C#", ".NET Core", "SQL"],
        "missing_skills": [
            "Minimum 2-3 years of software engineering experience",
            "Working knowledge of Microsoft 365, Azure, Power Platform, or enterprise identity/access systems",
        ],
    }

    output_dir = tmp_path / "applications" / "forterra-senior-platform-engineer"
    generate_cover_letter_draft(job_path, fit, FailingProvider(), repo_root=tmp_path, output_dir=output_dir)

    draft_path = output_dir / "generated" / "cover-letter-draft.md"
    text = draft_path.read_text(encoding="utf-8")
    assert draft_path.exists()
    assert "Senior Platform Engineer" in text
    assert "Forterra" in text
    assert "Minimum 2-3 years" not in text
    assert "[Candidate Name]" not in text
    assert "[Your Name]" not in text
    assert "I lack" not in text
    assert "I do not meet" not in text
    assert "I don't meet" not in text
    assert "limited exposure" not in text
    assert "C#" in text
    assert ".NET Core" in text
    assert "SQL" in text
    assert "Vincent Morrill" in text


def test_generate_cover_letter_rewrites_invalid_provider_output(tmp_path: Path) -> None:
    class InvalidProvider:
        def complete(self, request: ModelRequest) -> ModelResponse:
            del request
            return ModelResponse(
                text=(
                    "Dear Hiring Manager,\n\n"
                    "I do not meet Minimum 2-3 years of software engineering experience.\n\n"
                    "Best regards,\n[Candidate Name]"
                )
            )

    job_path = tmp_path / "job.json"
    job_path.write_text(
        json.dumps(
            {
                "title": "Application Services Software Engineer",
                "company": "Forterra",
                "location": "Remote",
                "source_url": "https://example.test/jobs/forterra",
                "description_text": "Maintain internal application services.",
            }
        ),
        encoding="utf-8",
    )

    profile_dir = tmp_path / "profile"
    profile_dir.mkdir(parents=True, exist_ok=True)
    (profile_dir / "resume_facts.md").write_text(
        """# Resume Facts

- Name: Vincent Morrill
- C#
- .NET Core
- SQL
- Enterprise application development
- Unit testing
""",
        encoding="utf-8",
    )

    fit = {
        "matched_skills": ["C#", ".NET Core", "SQL", "enterprise application development"],
        "missing_skills": ["Working knowledge of Microsoft 365, Azure, Power Platform, or enterprise identity/access systems"],
    }

    output_dir = tmp_path / "applications" / "forterra-application-services-software-engineer"
    generate_cover_letter_draft(job_path, fit, InvalidProvider(), repo_root=tmp_path, output_dir=output_dir)

    text = (output_dir / "generated" / "cover-letter-draft.md").read_text(encoding="utf-8")
    assert "Minimum 2-3 years" not in text
    assert "[Candidate Name]" not in text
    assert "I do not meet" not in text
    assert "I lack" not in text
    assert "limited exposure" not in text
    assert "C#" in text
    assert ".NET Core" in text
    assert "SQL" in text
    assert "enterprise application" in text.lower()
