# Task 01 — Windows Local Runtime

## Purpose

Set up and validate the local AI runtime for the job-search workflow on a Windows 11 workstation using an NVIDIA RTX 3060 12GB GPU.

This task proves that the system can run a local model before any LinkedIn intake, fit scoring, resume generation, or cloud-to-local migration work begins.

## Feature Mapping

This task supports:

- Local model execution
- No paid API requirement for first-pass scoring
- Windows 11 workstation deployment
- RTX 3060 GPU acceleration
- Future Ollama-backed model provider implementation

## Target Environment

- Operating system: Windows 11
- GPU: NVIDIA RTX 3060 12GB
- Runtime: Ollama
- Local API endpoint: `http://localhost:11434`

## Initial Model Targets

Install and test the following models:

```powershell
ollama pull qwen2.5:14b
ollama pull qwen3:14b
ollama pull llama3.1:8b
```

Primary candidates:

- `qwen2.5:14b`
- `qwen3:14b`

Fallback / speed-test candidate:

- `llama3.1:8b`

## Installation Checklist

Install Ollama:

```powershell
winget install Ollama.Ollama
```

Verify Ollama is installed:

```powershell
ollama --version
```

Pull candidate models:

```powershell
ollama pull qwen2.5:14b
ollama pull qwen3:14b
ollama pull llama3.1:8b
```

Confirm the local API endpoint is available:

```powershell
curl http://localhost:11434/api/tags
```

Expected result:

- A JSON response listing installed local models.

## Validation Test

Run the primary test model:

```powershell
ollama run qwen2.5:14b
```

Use this prompt:

```text
Return JSON only:
{
  "status": "ok",
  "task": "job_search_runtime_test"
}
```

## Acceptance Criteria

This task is complete when:

- Ollama is installed on Windows 11.
- At least one local model runs successfully.
- `http://localhost:11434/api/tags` returns a model list.
- The model can respond to a structured prompt.
- The response is valid JSON or close enough that a parser could normalize it.
- No paid cloud API key is required for this validation.

## Non-Goals

This task does not include:

- LinkedIn browser extension work
- Job posting capture
- Resume generation
- Cover letter generation
- Claude-to-local migration
- OpenAI API support
- Anthropic API support
- Full application workflow automation

Those are handled in later task documents.

## Notes

The goal of this task is to establish a working local foundation. Do not start refactoring the job-search project until this runtime test passes.

The first useful project milestone is:

```text
captured job posting → local model fit score → saved analysis file
```

This task only covers the local model runtime needed to make that later milestone possible.
