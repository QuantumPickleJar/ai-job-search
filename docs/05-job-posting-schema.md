# Task 05 — Job Posting Schema

## Purpose

Define the normalized JSON schema used for all captured job postings.

This schema allows LinkedIn captures, manual pastes, and future job-board captures to flow through the same local scoring and application workflow.

## Feature Mapping

This task supports:

- Consistent local processing
- Repeatable fit scoring
- Resume targeting
- Cover letter drafting
- Application tracking
- Job source portability

## Schema Goals

The schema should:

- Preserve the original captured text.
- Normalize common fields.
- Support missing or unknown values.
- Support local model enrichment.
- Avoid requiring live web access after capture.
- Support future application tracking.

## Required Fields

```json
{
  "id": "string",
  "source": "linkedin | indeed | ziprecruiter | manual | other",
  "source_url": "string",
  "captured_at": "ISO-8601 string",
  "title": "string",
  "company": "string",
  "description_text": "string"
}
```

## Full Schema Shape

```json
{
  "id": "string",
  "source": "linkedin | indeed | ziprecruiter | manual | other",
  "source_url": "string",
  "captured_at": "ISO-8601 string",
  "title": "string",
  "company": "string",
  "location": "string",
  "remote_status": "remote | hybrid | onsite | unknown",
  "employment_type": "full-time | part-time | contract | internship | unknown",
  "seniority": "intern | junior | mid | senior | unknown",
  "description_text": "string",
  "raw_text": "string",
  "requirements": ["string"],
  "preferred_qualifications": ["string"],
  "technologies": ["string"],
  "responsibilities": ["string"],
  "compensation": {
    "min": null,
    "max": null,
    "currency": "USD",
    "raw": ""
  },
  "fit_analysis": null,
  "application_status": "captured",
  "capture_method": "manual_extension_click",
  "notes": ""
}
```

## Status Values

Allowed `application_status` values:

```text
captured
scored
maybe
rejected
drafting
ready_to_apply
applied
interviewing
closed
```

## Enrichment Fields

The local model may populate:

- `requirements`
- `preferred_qualifications`
- `technologies`
- `responsibilities`
- `seniority`
- `remote_status`
- `employment_type`
- `fit_analysis`

The original `description_text` should remain unchanged.

## Validation

A schema validation script should confirm:

- Required fields exist.
- `source` is a known string or `other`.
- `captured_at` is parseable.
- `description_text` is not empty.
- `application_status` is valid.
- Compensation fields may be null.

## Example

```json
{
  "id": "2026-06-05_acme_junior_dotnet_developer",
  "source": "linkedin",
  "source_url": "https://www.linkedin.com/jobs/view/example",
  "captured_at": "2026-06-05T15:30:00-05:00",
  "title": "Junior .NET Developer",
  "company": "Acme Corp",
  "location": "Appleton, WI",
  "remote_status": "hybrid",
  "employment_type": "full-time",
  "seniority": "junior",
  "description_text": "Full job description...",
  "raw_text": "Visible page text...",
  "requirements": [],
  "preferred_qualifications": [],
  "technologies": [],
  "responsibilities": [],
  "compensation": {
    "min": null,
    "max": null,
    "currency": "USD",
    "raw": ""
  },
  "fit_analysis": null,
  "application_status": "captured",
  "capture_method": "manual_extension_click",
  "notes": ""
}
```

## Acceptance Criteria

This task is complete when:

- The normalized job schema is documented.
- Required fields are clear.
- Optional fields are clear.
- Status values are defined.
- Example JSON exists.
- Future validation scripts have clear requirements.

## Non-Goals

This task does not include:

- DOM capture implementation
- Intake server implementation
- Fit scoring implementation
- Resume generation
