# Task 08 — Document Curation Pack

## Purpose

Create the reusable candidate profile documents that local and cloud models can use to generate grounded, accurate application materials.

This is the anti-hallucination layer for the job-search workflow.

## Feature Mapping

This task supports:

- Setup phase profile creation
- Resume base facts
- Reusable experience bullets
- Skills inventory
- Project inventory
- Cover letter facts
- Disallowed claims
- Voice and style consistency

## Profile Folder Structure

Create:

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

## File Purposes

### `base_profile.md`

A short human-readable summary of the candidate.

Should include:

- Target roles
- Core technology stack
- Work style
- Geographic constraints
- Preferred role types

### `resume_facts.md`

Only verified resume facts.

Should include:

- Employers
- Job titles
- Dates
- Education
- Tools used
- Projects completed
- Quantified achievements only if verified

### `experience_bullets.md`

Reusable bullet bank grouped by employer/project.

Each bullet should be tagged:

```text
Tags: backend, .NET, SQL, documentation, Agile, Docker, Angular, testing
```

### `project_inventory.md`

Reusable project descriptions.

Should include:

- Project name
- Purpose
- Technologies
- Role
- Outcome
- Safe claims
- Claims to avoid

### `skills_inventory.md`

Grouped skills.

Suggested groups:

- Languages
- Frameworks
- Databases
- DevOps/tools
- Documentation/project management
- Embedded/systems
- Soft skills

### `education.md`

Education facts.

Should include:

- Degrees
- Schools
- Graduation dates
- GPA if desired
- Academic projects
- Relevant coursework if useful

### `job_preferences.md`

Role targeting preferences.

Should include:

- Preferred titles
- Acceptable titles
- Avoid titles
- Location constraints
- Remote/hybrid/on-site preference
- Commute radius
- Salary expectations if desired
- Contract/full-time preference

### `disallowed_claims.md`

Claims the model must not make.

Examples:

- Do not claim professional Kubernetes ownership unless verified.
- Do not claim senior-level architecture ownership unless verified.
- Do not claim AWS production deployment unless verified.
- Do not claim team leadership unless verified.
- Do not claim mastery of technologies only lightly used.

### `voice_and_style.md`

Writing preferences.

Should include:

- Concise but human tone
- No exaggerated corporate language
- Avoid fake-sounding enthusiasm
- Prefer grounded technical specificity
- Keep cover letters direct
- Avoid overclaiming

## Grounding Rule

Generated documents should only use facts from the profile folder or the captured job posting.

If a model wants to claim something not in the profile folder, it should flag it as a question instead of writing it as fact.

## Acceptance Criteria

This task is complete when:

- The `profile/` folder exists.
- Each profile document exists.
- Each document has clear instructions/placeholders.
- The model has a known-facts source.
- The model has a disallowed-claims source.
- The workflow can distinguish verified facts from suggested wording.

## Non-Goals

This task does not include:

- Final resume rewrite
- Final cover letter rewrite
- LinkedIn capture
- Model provider implementation
- Application submission
