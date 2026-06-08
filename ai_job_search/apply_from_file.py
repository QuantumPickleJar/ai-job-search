"""Create a reviewable application workspace from a captured job JSON file."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ai_job_search.fit_scoring import FitScoringError, load_profile_context, score_job_file, validate_fit_analysis
from ai_job_search.job_validation import load_json, validate_job
from ai_job_search.model_provider import ModelProvider, ModelRequest
from ai_job_search.model_provider import ModelProviderError


class ApplyFromFileError(RuntimeError):
    """Raised when the apply-from-file workflow cannot complete."""


REQUIREMENT_LIKE_MARKERS = (
    "minimum",
    "years",
    "required",
    "requirement",
    "degree",
    "bachelor",
    "must have",
    "working knowledge of",
    "experience with",
)

COVER_LETTER_BLOCKLIST = (
    "minimum 2-3 years",
    "i do not meet",
    "i don't meet",
    "i lack",
    "lacks the minimum",
    "limited exposure",
    "actively deepening my experience with minimum",
    "[candidate name]",
    "[your name]",
    "[mention",
)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower())
    slug = slug.strip("-")
    return slug or "unknown"


def application_slug(job: dict[str, Any]) -> str:
    company = slugify(str(job.get("company", "unknown-company")))
    title = slugify(str(job.get("title", "unknown-role")))
    return f"{company}-{title}"


def application_dir_for_job(job: dict[str, Any], repo_root: Path) -> Path:
    return repo_root / "applications" / application_slug(job)


def latest_captured_job(repo_root: Path) -> Path:
    captured_dir = repo_root / "job_intake" / "captured_jobs"
    candidates = [path for path in captured_dir.glob("*.json") if path.is_file()]
    if not candidates:
        raise ApplyFromFileError(f"no JSON files found in {captured_dir}")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def load_valid_job(job_path: Path) -> dict[str, Any]:
    job, load_errors = load_json(job_path)
    if load_errors:
        raise ApplyFromFileError("; ".join(load_errors))

    errors = validate_job(job)
    if errors:
        raise ApplyFromFileError("job validation failed: " + "; ".join(errors))

    if not isinstance(job, dict):
        raise ApplyFromFileError("job validation failed: root value must be an object")
    return job


def load_valid_fit_analysis(path: Path) -> dict[str, Any]:
    analysis, load_errors = load_json(path)
    if load_errors:
        raise ApplyFromFileError("; ".join(load_errors))

    errors = validate_fit_analysis(analysis)
    if errors:
        raise ApplyFromFileError("fit analysis validation failed: " + "; ".join(errors))

    if not isinstance(analysis, dict):
        raise ApplyFromFileError("fit analysis validation failed: root value must be an object")
    return analysis


def ensure_fit_analysis(job_path: Path, app_dir: Path, provider: ModelProvider, repo_root: Path) -> dict[str, Any]:
    fit_path = app_dir / "fit-analysis.json"
    if fit_path.exists():
        return load_valid_fit_analysis(fit_path)

    try:
        score_job_file(job_path, provider=provider, repo_root=repo_root, output_dir=app_dir)
    except FitScoringError as exc:
        raise ApplyFromFileError(str(exc)) from exc

    return load_valid_fit_analysis(fit_path)


def format_list(items: Any, fallback: str = "None identified yet.") -> str:
    if not isinstance(items, list) or not items:
        return f"- {fallback}"
    lines = []
    for item in items:
        text = str(item).strip()
        if text:
            lines.append(f"- {text}")
    return "\n".join(lines) if lines else f"- {fallback}"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_resume_targeting(path: Path, job: dict[str, Any], fit: dict[str, Any]) -> None:
    title = job.get("title", "Unknown role")
    company = job.get("company", "Unknown company")
    score = fit.get("overall_score", "unknown")
    recommendation = fit.get("recommendation", "unknown")
    angle = fit.get("suggested_resume_angle", "")

    content = f"""# Resume Targeting Notes

## Job

- Title: {title}
- Company: {company}
- Source: {job.get("source_url", "")}

## Fit Summary

- Overall score: {score}
- Recommendation: {recommendation}

## Skills To Emphasize

{format_list(fit.get("matched_skills"))}

## Missing Skills To Avoid Overclaiming

{format_list(fit.get("missing_skills"))}

## Suggested Resume Angle

{angle or "Review the fit analysis and write a grounded angle before creating a tailored resume."}

## Keywords To Consider

{format_list(fit.get("resume_keywords_to_include"))}

## Suggested Bullets To Consider

These are suggestions only. Do not paste them into a final resume until each claim is verified against profile facts.

{format_list(fit.get("reasons_to_apply"))}
"""
    path.write_text(content, encoding="utf-8")


def write_cover_letter_notes(path: Path, job: dict[str, Any], fit: dict[str, Any]) -> None:
    missing_raw = fit.get("missing_skills")
    missing_items = [str(item).strip() for item in missing_raw] if isinstance(missing_raw, list) else []
    requirement_like, skill_like = _split_requirement_like_items(missing_items)
    warnings: list[str] = []
    warnings.extend(skill_like)
    req_text = " ".join(requirement_like).lower()
    if any(token in req_text for token in ("microsoft 365", "azure", "power platform", "identity", "access")):
        warnings.append("Specific Microsoft platform experience is not verified.")
    if not warnings:
        warnings = fit.get("do_not_claim") if isinstance(fit.get("do_not_claim"), list) else []

    content = f"""# Cover Letter Notes

## Cover Letter Angle

{fit.get("cover_letter_angle") or "Review the fit analysis and write a grounded cover letter angle."}

## Company And Job Hooks

- Company: {job.get("company", "Unknown company")}
- Role: {job.get("title", "Unknown role")}
- Location: {job.get("location", "Unknown location")}
- Source: {job.get("source_url", "")}

## Candidate Strengths To Emphasize

{format_list(fit.get("matched_skills"))}

## Warnings About Claims Not To Make

{format_list(warnings, "No warnings identified yet. Still verify every claim against profile facts.")}

## Questions Before Applying

{format_list(fit.get("questions_to_answer_before_applying"))}
"""
    path.write_text(content, encoding="utf-8")


def write_application_checklist(path: Path, job: dict[str, Any], fit: dict[str, Any]) -> None:
    content = f"""# Application Checklist

- [ ] Review job details for {job.get("company", "Unknown company")} - {job.get("title", "Unknown role")}
- [ ] Review fit score: {fit.get("overall_score", "unknown")} ({fit.get("recommendation", "unknown")})
- [ ] Review tailored resume notes in `resume-targeting.md`
- [ ] Review cover letter notes in `cover-letter-notes.md`
- [ ] Verify all claims against profile facts before drafting final documents
- [ ] Submit manually through the employer's application flow
- [ ] Record application status after submission

## Tracking

- Source URL: {job.get("source_url", "")}
- Resume version:
- Cover letter version:
- Submission status: not submitted
- Follow-up reminder:
"""
    path.write_text(content, encoding="utf-8")


def _split_requirement_like_items(items: list[str]) -> tuple[list[str], list[str]]:
    requirements: list[str] = []
    skills: list[str] = []
    for item in items:
        if _is_requirement_like_phrase(item):
            requirements.append(item)
        else:
            skills.append(item)
    return requirements, skills


def _fallback_cover_letter_text(
    job: dict[str, Any],
    fit: dict[str, Any],
    profile_context: str,
    candidate_name: str,
) -> str:
    title = str(job.get("title") or "the role").strip() or "the role"
    company = str(job.get("company") or "your company").strip() or "your company"

    strengths = _supported_strengths_from_fit(fit, profile_context)

    if strengths:
        strengths_text = ", ".join(strengths[:-1]) + (f", and {strengths[-1]}" if len(strengths) > 1 else strengths[0])
        opening_strengths = f"My background in {strengths_text} aligns well with the role's focus on supporting business-critical application services."
    else:
        opening_strengths = (
            "My background in enterprise application development and maintainable internal software "
            "aligns well with the role's focus on supporting business-critical application services."
        )

    ramp_sentence = ""
    missing_raw = fit.get("missing_skills")
    missing_skills = [str(item).strip() for item in missing_raw] if isinstance(missing_raw, list) else []
    requirement_like, _ = _split_requirement_like_items(missing_skills)
    requirement_text = " ".join(requirement_like).lower()
    if any(token in requirement_text for token in ("microsoft 365", "azure", "power platform", "identity", "access")):
            ramp_sentence = (
                " I would bring a grounded engineering approach, careful attention to maintainability, "
                f"and a willingness to ramp into {company}'s Microsoft platform environment where needed."
            )

    signoff = "Best regards,"
    if candidate_name:
        signoff += f"\n\n{candidate_name}"

    return (
        "Dear Hiring Manager,\n\n"
        + f"I am excited to apply for the {title} position at {company}. {opening_strengths}\n\n"
        + "In my recent development work, I have contributed to internal and enterprise-grade systems by implementing features, "
        + "writing unit tests, improving workflow behavior, and collaborating through pull-request-based development. "
        + "My experience includes application work in university IT, benefits/insurance software, and business-critical workflows.\n\n"
        + f"I am especially interested in {company}'s application services work because it combines software development, stakeholder support, and operational problem-solving."
        + ramp_sentence
        + "\n\n"
        + "Thank you for your time and consideration. I would welcome the opportunity to discuss how my application development experience can support your team.\n\n"
        + signoff
    )


def _extract_candidate_name(profile_context: str) -> str:
    match = re.search(r"(?im)^\s*(?:-\s*)?(?:\*\*)?name(?:\*\*)?\s*:\s*([A-Za-z][A-Za-z .'-]{2,})\s*$", profile_context)
    if not match:
        return ""
    return match.group(1).strip()


def _is_requirement_like_phrase(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in REQUIREMENT_LIKE_MARKERS)


def _supported_strengths_from_fit(fit: dict[str, Any], profile_context: str) -> list[str]:
    matched_raw = fit.get("matched_skills")
    matched = [str(item).strip() for item in matched_raw] if isinstance(matched_raw, list) else []
    filtered = [item for item in matched if item and not _is_requirement_like_phrase(item)]

    profile_lower = profile_context.lower()
    verified = [item for item in filtered if item.lower() in profile_lower]
    if verified:
        return verified[:4]

    defaults = [
        "C#",
        ".NET Core",
        "SQL",
        "enterprise application development",
    ]
    return [item for item in defaults if item.lower() in profile_lower][:4]


def _validate_cover_letter_output(text: str, profile_context: str) -> list[str]:
    lowered = text.lower()
    errors: list[str] = []

    for blocked in COVER_LETTER_BLOCKLIST:
        if blocked in lowered:
            errors.append(f"blocked phrase present: {blocked}")

    if "certification" in lowered and "certification" not in profile_context.lower():
        errors.append("blocked topic present: certifications are not verified in profile facts")

    if "lacks 2-3 years" in lowered or "lack 2-3 years" in lowered:
        errors.append("blocked claim present: implies candidate lacks general software experience")

    return errors


def generate_cover_letter_draft(
    job_path: Path,
    fit: dict[str, Any],
    provider: ModelProvider,
    repo_root: Path,
    output_dir: Path | None = None,
) -> Path:
    job, load_errors = load_json(job_path)
    if load_errors:
        raise ApplyFromFileError("; ".join(load_errors))
    if not isinstance(job, dict):
        raise ApplyFromFileError("job validation failed: root value must be an object")
    output_dir = output_dir or application_dir_for_job(job, repo_root)
    generated_dir = output_dir / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)

    profile_context = load_profile_context(repo_root)
    candidate_name = _extract_candidate_name(profile_context)

    system_prompt = """You are a careful hiring-application assistant.
Write a polished, grounded cover letter draft in Markdown for the provided role.
Use only supported profile evidence from the candidate profile and fit analysis.
Do not invent experience, dates, companies, awards, or technologies.
Keep the letter concise, professional, and tailored to the job description.
Return only the letter text, without commentary or bullet lists.

Hard safety rules:
- Mention only verified strengths from candidate profile facts.
- Do not include self-disqualifying language.
- Do not say: "I do not meet", "I don't meet", "I lack", "limited exposure", or
    "actively deepening my experience with [missing requirement]".
- Do not include placeholders like [Candidate Name], [Your Name], or [mention ...].
- Do not mention certifications unless explicitly present in profile facts.
- Do not claim or imply the candidate lacks 2-3 years of general software/application development experience.
- Missing skills from fit analysis are internal notes, not final cover-letter prose.
- If Microsoft platform experience is not verified, prefer:
    "I am prepared to ramp into the Microsoft platform environment where needed."
"""

    signature_rule = (
        f"Use this exact signature name: {candidate_name}."
        if candidate_name
        else "If a personal signature name is unavailable from profile facts, end with 'Best regards,' and no name line."
    )

    user_prompt = f"""Candidate profile context:
{profile_context}

Fit analysis summary:
{json.dumps(fit, ensure_ascii=False, indent=2)}

Captured job posting:
{json.dumps(job, ensure_ascii=False, indent=2)}

Write a tailored cover letter draft for this role. Mention the strongest evidence and the most relevant angle, but avoid unsupported claims.
{signature_rule}
"""

    try:
        response = provider.complete(
            ModelRequest(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.2,
                max_tokens=1200,
                response_format="text",
            )
        )

        draft_text = response.text.strip()
        if draft_text.startswith("```"):
            draft_text = draft_text.strip("`\n")
            if draft_text.startswith("markdown"):
                draft_text = draft_text.split("\n", 1)[1]

        validation_errors = _validate_cover_letter_output(draft_text, profile_context)
        if validation_errors:
            draft_text = _fallback_cover_letter_text(job, fit, profile_context, candidate_name).strip()
    except ModelProviderError as exc:
        del exc
        draft_text = _fallback_cover_letter_text(job, fit, profile_context, candidate_name).strip()

    final_errors = _validate_cover_letter_output(draft_text, profile_context)
    if final_errors:
        raise ApplyFromFileError("cover letter output failed validation: " + "; ".join(final_errors))

    draft_path = generated_dir / "cover-letter-draft.md"
    draft_path.write_text(draft_text.strip() + "\n", encoding="utf-8")
    return draft_path


def apply_from_file(job_path: Path, provider: ModelProvider, repo_root: Path) -> Path:
    job = load_valid_job(job_path)
    app_dir = application_dir_for_job(job, repo_root)
    fit = ensure_fit_analysis(job_path, app_dir=app_dir, provider=provider, repo_root=repo_root)

    app_dir.mkdir(parents=True, exist_ok=True)
    normalized_job_path = app_dir / "job.json"
    write_json(normalized_job_path, job)
    write_resume_targeting(app_dir / "resume-targeting.md", job, fit)
    write_cover_letter_notes(app_dir / "cover-letter-notes.md", job, fit)
    write_application_checklist(app_dir / "application-checklist.md", job, fit)

    generated_dir = app_dir / "generated"
    generated_dir.mkdir(exist_ok=True)
    keep = generated_dir / ".gitkeep"
    if not keep.exists():
        keep.write_text("", encoding="utf-8")

    return app_dir
