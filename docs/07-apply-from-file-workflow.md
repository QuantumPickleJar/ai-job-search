# Task 07 — Apply From File Workflow

## Purpose

Create a workflow that runs application preparation from a locally captured job JSON file.

This avoids depending on live job portal access and makes LinkedIn/manual captures compatible with the application-generation pipeline.

## Feature Mapping

This task supports:

- Captured LinkedIn job compatibility
- Manual job text compatibility
- Local-first application preparation
- Repeatable output folders
- Future batch processing
- Separation of model suggestions from final documents

## CLI Goal

Example:

```powershell
python apply_from_file.py job_intake/captured_jobs/company-role.json
```

or:

```powershell
python apply_from_file.py --latest
```

Use the project’s existing language and CLI style if it already has one.

## Internal Flow

```text
1. Load captured job JSON.
2. Validate schema.
3. Create application output folder.
4. Run local fit scoring if not already done.
5. Generate resume targeting notes.
6. Generate cover letter notes or rough draft.
7. Generate application checklist.
8. Save outputs for human review.
```

## Output Folder

```text
applications/
  company-role/
    job.json
    fit-analysis.json
    resume-targeting.md
    cover-letter-draft.md
    application-checklist.md
    generated/
      resume.tex
      cover-letter.tex
      resume.pdf
      cover-letter.pdf
```

## Staged Output Rule

Do not let the local model overwrite final resume files directly.

Use this path:

```text
model suggestions → markdown review → LaTeX generation → human review → final PDF
```

## Resume Targeting Notes

`resume-targeting.md` should include:

- Recommended summary angle
- Skills to emphasize
- Experience bullets to reuse
- Experience bullets to avoid
- Keywords from the job posting
- Risks or gaps to handle honestly

## Cover Letter Draft

`cover-letter-draft.md` should include:

- Short draft
- Why this company / role
- Relevant experience
- Honest gap handling if needed
- No unverifiable claims

## Application Checklist

`application-checklist.md` should include:

- Company
- Role
- Source URL
- Application link
- Resume version
- Cover letter version
- Required questions
- Submission status
- Follow-up reminder field

## Acceptance Criteria

This task is complete when:

- A captured job JSON can be passed to the workflow.
- An application folder is created.
- Job JSON is copied into the output folder.
- Fit analysis is present.
- Resume targeting notes are present.
- Cover letter draft or notes are present.
- Application checklist is present.
- No cloud API is required for the default local workflow.

## Non-Goals

This task does not include:

- Browser extension work
- Direct LinkedIn automation
- Easy Apply automation
- Sending applications
- Final human-quality resume guarantee
