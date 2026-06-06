# AI Job Search Service

Deployment guide for the Phase 3 local-first job application service.

> **Current status:** The containerized FastAPI service, health endpoints, filesystem-backed APIs, JSON-backed processing queue, and server-rendered web UI are implemented. Docker Compose deployment remains for a later Phase 3 prompt.

## Which README Should I Read?

Use this order:

1. [`README.md`](README.md) - project overview, upstream Claude workflow, and the working Phase 2 local scripts.
2. [`README.ai-job-service.md`](README.ai-job-service.md) - this guide; planned Raspberry Pi service deployment and operation.
3. [`docs/phase-3-service-architecture.md`](docs/phase-3-service-architecture.md) - security boundaries, component responsibilities, networking, and persistence design.
4. [`extensions/linkedin-job-clipper/README.md`](extensions/linkedin-job-clipper/README.md) - optional Chrome/Edge extension installation and single-job capture flow.
5. [`documents/README.md`](documents/README.md) - optional source-document organization for the upstream profile setup workflow.
6. [`tools/README_SALARY_TOOL.md`](tools/README_SALARY_TOOL.md) - optional salary benchmarking tool.
7. [`SETUP.md`](SETUP.md) - detailed setup for the original Claude/Bun/LaTeX workflow; it is not required for the Phase 3 local service MVP.

The root `README.md` remains the general entry point. This service README does not replace it.

## Purpose

The service makes the Phase 2 local-first workflow available through a lightweight web/API application hosted on a Raspberry Pi.

It is intended to:

- accept one manually captured job posting;
- validate and store job data locally;
- request fit scoring from Ollama on a Windows GPU workstation;
- create reviewable application workspaces;
- persist captured and generated data on the Pi; and
- permit authenticated remote access without requiring a paid model API.

The service does not crawl LinkedIn, capture jobs in bulk, automate Easy Apply, scrape people or contacts, send messages, or submit applications.

## Architecture

```text
Remote browser or LinkedIn clipper
                |
                | authenticated HTTPS or private overlay network
                v
Tailscale, Cloudflare Tunnel + Access, or private VPN
                |
                v
Raspberry Pi
Docker Compose: ai-job-service
                |
                | private LAN or tailnet
                v
Windows 11 workstation
Ollama + NVIDIA RTX 3060 12GB
```

The browser communicates with the Pi service. The Pi service calls Ollama through `OLLAMA_BASE_URL`. The browser never calls Ollama directly, and Ollama port `11434` must never be forwarded to the public internet.

See [`docs/phase-3-service-architecture.md`](docs/phase-3-service-architecture.md) for the complete trust-boundary and failure-mode design.

## Requirements

### Raspberry Pi service host

- Raspberry Pi capable of running a supported 64-bit Raspberry Pi OS.
- Reliable local storage for job, profile, and application data.
- Git.
- Docker Engine.
- Docker Compose plugin (`docker compose`).
- Private connectivity to the Windows workstation through LAN, Tailscale, or a private VPN.

Verify Docker on the Pi:

```bash
docker --version
docker compose version
```

### Windows model workstation

- Windows 11.
- NVIDIA RTX 3060 12GB or equivalent supported local inference hardware.
- Ollama.
- At least one installed model, initially `qwen2.5:14b`.
- A private network address reachable from the Pi.
- A Windows Firewall rule restricted to the Pi, trusted LAN subnet, or tailnet.

Install and verify Ollama from PowerShell:

```powershell
winget install Ollama.Ollama
ollama pull qwen2.5:14b
curl.exe http://localhost:11434/api/tags
```

Ollama may need to listen on a private interface so the Pi can reach it. Do not create router port forwarding for `11434`, expose it through Cloudflare Tunnel, or give it a public URL.

### Remote client

- A browser connected through the selected secure access layer.
- Optionally, Chrome or Microsoft Edge with the LinkedIn clipper loaded unpacked.
- Permission to access the protected Pi service.

The remote extension target will need to be configurable in a later Phase 3 prompt. The current Phase 2 extension targets `http://localhost:3927`.

## Prepare the Repository

On the Pi:

```bash
git clone <YOUR_FORK_URL>
cd ai-job-search
```

Create local service configuration from the committed example:

```bash
cp service/.env.example service/.env
```

Never commit `.env`, API keys, tunnel credentials, VPN keys, or Access tokens.

## Environment Configuration

The minimum configuration is:

```env
APP_HOST=0.0.0.0
APP_PORT=3927
APP_DATA_DIR=/app/data
OLLAMA_BASE_URL=http://<PRIVATE_WINDOWS_ADDRESS>:11434
OLLAMA_MODEL=qwen2.5:14b
APP_API_KEY=<GENERATE_A_STRONG_SECRET>
ENABLE_REMOTE_MODE=false
```

| Variable | Purpose |
|---|---|
| `APP_HOST` | Container-internal listen address. `0.0.0.0` does not by itself authorize public access. |
| `APP_PORT` | Internal/default service port. Compose or a reverse proxy may map another host or external port to it. |
| `APP_DATA_DIR` | Container path for mounted persistent data. |
| `OLLAMA_BASE_URL` | Private LAN or tailnet URL for the Windows Ollama instance. |
| `OLLAMA_MODEL` | Installed Ollama model used by the provider. |
| `APP_API_KEY` | Defense-in-depth credential required by mutating endpoints when configured. Store only in local secret configuration. |
| `ENABLE_REMOTE_MODE` | Must remain `false` until authentication, allowed origins, and secure ingress are configured. |

Example private Ollama URLs:

```env
# Private LAN address
OLLAMA_BASE_URL=http://192.168.1.50:11434

# Tailscale address
OLLAMA_BASE_URL=http://100.x.y.z:11434
```

Do not use a public hostname or public IP for `OLLAMA_BASE_URL`.

## Persistent Data

The service container should mount a Pi-owned directory at `/app/data`:

```text
data/
  job_intake/
    captured_jobs/
    processed_jobs/
    rejected_jobs/
  applications/
  tasks/
  profile/
  logs/
```

The intended Compose mapping is:

```yaml
volumes:
  - ./data:/app/data
```

Captured jobs, profile facts, model diagnostics, and generated application workspaces must survive container rebuilds. Back up `data/` separately from the container image.

## Docker Compose Commands

These are the expected commands after the Compose deployment is implemented. The current image can also be built directly from `service/Dockerfile`.

Current direct-image commands:

```bash
docker build -f service/Dockerfile -t ai-job-service .
docker run --rm \
  --env-file service/.env \
  -v "$(pwd)/data:/app/data" \
  -p 3927:3927 \
  ai-job-service
```

Build:

```bash
docker compose build
```

Start or update:

```bash
docker compose up -d --build
```

Inspect service state:

```bash
docker compose ps
```

Follow logs:

```bash
docker compose logs -f ai-job-service
```

Restart:

```bash
docker compose restart ai-job-service
```

Stop containers without deleting mounted data:

```bash
docker compose down
```

Do not add `--volumes` to routine shutdown commands unless you have verified exactly which named volumes would be removed.

## Health Checks

The implemented health endpoints are:

```bash
curl --fail http://localhost:3927/health
curl --fail http://localhost:3927/health/ollama
```

The service health check should report whether the Pi web/API process and mounted storage are usable.

The Ollama health check should call:

```text
${OLLAMA_BASE_URL}/api/tags
```

It should distinguish:

- Windows workstation offline;
- Ollama not running;
- network or firewall failure;
- configured model missing; and
- malformed Ollama response.

`GET /health` returns HTTP 200 with:

```json
{"status": "ok"}
```

`GET /health/ollama` returns HTTP 200 when Ollama is reachable and `OLLAMA_MODEL` is installed. It returns HTTP 503 for an unreachable endpoint, malformed tags response, no installed models, or a missing configured model. Responses do not include `APP_API_KEY` or `OLLAMA_BASE_URL`.

## Web UI

Open the local service dashboard:

```text
http://localhost:3927/ui
```

The server-rendered interface includes:

- dashboard counts and recent processing activity;
- manual job submission;
- captured job search and detail pages;
- queued fit-analysis actions;
- application workspace lists and file review; and
- service and Ollama health status.

The UI does not call Ollama from browser JavaScript. Job processing remains a server-side queued action. When `APP_API_KEY` is configured, mutating forms request it for that submission and do not persist it in browser storage.

## Submit a Job

The implemented capture endpoint is:

```text
POST /jobs/capture
```

Set shell variables rather than placing a real API key directly in copied commands:

```bash
export SERVICE_BASE_URL="http://localhost:3927"
export APP_API_KEY="<YOUR_LOCAL_SECRET>"
```

Submit a placeholder job from the Pi or another authorized client:

```bash
curl --fail-with-body \
  -X POST "${SERVICE_BASE_URL}/jobs/capture" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${APP_API_KEY}" \
  -d '{
    "source": "manual",
    "source_url": "https://example.com/jobs/junior-dotnet-developer",
    "title": "Junior .NET Developer",
    "company": "Example Software Labs",
    "location": "Appleton, WI",
    "description_text": "Placeholder job description for service testing.",
    "raw_text": "Placeholder job description for service testing.",
    "capture_method": "manual"
  }'
```

PowerShell equivalent:

```powershell
$env:SERVICE_BASE_URL = "http://localhost:3927"
$env:APP_API_KEY = "<YOUR_LOCAL_SECRET>"

$body = @{
    source = "manual"
    source_url = "https://example.com/jobs/junior-dotnet-developer"
    title = "Junior .NET Developer"
    company = "Example Software Labs"
    location = "Appleton, WI"
    description_text = "Placeholder job description for service testing."
    raw_text = "Placeholder job description for service testing."
    capture_method = "manual"
} | ConvertTo-Json

Invoke-RestMethod `
    -Method Post `
    -Uri "$env:SERVICE_BASE_URL/jobs/capture" `
    -Headers @{ "X-API-Key" = $env:APP_API_KEY } `
    -ContentType "application/json" `
    -Body $body
```

A successful request returns the normalized job, identifier, and saved path without requiring Ollama to be online. `X-API-Key` is required when `APP_API_KEY` is configured.

## Process a Job

The implemented processing endpoint is:

```text
POST /jobs/<JOB_ID>/process
```

Example:

```bash
export JOB_ID="<JOB_ID_FROM_CAPTURE>"

curl --fail-with-body \
  -X POST "${SERVICE_BASE_URL}/jobs/${JOB_ID}/process" \
  -H "X-API-Key: ${APP_API_KEY}"
```

Model processing creates a persisted task and returns HTTP 202:

```json
{
  "status": "queued",
  "job_id": "<JOB_ID>",
  "task_id": "<TASK_ID>"
}
```

A single background worker runs tasks in order and delegates to the Phase 2 apply-from-file workflow. Task state is stored under `data/tasks/`.

The current queue assumes one service process per mounted `APP_DATA_DIR`. Do not start multiple Uvicorn workers or multiple service containers against the same task directory.

Expected persisted output:

```text
data/applications/<safe-company-role-slug>/
  job.json
  fit-analysis.json
  resume-targeting.md
  cover-letter-notes.md
  application-checklist.md
```

Processing must validate model JSON before writing a valid-looking fit analysis. Malformed output should be retained for diagnosis and reported as a failure.

## Monitor Processing Tasks

```bash
curl --fail "${SERVICE_BASE_URL}/tasks"
curl --fail "${SERVICE_BASE_URL}/tasks/<TASK_ID>"
```

Task states are:

- `queued`
- `running`
- `succeeded`
- `failed`

Tasks left in `queued` state are restored after a service restart. A task interrupted while `running` is marked `failed` because completion cannot be proven safely.

## List Jobs and Applications

Read-only endpoints do not require `X-API-Key` at this stage:

```bash
curl --fail "${SERVICE_BASE_URL}/jobs"
curl --fail "${SERVICE_BASE_URL}/jobs/<JOB_ID>"
curl --fail "${SERVICE_BASE_URL}/applications"
curl --fail "${SERVICE_BASE_URL}/applications/<APPLICATION_ID>"
```

The application detail endpoint returns only the known workspace files. It does not provide arbitrary filesystem access.

## Remote Access Recommendations

### 1. Tailscale private access

Recommended default.

- Join the Pi, Windows workstation, and remote client to the same tailnet.
- Reach the Pi service through its Tailscale address or MagicDNS name.
- Use the Windows Tailscale address for `OLLAMA_BASE_URL` when appropriate.
- Restrict tailnet access with ACLs or grants.
- Do not use Tailscale Funnel by default.

Tailscale usually requires no router port forwarding.

### 2. Cloudflare Tunnel with Access

Use when a browser-friendly HTTPS hostname is needed.

- Publish only the Pi application service through the tunnel.
- Require a Cloudflare Access identity policy.
- Do not configure a bypass route around Access.
- Do not publish Ollama through the tunnel.
- Keep service-level authorization enabled as defense in depth.

Cloudflare Tunnel normally requires no router port forwarding.

### 3. Private VPN

Use an existing WireGuard or other private VPN when preferred.

- Forward only the VPN listener port if router forwarding is required.
- Access the Pi through its VPN address.
- Keep the application service and Ollama off the public network.

### 4. Authenticated TLS reverse proxy

Traditional port forwarding is possible because the external port is deployment-specific.

- Forward an external port such as `443` or `8443` to a TLS-enabled reverse proxy on the Pi.
- Require strong authentication before proxying to the application.
- Add rate limiting, restricted CORS, firewall rules, and service-level authorization.
- Do not forward the service directly until those controls exist.
- Never forward Ollama port `11434`.

An unusual port number alone is not security.

## Troubleshooting

### Docker Compose files do not exist

The service image is implemented, but the Raspberry Pi Compose file remains for a later Phase 3 prompt. Use the direct `docker build` and `docker run` commands above until that deployment file is added.

### Service health endpoint is unreachable

Check:

- `docker compose ps`;
- `docker compose logs ai-job-service`;
- the configured host-port mapping;
- Pi firewall rules;
- whether the selected Tailscale/VPN/tunnel route reaches the Pi; and
- whether authentication is blocking the request.

### Capture works but Ollama health fails

Check:

- the Windows workstation is awake;
- Ollama is running;
- `OLLAMA_BASE_URL` uses a private address reachable from the Pi;
- the Pi can route to that address;
- Windows Firewall permits the Pi or trusted private subnet; and
- the selected model appears in `/api/tags`.

From the Windows workstation:

```powershell
ollama list
curl.exe http://localhost:11434/api/tags
```

From the Pi, using the private Windows address:

```bash
curl --fail http://<PRIVATE_WINDOWS_ADDRESS>:11434/api/tags
```

That Pi-to-Ollama test is private-network verification only. Do not make the URL publicly reachable.

### Configured model is missing

On Windows:

```powershell
ollama pull qwen2.5:14b
```

Or change `OLLAMA_MODEL` to another model already listed by `ollama list`.

### Job submission returns a validation error

Confirm the request uses `Content-Type: application/json` and includes non-empty:

- `source`;
- `source_url`;
- `title`;
- `company`; and
- `description_text`.

### A task stays queued

- Confirm the service process is healthy.
- Check `docker compose logs ai-job-service`.
- Verify only one service process is using the mounted task directory.

### A task fails

- Confirm Ollama is responsive locally on Windows.
- Test with a smaller installed model.
- Review service timeout configuration after it is implemented.
- Inspect `GET /tasks/<TASK_ID>` and verify Ollama connectivity with `/health/ollama`.

### Generated output contains weak or unsupported claims

Review:

- `data/profile/resume_facts.md`;
- `data/profile/disallowed_claims.md`;
- `data/profile/skills_inventory.md`;
- the captured job description; and
- the selected model.

Never solve weak output by adding unsupported candidate claims.

### Files disappear after a rebuild

Confirm the Compose deployment mounts the Pi data directory at `APP_DATA_DIR`. Do not store persistent application data only inside the container writable layer.

## Safety and Human Review

This service accelerates application preparation. It does not make final career decisions or submit applications.

Before using any generated material:

- verify every claim against curated profile facts;
- inspect missing-skill and risk warnings;
- review the job source and company independently;
- edit resume-targeting and cover-letter notes;
- generate and inspect final documents separately; and
- submit the application manually.

Local model output is advisory even when it is valid JSON. Human review is mandatory.

## What Comes Next

The next Phase 3 prompt should add secure remote-access guidance or Raspberry Pi Compose deployment. Remaining work includes:

1. secure remote-access runbooks;
2. Raspberry Pi Docker Compose deployment; and
3. Phase 3 acceptance tests.
