"""Adapter from the service API to the Phase 2 apply-from-file workflow."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from ai_job_search.apply_from_file import ApplyFromFileError, apply_from_file
from ai_job_search.fit_scoring import load_profile_context
from ai_job_search.model_provider import ModelProviderError, ModelRequest
from ai_job_search.providers import OllamaProvider

from app.config import Settings
from app.services.job_store import is_safe_identifier


class ProcessingError(RuntimeError):
    """Raised when a job cannot be processed into an application workspace."""


LOGGER = logging.getLogger(__name__)

DEFAULT_CANDIDATE_NAME = "Vincent Morrill"
DEFAULT_CANDIDATE_EMAIL = "vince.codefactory@outlook.com"

REQUIREMENT_MARKERS = (
    "minimum",
    "years",
    "required",
    "working knowledge",
    "must have",
    "degree",
    "bachelor",
)

BLOCKED_COVER_LETTER_PHRASES = (
    "[candidate name]",
    "[your name]",
    "[mention",
    "minimum 2-3 years",
    "i do not meet",
    "i don't meet",
    "i lack",
    "lacks the minimum",
    "does not meet the minimum",
    "limited exposure",
    "actively deepening my experience with",
)


def candidate_identity() -> dict[str, str]:
    return {
        "name": DEFAULT_CANDIDATE_NAME,
        "email": DEFAULT_CANDIDATE_EMAIL,
    }


def _clean_text_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = str(item).strip()
        if text:
            items.append(text)
    return items


def _is_requirement_like(text: str) -> bool:
    lowered = text.casefold()
    return any(marker in lowered for marker in REQUIREMENT_MARKERS)


def _split_requirement_like(items: list[str]) -> tuple[list[str], list[str]]:
    requirements: list[str] = []
    skills: list[str] = []
    for item in items:
        if _is_requirement_like(item):
            requirements.append(item)
        else:
            skills.append(item)
    return requirements, skills


def build_cover_letter_fit_view(fit: dict[str, Any]) -> dict[str, Any]:
    missing_skills = _clean_text_list(fit.get("missing_skills"))
    missing_requirements, _ = _split_requirement_like(missing_skills)
    risks = _clean_text_list(fit.get("risks"))
    internal_risks = [*risks, *missing_requirements]

    requirements_blob = " ".join(internal_risks).casefold()
    if any(token in requirements_blob for token in ("microsoft 365", "azure", "power platform", "identity", "access")):
        internal_risks.append("Specific Microsoft platform experience is not verified.")

    return {
        "matched_skills": _clean_text_list(fit.get("matched_skills")),
        "reasons_to_apply": _clean_text_list(fit.get("reasons_to_apply")),
        "resume_keywords_to_include": _clean_text_list(fit.get("resume_keywords_to_include")),
        "suggested_resume_angle": str(fit.get("suggested_resume_angle") or "").strip(),
        "cover_letter_angle": str(fit.get("cover_letter_angle") or "").strip(),
        "internal_risks": internal_risks,
    }


def _sanitize_generated_markdown(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`\n")
        if cleaned.startswith("markdown"):
            parts = cleaned.split("\n", 1)
            cleaned = parts[1] if len(parts) > 1 else ""
    return cleaned.strip()


def validate_cover_letter_output(text: str, profile_context: str) -> list[str]:
    lowered = text.casefold()
    errors: list[str] = []

    for blocked in BLOCKED_COVER_LETTER_PHRASES:
        if blocked in lowered:
            errors.append(f"blocked phrase present: {blocked}")

    if "certification" in lowered and "certification" not in profile_context.casefold():
        errors.append("blocked phrase present: certification claims are not verified in profile facts")

    return errors


def build_cover_letter_prompt(
    job: dict[str, Any],
    fit_view: dict[str, Any],
    notes: str,
    profile_context: str,
    identity: dict[str, str],
) -> str:
    return f"""Write a complete, job-specific cover letter in Markdown.

Candidate identity (use exactly for signature):
- Name: {identity['name']}
- Email: {identity['email']}

Output format:
- Start with: Dear Hiring Manager,
- 3 to 5 short paragraphs
- End with:
  Best regards,
  {identity['name']}

Hard rules:
- Emphasize only verified strengths from profile facts.
- Mention only supported technologies.
- Missing skills, risks, and questions are internal planning context and must not be copied into applicant-facing prose.
- Do not use self-disqualifying language.
- Do not say: "I do not meet", "I don't meet", "I lack", "limited exposure", or "actively deepening my experience with".
- Do not claim or imply the candidate lacks 2-3 years of general software/application development experience.
- If specific Microsoft platform experience is not verified, use neutral language such as:
  "I am prepared to ramp into {job.get('company', 'the employer')}'s Microsoft platform environment where needed."
- Do not use placeholders like [Candidate Name], [Your Name], or [mention ...].

Candidate profile context:
{profile_context}

Cover-letter-safe fit context JSON:
{json.dumps(fit_view, ensure_ascii=False, indent=2)}

Captured job JSON:
{json.dumps(job, ensure_ascii=False, indent=2)}

Cover letter notes:
{notes}
"""


def _build_safe_fallback_cover_letter(
    job: dict[str, Any],
    fit_view: dict[str, Any],
    identity: dict[str, str],
) -> str:
    title = str(job.get("title") or "the role").strip() or "the role"
    company = str(job.get("company") or "the company").strip() or "the company"
    skills = fit_view.get("matched_skills") if isinstance(fit_view.get("matched_skills"), list) else []
    selected = [str(item).strip() for item in skills if str(item).strip()][:4]
    skills_text = ", ".join(selected) if selected else "C#, .NET Core, SQL, and enterprise application development"

    risk_blob = " ".join(fit_view.get("internal_risks", []) if isinstance(fit_view.get("internal_risks"), list) else []).casefold()
    ramp_sentence = ""
    if any(token in risk_blob for token in ("microsoft 365", "azure", "power platform", "identity", "access")):
        ramp_sentence = f" I am prepared to ramp into {company}'s Microsoft platform environment where needed."

    return (
        "Dear Hiring Manager,\n\n"
        + f"I am excited to apply for the {title} position at {company}. My background in {skills_text} aligns well with the role's focus on supporting business-critical application services.\n\n"
        + "In my recent development work, I have contributed to internal and enterprise-grade systems by implementing features, writing unit tests, improving workflow behavior, and collaborating through pull-request-based development.\n\n"
        + f"I am especially interested in {company}'s application services work because it combines software development, stakeholder support, and operational problem-solving."
        + ramp_sentence
        + "\n\n"
        + "Thank you for your time and consideration. I would welcome the opportunity to discuss how my application development experience can support your team.\n\n"
        + "Best regards,\n\n"
        + identity["name"]
    )


def _read_json_file(path: Path, label: str) -> dict[str, Any]:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProcessingError(f"cannot read {label} from {path.name}") from exc
    if not isinstance(parsed, dict):
        raise ProcessingError(f"{label} in {path.name} must be a JSON object")
    return parsed


def _read_text_file(path: Path, label: str) -> str:
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ProcessingError(f"cannot read {label} from {path.name}") from exc
    if not text:
        raise ProcessingError(f"{label} in {path.name} is empty")
    return text


def generate_cover_letter(application_id: str, settings: Settings) -> Path:
    if not is_safe_identifier(application_id):
        raise ProcessingError(f"invalid application id: {application_id}")

    app_dir = settings.app_data_dir / "applications" / application_id
    if not app_dir.is_dir():
        raise ProcessingError(f"application workspace not found: {application_id}")

    job = _read_json_file(app_dir / "job.json", "job")
    fit = _read_json_file(app_dir / "fit-analysis.json", "fit analysis")
    notes = _read_text_file(app_dir / "cover-letter-notes.md", "cover letter notes")
    identity = candidate_identity()
    profile_context = load_profile_context(settings.app_data_dir)
    fit_view = build_cover_letter_fit_view(fit)

    provider = OllamaProvider(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        timeout_seconds=300,
    )
    request = ModelRequest(
        system_prompt="You write concise, factual, role-targeted cover letters.",
        user_prompt=build_cover_letter_prompt(job, fit_view, notes, profile_context, identity),
        temperature=0.3,
        max_tokens=1400,
        response_format="text",
    )

    LOGGER.info("cover-letter: starting provider call", extra={"application_id": application_id})
    try:
        response = provider.complete(request)
        LOGGER.info("cover-letter: provider call completed", extra={"application_id": application_id})
        content = _sanitize_generated_markdown(response.text)
    except ModelProviderError:
        LOGGER.exception("cover-letter: provider call failed; using deterministic safe fallback", extra={"application_id": application_id})
        content = _build_safe_fallback_cover_letter(job, fit_view, identity)

    errors = validate_cover_letter_output(content, profile_context)
    if errors:
        LOGGER.error(
            "cover-letter: validation rejected output",
            extra={"application_id": application_id, "errors": errors},
        )
        raise ProcessingError("cover letter output failed validation: " + "; ".join(errors))

    output_path = app_dir / "cover-letter.md"
    LOGGER.info("cover-letter: writing cover-letter.md", extra={"application_id": application_id, "path": str(output_path)})
    output_path.write_text(content + "\n", encoding="utf-8")
    return output_path


def process_job(job_path: Path, settings: Settings) -> Path:
    provider = OllamaProvider(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
    )
    try:
        return apply_from_file(
            job_path,
            provider=provider,
            repo_root=settings.app_data_dir,
        )
    except (ApplyFromFileError, ModelProviderError, OSError) as exc:
        raise ProcessingError(str(exc)) from exc
