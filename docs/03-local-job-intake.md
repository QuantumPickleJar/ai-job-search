# Task 03 — Local Job Intake

## Purpose

Create a local intake path for job postings so the project can process jobs from LinkedIn, manual paste, saved files, or future job board integrations without relying on live web scraping.

## Feature Mapping

This task supports:

- LinkedIn one-click capture
- Manual paste fallback
- Future Indeed/ZipRecruiter/manual capture support
- Local-only job storage
- Repeatable fit scoring
- Apply-from-file workflow

## Folder Structure

Create:

```text
job_intake/
  captured_jobs/
  processed_jobs/
  rejected_jobs/
  examples/
```

## Capture Modes

Supported capture modes:

```text
Mode A: Browser extension sends job JSON to a local server.
Mode B: User pastes job text into a CLI command.
Mode C: User saves Markdown or text manually.
Mode D: Future import from CSV, Huntr export, or Google Sheet.
```

## Local Intake Server

Recommended endpoint:

```http
POST http://localhost:3927/jobs/capture
```

The server should bind to localhost only.

Recommended implementation options:

- Python + FastAPI
- Node + Express

Choose the one that matches the existing repository style.

## Local-Only Rule

The intake server should:

- Listen on `127.0.0.1`
- Avoid public network exposure
- Avoid cloud upload
- Write captured jobs to local disk
- Return the saved file path to the caller

## Captured Job File Naming

Suggested naming format:

```text
YYYY-MM-DD_company_slug_role_slug.json
```

Example:

```text
2026-06-05_acme_corp_junior_dotnet_developer.json
```

## Minimal Request Body

```json
{
  "source": "linkedin",
  "source_url": "https://www.linkedin.com/jobs/view/example",
  "captured_at": "2026-06-05T15:30:00-05:00",
  "title": "Junior .NET Developer",
  "company": "Example Company",
  "location": "Appleton, WI",
  "description_text": "Full job description here...",
  "raw_text": "Raw visible text from the page...",
  "capture_method": "manual_extension_click"
}
```

## Response Body

```json
{
  "status": "saved",
  "job_id": "2026-06-05_acme_corp_junior_dotnet_developer",
  "path": "job_intake/captured_jobs/2026-06-05_acme_corp_junior_dotnet_developer.json"
}
```

## Validation Requirements

The intake server should reject requests that lack:

- `source`
- `source_url`
- `title`
- `company`
- `description_text`

It should allow unknown values for:

- `location`
- `employment_type`
- `remote_status`
- `compensation`

## Acceptance Criteria

This task is complete when:

- The intake folder structure exists.
- A local capture endpoint or CLI intake path is documented.
- Captured job data can be saved as JSON.
- Saved files follow a predictable naming format.
- Invalid captures fail with useful messages.

## Non-Goals

This task does not include:

- LinkedIn DOM extraction
- Local model scoring
- Resume generation
- Cloud provider migration
- Application submission
