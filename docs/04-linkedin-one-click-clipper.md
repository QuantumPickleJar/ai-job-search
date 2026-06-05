# Task 04 — LinkedIn One-Click Clipper

## Purpose

Create a user-triggered browser extension that captures the currently visible LinkedIn job posting and sends it to the local job intake server.

This is intended to support a near hands-free workflow without building a LinkedIn crawler or auto-apply bot.

## Feature Mapping

This task supports:

- Manual one-click LinkedIn capture
- Local job intake
- No mass job scraping
- No automated application submission
- Job posting to local JSON workflow

## Target Browser

Initial target:

- Chromium-based browsers
- Google Chrome
- Microsoft Edge

Firefox support is a future enhancement.

## Extension Structure

```text
extensions/
  linkedin-job-clipper/
    manifest.json
    popup.html
    popup.js
    content.js
```

## User Flow

```text
1. User opens one LinkedIn job posting.
2. User clicks the extension icon.
3. The extension extracts visible job data from the current page DOM.
4. The popup previews extracted fields.
5. User clicks "Save Local Job."
6. Extension sends JSON to http://localhost:3927/jobs/capture.
7. Local intake server saves the posting.
```

## Extracted Fields

```json
{
  "source": "linkedin",
  "source_url": "",
  "captured_at": "",
  "title": "",
  "company": "",
  "location": "",
  "workplace_type": "",
  "employment_type": "",
  "description_text": "",
  "raw_text": "",
  "capture_method": "manual_extension_click"
}
```

## Extension Rules

The extension must:

- Run only after user interaction.
- Capture only the current visible job posting.
- Send data only to localhost.
- Avoid background crawling.
- Avoid reading LinkedIn search result pages in bulk.
- Avoid auto-clicking buttons.
- Avoid applying to jobs.
- Avoid scraping people, recruiters, or profiles.

## Explicit Non-Goals

Do not implement:

- Search result crawling
- Infinite scroll extraction
- “Capture all jobs on page”
- Easy Apply automation
- Auto-fill application forms
- Recruiter/contact extraction
- Profile scraping
- Message automation
- Login/session automation
- Anti-bot bypassing

## DOM Extraction Strategy

Use resilient selectors where possible, but expect LinkedIn’s DOM to change.

The extractor should attempt:

1. Known selectors for title, company, location, and description.
2. Fallback selectors for visible text.
3. A raw text capture as a backup.

If extraction is incomplete, the popup should show a warning and allow the user to copy/paste missing fields manually.

## Localhost Posting

The extension should POST to:

```http
POST http://localhost:3927/jobs/capture
```

The extension should handle:

- Intake server unavailable
- Missing fields
- Network failure
- Duplicate capture
- Invalid response

## Acceptance Criteria

This task is complete when:

- The extension can be loaded unpacked in Chrome/Edge.
- The user can click the extension on a LinkedIn job page.
- A preview of extracted data appears.
- The user can save the posting to the local intake server.
- The local intake server writes a captured job JSON file.
- No automatic crawling or applying behavior exists.

## Non-Goals

This task does not include:

- Fit scoring
- Resume generation
- Cover letter generation
- Provider abstraction
- Batch processing
- Job board search
