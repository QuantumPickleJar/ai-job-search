# Task 06 — Local Fit Scoring

## Purpose

Use a local model to analyze a captured job posting and produce a structured fit score before investing time in tailoring documents.

This is the first major productivity feature in the local-first workflow.

## Feature Mapping

This task supports:

- High-throughput job triage
- Free or low-cost first-pass analysis
- Skill matching
- Keyword extraction
- Apply / maybe / skip decisions
- Resume targeting preparation

## Input

The scorer takes:

```text
job_intake/captured_jobs/*.json
profile/resume_facts.md
profile/skills_inventory.md
profile/experience_bullets.md
profile/job_preferences.md
profile/disallowed_claims.md
```

For v1, it may operate with only:

```text
job JSON + a simple candidate profile markdown file
```

## Output

Write:

```text
applications/company-role/fit-analysis.json
```

## Fit Score Shape

```json
{
  "overall_score": 0,
  "recommendation": "apply | maybe | skip",
  "confidence": "low | medium | high",
  "reasons_to_apply": [],
  "risks": [],
  "matched_skills": [],
  "missing_skills": [],
  "resume_keywords_to_include": [],
  "suggested_resume_angle": "",
  "cover_letter_angle": "",
  "questions_to_answer_before_applying": [],
  "do_not_claim": []
}
```

## Scoring Rubric

```text
90-100:
Strong apply. Direct match with .NET, C#, SQL, backend, API, Angular, Docker, or related stack.

75-89:
Apply. Good match with minor gaps.

60-74:
Maybe. Apply if local, entry-level, contract-friendly, recruiter-friendly, or strategically useful.

Below 60:
Skip unless there is a specific strategic reason.
```

## Candidate Match Signals

High-value match signals:

- C#
- .NET / ASP.NET / .NET Core
- Entity Framework
- SQL Server / PostgreSQL / MySQL
- Angular / TypeScript
- Docker
- CI/CD
- Jira / Confluence
- API development
- Backend development
- University IT or enterprise systems
- Agile team experience
- Debugging and environment setup
- Technical documentation

## Prompt Requirements

The local model prompt should instruct the model to:

- Return JSON only.
- Avoid inventing experience.
- Cite which candidate facts support each match.
- Separate required skills from preferred skills.
- Identify missing skills honestly.
- Prefer conservative scoring.
- Recommend skipping bad-fit senior-only roles.

## Local Model Behavior

Expected model:

- `qwen2.5:14b` or `qwen3:14b`

Fallback model:

- `llama3.1:8b`

## Acceptance Criteria

This task is complete when:

- A captured job JSON can be scored locally.
- The scorer writes `fit-analysis.json`.
- The JSON includes score, recommendation, matched skills, missing skills, and resume keywords.
- The output does not invent candidate experience.
- The system works without paid cloud APIs.

## Non-Goals

This task does not include:

- Final resume generation
- Cover letter PDF generation
- Application submission
- Browser extension capture
- Cloud provider support
