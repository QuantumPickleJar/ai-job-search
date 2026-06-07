# LinkedIn Job Clipper

Minimal local-only browser extension for saving the currently open LinkedIn job posting to the local `ai-job-search` intake server.

## What It Does

- Runs only when the user opens the extension popup.
- Captures visible fields from the current LinkedIn job page.
- Shows a preview before saving.
- Sends one JSON object to the configured intake URL (default: `http://localhost:3927/jobs/capture`).
- Stores nothing in browser storage.

Captured fields:

- `source`: `linkedin`
- `source_url`
- `title`
- `company`
- `location`
- `description_text`
- `raw_text`
- `capture_method`: `manual_extension_click`

## What It Does Not Do

- No LinkedIn search automation.
- No search result crawling.
- No infinite scrolling.
- No bulk capture.
- No "next job" automation.
- No Easy Apply automation.
- No recruiter, profile, or contact scraping.
- No automated messaging.
- No login or cookie extraction.
- No AI/model calls.
- No application submission.

## Start The Local Intake Server

From the repository root:

```powershell
python scripts\job_intake_server.py
```

For local use, the server still binds to `127.0.0.1:3927`.
For Pi deployment, run the intake server on `0.0.0.0:3927` and point the extension at your Pi address with `extensions/linkedin-job-clipper/config.js`.

Captured jobs are written to:

```text
job_intake/captured_jobs/
```

## Build Or Package Status

There is no JavaScript build step for this extension. The folder is the source artifact.

- For Chrome, Edge, Firefox development, and Opera development: load the folder directly as an unpacked or temporary extension.
- For Firefox distribution beyond temporary loading: package the extension with the included helper script and sign the resulting `.xpi`.
- For Opera packaging: use Opera's `Pack Extension` flow to create a `.crx` after you have tested the unpacked version.

## Load In Chrome

1. Open `chrome://extensions`.
2. Enable Developer mode.
3. Click **Load unpacked**.
4. Select:

```text
extensions/linkedin-job-clipper/
```

Chrome uses the folder as-is. There is no separate build output.

## Load In Microsoft Edge

1. Open `edge://extensions`.
2. Enable Developer mode.
3. Click **Load unpacked**.
4. Select:

```text
extensions/linkedin-job-clipper/
```

Edge uses the same unpacked folder and does not need a separate manifest.

## Load In Firefox

This repository now includes the Firefox-specific manifest metadata needed for a local MV3 install.

For development or local testing:

1. Open `about:debugging`.
2. Click **This Firefox**.
3. Click **Load Temporary Add-on**.
4. In the file picker, open the manifest file directly:

```text
extensions/linkedin-job-clipper/manifest.json
```

5. Select that file. Do not select the folder itself, because Firefox treats the chosen file as the add-on package.

Important Firefox notes:

- Temporary add-ons are removed when Firefox restarts.
- The extension code now uses `browser` when available and falls back to `chrome`, so the same source folder works across Chromium browsers and Firefox.
- For persistent installation outside developer mode, Firefox requires a packaged and signed add-on.

## Package For Firefox

Firefox does not install this repo folder persistently as an end-user add-on unless it is packaged and signed.

Practical flow:

1. From the repository root, run:

```powershell
python scripts\package_firefox_extension.py
```

   This writes `extensions/linkedin-job-clipper/linkedin-job-clipper.xpi` with the extension contents at the archive root.
2. If you prefer to package manually, zip the contents of `extensions/linkedin-job-clipper/` (not the folder itself) so `manifest.json` is at the archive root, then rename the archive to `.xpi`.
3. Sign the `.xpi` through Mozilla's add-on distribution flow before expecting normal end-user installation.

For local development, the temporary install flow above is the intended path.

## Load In Opera

Opera is Chromium-based, so this extension should use the same source folder with no Opera-specific code changes.

1. Open `opera:extensions`.
2. Enable **Developer Mode**.
3. Click **Load Unpacked Extension**.
4. Select:

```text
extensions/linkedin-job-clipper/
```

## Package For Opera

Once the unpacked extension works in Opera:

1. Open `opera:extensions`.
2. Enable **Developer Mode**.
3. Click **Pack Extension**.
4. Select `extensions/linkedin-job-clipper/`.
5. Opera will generate a `.crx` package in the parent directory.

## Pi Deployment Setup

For a Pi-hosted intake server, generate the Pi config and service files from the repo root:

```powershell
python scripts\setup_pi_job_intake.py --pi-host 192.168.1.50
```

This writes:

- `extensions/linkedin-job-clipper/config.js` — points the clipper at `http://192.168.1.50:3927/jobs/capture`
- `deploy/ai-job-intake.service` — a systemd service definition for auto-starting the intake server on the Pi

Then install the service on the Pi:

```bash
sudo cp deploy/ai-job-intake.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ai-job-intake
```

## Test The Flow

1. Start the local intake server.
2. Open one LinkedIn job posting manually.
3. Click the LinkedIn Job Clipper extension icon.
4. Review the captured title, company, location, description character count, and URL.
5. Click **Save Local Job**.
6. Confirm a JSON file appears in:

```text
job_intake/captured_jobs/
```

## Extraction Heuristics

LinkedIn changes DOM structure often, so `content.js` tries several selector families for each field:

- Top-card job title selectors, then `h1`.
- Top-card company selectors.
- Top-card location/workplace selectors.
- Job description selectors such as `.jobs-description__content`, `.jobs-box__html-content`, and `#job-details`.
- Visible main-page text as a fallback.

If required fields are missing, the popup disables saving and shows which fields were not captured.

## Browser Compatibility Notes

- Chrome and Edge use the current Manifest V3 configuration directly.
- Firefox support depends on the `browser_specific_settings.gecko` manifest block and the browser-agnostic API wrapper in `popup.js` and `content.js`.
- Opera uses the Chromium path and should behave like Chrome for this extension.
- The extension now reads its intake URL from `config.js`, so you can switch between `localhost` and a Pi LAN address without changing the popup code.

## Localhost CORS

The intake server allows extension origins such as:

```text
chrome-extension://...
edge-extension://...
moz-extension://...
```

It does not use a wide-open `*` CORS policy.
