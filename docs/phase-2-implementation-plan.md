# Phase 2 Implementation Plan

## 1. Current Repository Structure Summary

The repository is currently a Claude Code-centered job application workspace with a small amount of local scripting and several independent TypeScript job-search CLIs.

Top-level structure observed:

- `README.md`, `SETUP.md`, `AGENTS.md`, and `CLAUDE.md` define the user-facing workflow, setup steps, and agent behavior.
- `.claude/commands/` contains the active Claude command workflows:
  - `setup.md`
  - `reset.md`
  - `expand.md`
  - `apply.md`
- `.claude/skills/` contains Claude skill instructions for:
  - job application assistance
  - job scraping
  - upskilling
- `.agents/skills/` contains mirrored or Codex-oriented skills plus working job-board CLI tools.
- `.agents/skills/*-search/cli/` contains independent Bun/TypeScript CLIs for Danish job portals:
  - `jobbank-search`
  - `jobdanmark-search`
  - `jobindex-search`
  - `jobnet-search`
- `salary_lookup.py` is a top-level Python CLI for optional salary benchmarking.
- `tools/convert_salary_excel.py` converts salary data from Excel to JSON for `salary_lookup.py`.
- `cv/main_example.tex` is the moderncv/banking LaTeX CV template.
- `cover_letters/cover.cls` and `cover_letters/OpenFonts/` support custom xelatex cover letters.
- `documents/` is the personal source-material folder used by setup/expand workflows.
- `job_scraper/` and `upskill/` currently contain only `.gitkeep` placeholders.
- `job_search_tracker.csv` exists as a personal application tracking file and is ignored.
- `docs/` currently contains Phase 2 planning documents `01` through `08`.

Important repository state:

- The requested root `docs/00-project-constraints.md`, `docs/09-cloud-to-local-migration.md`, and `docs/10-acceptance-tests.md` are not currently present under root `docs/`.
- Equivalent documents exist under `.agents/codex/` and under `.agents/codex/ai_job_search_local_docs_pack/docs/`, but `.agents/` is ignored by `.gitignore`.
- `docs/` itself is currently untracked according to `git status --short`.

## 2. Main Language and Runtime

There is no single application runtime yet.

Current runtime split:

- Primary workflow runtime: Claude Code command files and skill markdown.
- Top-level local scripts: Python 3.10+.
- Job portal search tools: Bun + TypeScript, each as an independent CLI package.
- Document generation: LaTeX, with `lualatex` for CVs and `xelatex` for cover letters.
- Future local model runtime planned by docs: Ollama on Windows 11, defaulting toward `qwen2.5:14b` or `qwen3:14b`.

There is no root `package.json`, `pyproject.toml`, `requirements.txt`, or shared test configuration at the repo root.

## 3. Recommended Implementation Style

Recommended style: mixed, with a Python-first local application core.

Rationale:

- The repo already has top-level Python scripts for local CLI work.
- The planned Phase 2 local workflows are file-heavy: validate JSON, save captured jobs, create application folders, call a localhost model endpoint, and write markdown artifacts. Python is a good fit for this without forcing a root Node app.
- Windows local execution is a stated goal, and simple Python CLIs are easy to run in PowerShell.
- Existing Bun/TypeScript code should remain in the job-board CLI skill directories.
- The future browser extension naturally belongs in JavaScript or TypeScript, but it should remain isolated under `extensions/linkedin-job-clipper/`.
- Provider prompts should live as markdown files, separate from provider code, so Python or TypeScript callers can reuse the same prompt assets.

Practical rule:

- Use Python for the local job intake server/CLI, schema validation, fit scoring, provider adapters, and apply-from-file workflow.
- Use TypeScript only for existing portal CLIs and the future browser extension.
- Do not convert the repo into a Node/TypeScript monorepo during Phase 2 unless a later requirement makes that clearly worthwhile.

## 4. Exact Files and Directories Recommended for Phase 2

Create these in Phase 2, in roughly this order.

### Planning Docs Cleanup

These should be restored or copied into root `docs/` before implementation so the public planning surface is complete:

```text
docs/00-project-constraints.md
docs/09-cloud-to-local-migration.md
docs/10-acceptance-tests.md
```

### Candidate Profile Grounding

```text
profile/
  base_profile.md
  resume_facts.md
  experience_bullets.md
  project_inventory.md
  skills_inventory.md
  education.md
  job_preferences.md
  disallowed_claims.md
  voice_and_style.md
```

These files should be human-editable markdown and should become the source of truth for local model grounding.

### Local Job Intake Storage

```text
job_intake/
  captured_jobs/
    .gitkeep
  processed_jobs/
    .gitkeep
  rejected_jobs/
    .gitkeep
  examples/
    example_linkedin_job.json
```

### Python Application Package

```text
ai_job_search/
  __init__.py
  config.py
  paths.py
  slugs.py
  json_io.py
  job_schema.py
  intake.py
  fit_scoring.py
  apply_from_file.py
  providers/
    __init__.py
    base.py
    ollama.py
    manual.py
  prompts/
    fit_scoring_system.md
    fit_scoring_user.md
    resume_targeting_system.md
    cover_letter_system.md
```

Keep this package small and boring at first. It should support the minimum useful path before it grows.

### Root CLI Entrypoints

```text
capture_job.py
score_job.py
apply_from_file.py
```

These can be thin wrappers around `ai_job_search.*` modules so users have simple PowerShell commands while implementation remains organized.

### Local Intake Server

If the Python-first path is accepted:

```text
serve_intake.py
```

Initial version can use Python stdlib HTTP handling if dependency-free is important. A later pass can move to FastAPI if the repo accepts dependencies.

### Application Output

```text
applications/
  .gitkeep
```

Generated per-job folders should follow:

```text
applications/company-role/
  job.json
  fit-analysis.json
  resume-targeting.md
  cover-letter-draft.md
  application-checklist.md
  generated/
    .gitkeep
```

### Tests

Start with Python stdlib tests to avoid dependency work:

```text
tests/
  fixtures/
    valid_job.json
    invalid_job_missing_description.json
  test_job_schema.py
  test_slugs.py
  test_fit_scoring_parse.py
  test_apply_from_file_outputs.py
```

If the project later adopts `pytest`, the test files can stay mostly the same.

### Future Browser Extension

Do not create this yet, but reserve this path:

```text
extensions/
  linkedin-job-clipper/
    manifest.json
    popup.html
    popup.js
    content.js
```

## 5. Existing Files That Probably Need Modification Later

Likely later modifications:

- `.gitignore`
  - Add local generated folders such as `applications/*`, captured job files, model raw-output logs, and any local config containing personal data.
  - Consider whether root `docs/` should be tracked while `.agents/` stays ignored.
- `README.md`
  - Add the Phase 2 local-first workflow once it exists.
  - Document `capture_job.py`, `score_job.py`, and `apply_from_file.py`.
- `SETUP.md`
  - Add Ollama setup and local workflow smoke tests.
  - Clarify Python-first local tooling if accepted.
- `AGENTS.md` and `CLAUDE.md`
  - Eventually reference the local profile folder and captured-job workflow.
  - Keep Claude-specific command behavior intact until migration work is deliberate.
- `.claude/commands/apply.md`
  - Later, optionally add an apply-from-file path or point users to the local workflow.
  - Do not edit this during the first implementation pass.
- `.claude/commands/setup.md` and `.claude/commands/expand.md`
  - Later, optionally populate or refresh the new `profile/` grounding files.
- `.claude/skills/job-application-assistant/*`
  - Later, align grounding rules with `profile/`, but avoid doing this before the local workflow exists.
- `cv/main_example.tex`
  - Later, add `needspace` guidance if the local generator starts emitting final CV LaTeX.
- `cover_letters/cover.cls`
  - Probably no change needed unless cover letter generation reveals layout limits.
- Existing `.agents/skills/*-search/cli/` packages
  - Leave untouched unless integrating their output into normalized captured-job JSON.

## 6. Risk List

- Hidden planning-source risk: the most complete planning pack is under `.agents/`, but `.agents/` is ignored. Future collaborators may only see the root `docs/` subset.
- Runtime sprawl risk: Python, Bun/TypeScript, LaTeX, Claude Code, and Ollama can become hard to reason about unless boundaries stay explicit.
- Dependency drift risk: adding FastAPI, Pydantic, pytest, or provider SDKs too early could make setup heavier before the minimum local path proves useful.
- Schema drift risk: LinkedIn capture, manual paste, job-board CLIs, and future imports could produce different field names unless normalized early.
- Local model reliability risk: Ollama models may return malformed JSON, weak reasoning, or overconfident fit scores. Save raw outputs and validate strictly.
- Hallucination risk: generated claims may exceed verified profile facts unless `profile/disallowed_claims.md` and `profile/resume_facts.md` are enforced.
- Privacy risk: captured jobs, application folders, salary data, and profile files may include personal or sensitive data. `.gitignore` needs a deliberate pass.
- LinkedIn boundary risk: the clipper must remain user-triggered and single-posting only. Avoid crawl, bulk capture, Easy Apply automation, and recruiter/profile scraping.
- Windows path risk: generated paths and scripts should be tested from PowerShell and should avoid POSIX-only assumptions.
- LaTeX layout risk: final document generation still requires compile-and-inspect behavior; local model markdown drafts should not be treated as final PDFs.

## 7. Proposed Implementation Order

1. Restore missing root planning docs.
   - Bring `00`, `09`, and `10` into `docs/` so implementation starts from one canonical documentation location.

2. Create local folder skeletons and sample data.
   - Add `profile/`, `job_intake/`, `applications/`, and `tests/fixtures/`.
   - Add a sample captured job JSON.
   - Update `.gitignore` for generated and personal outputs.

3. Define and validate the job posting schema.
   - Implement `ai_job_search/job_schema.py`.
   - Add `tests/test_job_schema.py`.
   - Validate sample good and bad jobs.

4. Implement manual/local job intake.
   - Start with `capture_job.py` for paste/file input.
   - Save predictable JSON under `job_intake/captured_jobs/`.
   - Do not build the browser extension yet.

5. Run the Ollama runtime smoke test outside application logic.
   - Confirm Ollama is installed and at least one model responds.
   - Record expected environment variables but keep provider logic minimal.

6. Implement the model provider abstraction.
   - Add `providers/base.py`, `providers/ollama.py`, and `providers/manual.py`.
   - Keep prompts in markdown files.
   - Include timeout, missing-model, unreachable-endpoint, and malformed-output errors.

7. Implement local fit scoring MVP.
   - Input: one captured job JSON plus profile markdown.
   - Output: `applications/company-role/fit-analysis.json`.
   - Save raw model output for debugging if parsing fails.

8. Implement apply-from-file MVP.
   - Copy job JSON into an application folder.
   - Ensure fit analysis exists.
   - Write `resume-targeting.md`, `cover-letter-draft.md`, and `application-checklist.md`.
   - Keep outputs staged for human review.

9. Add acceptance tests for the minimum useful path.
   - Schema validation.
   - Slug/path generation.
   - Application folder output.
   - Provider failure handling using a fake/manual provider.

10. Build the local intake server.
    - Add localhost-only `POST /jobs/capture`.
    - Reuse the same schema validation and save path as manual intake.

11. Build the LinkedIn one-click clipper.
    - Only after the local server and schema are stable.
    - Keep extraction user-triggered and localhost-only.

12. Perform cloud-to-local migration audit.
    - Search for Claude/OpenAI/Anthropic-specific assumptions.
    - Migrate only the minimum useful path first.
    - Leave full Claude command parity for later.

13. Polish and safety pass.
    - Confirm personal-data ignores.
    - Confirm no automated application behavior.
    - Confirm no model-generated final documents bypass human review.

## 8. Do Not Touch Yet

- Do not modify `.claude/commands/*.md` during the first Phase 2 implementation pass.
- Do not modify Claude-specific skill files yet.
- Do not create `extensions/linkedin-job-clipper/` until local intake server and schema validation work.
- Do not implement OpenAI or Anthropic providers before the Ollama/manual provider path works.
- Do not refactor existing Bun/TypeScript job-board CLIs.
- Do not replace the current `/apply` workflow.
- Do not generate final CV or cover-letter LaTeX from the local model until the staged markdown workflow is working.
- Do not add new dependencies until the dependency-free skeleton and tests prove the direction.
- Do not add auto-apply, Easy Apply automation, bulk LinkedIn scraping, recruiter scraping, or browser-session automation.
