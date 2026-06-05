# Task 10 — Acceptance Tests

## Purpose

Define practical acceptance tests so the project does not become endless infrastructure work.

These tests decide whether the local-first job-search workflow is actually usable.

## Feature Mapping

This task supports:

- Runtime validation
- Capture validation
- Schema validation
- Fit scoring validation
- Anti-hallucination validation
- Application package validation
- Regression testing

## Test 1 — Runtime

Given Ollama is installed, when a local model is called, then it returns a response from localhost.

Validation:

```powershell
curl http://localhost:11434/api/tags
```

Pass condition:

- The command returns installed models as JSON.

## Test 2 — Local Model Prompt

Given `qwen2.5:14b` is installed, when the validation prompt is sent, then it returns valid or near-valid JSON.

Prompt:

```text
Return JSON only:
{
  "status": "ok",
  "task": "job_search_runtime_test"
}
```

Pass condition:

- The response can be parsed or normalized.

## Test 3 — Capture

Given a LinkedIn job page is open, when the user clicks “Save Local Job,” then a JSON file appears in:

```text
job_intake/captured_jobs/
```

Pass condition:

- File exists.
- Required fields are present.
- Source URL is preserved.
- Description text is not empty.

## Test 4 — Manual Capture Fallback

Given a user pastes a job posting manually, when the intake command runs, then a valid job JSON file is created.

Pass condition:

- Manual capture works without browser extension.

## Test 5 — Schema Validation

Given a captured job JSON file, when validation runs, then required fields are checked.

Required fields:

- `id`
- `source`
- `source_url`
- `captured_at`
- `title`
- `company`
- `description_text`

Pass condition:

- Valid files pass.
- Invalid files fail with useful messages.

## Test 6 — Fit Scoring

Given a job posting for a .NET Developer role, when local fit scoring runs, then output includes:

- Overall score
- Recommendation
- Matched skills
- Missing skills
- Resume keywords
- Risks
- Suggested resume angle

Pass condition:

- `fit-analysis.json` is written.
- Recommendation is one of `apply`, `maybe`, or `skip`.

## Test 7 — No Hallucinated Claims

Given the profile facts and disallowed claims files, when resume targeting runs, then generated claims must trace back to known facts.

Pass condition:

- No unverifiable seniority, leadership, cloud, or technology claims appear.
- Questionable claims are flagged as questions instead.

## Test 8 — Application Package

Given a captured job, when `apply_from_file` runs, then the output folder contains:

```text
applications/company-role/
  job.json
  fit-analysis.json
  resume-targeting.md
  cover-letter-draft.md
  application-checklist.md
```

Pass condition:

- All files exist.
- Content is specific to the job.
- No final submission is attempted.

## Test 9 — Local-Only Default

Given no OpenAI or Anthropic API keys are configured, when the default workflow runs, then it still works using Ollama.

Pass condition:

- No paid cloud key is required for the fit-scoring path.

## Test 10 — Failure Handling

Given Ollama is stopped, when fit scoring runs, then the system fails clearly.

Pass condition:

- Error message tells the user Ollama is not reachable.
- No empty or misleading output is written.

## Acceptance Criteria

This task is complete when:

- The acceptance tests are documented.
- Each major workflow has a pass/fail condition.
- The minimum useful path is testable.
- Failures produce useful messages.
- The project has a clear definition of “working.”
