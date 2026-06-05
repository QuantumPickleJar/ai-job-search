# Task 09 — Cloud-to-Local Migration

## Purpose

Convert cloud-consuming workflow functions to use the model-provider abstraction, with Ollama as the initial default provider.

This task is where the project shifts from being Claude-centric to provider-portable.

## Feature Mapping

This task supports:

- Replacing Claude-consuming calls
- Replacing OpenAI-consuming calls if present
- Routing model work through local Ollama
- Keeping future cloud support possible
- Avoiding paid API dependency for the default path

## Migration Search Terms

Search the repository for:

```text
claude
anthropic
openai
api_key
apiKey
client.messages
chat.completions
completion
/commands
/skills
model
llm
```

## Migration Strategy

Convert provider-specific calls from this shape:

```ts
const response = await anthropic.messages.create(...)
```

To this shape:

```ts
const response = await modelProvider.complete({
  systemPrompt,
  userPrompt,
  responseFormat: "json"
});
```

## Priority Order

### Priority 1 — Minimum Useful Local Path

```text
captured job → fit score → saved analysis
```

Migrate:

- Job extraction
- Requirement parsing
- Fit scoring
- Keyword matching

### Priority 2 — Application Drafting Support

Migrate:

- Resume targeting notes
- Cover letter drafting
- Application checklist generation

### Priority 3 — Document Generation

Migrate:

- LaTeX resume generation
- LaTeX cover letter generation
- PDF repair loops

### Priority 4 — Extras

Migrate:

- Interview prep
- Application tracking
- Batch processing
- Search/scrape commands

## Important Rule

Do not start by migrating the entire repo.

Start with the smallest end-to-end path:

```text
local job JSON → local fit-analysis.json
```

Then expand.

## Prompt Portability

Prompts should be stored separately from provider code.

Suggested structure:

```text
prompts/
  fit-scoring-system.md
  fit-scoring-user.md
  resume-targeting-system.md
  cover-letter-system.md
```

## JSON Repair

Local models may produce imperfect JSON.

The migration should include:

- JSON-only prompting
- Retry with stricter prompt
- Simple JSON cleanup if needed
- Clear failure messages
- Saved raw output for debugging

## Acceptance Criteria

This task is complete when:

- Core model calls use the provider abstraction.
- Ollama is the default provider.
- The fit scoring workflow works without cloud keys.
- Cloud providers are not required for the default path.
- Provider-specific code is isolated.
- Raw model outputs can be inspected for debugging.

## Non-Goals

This task does not include:

- Building the browser extension
- Installing Ollama
- Curating resume facts
- Auto-applying to jobs
- Full Claude Code feature parity in one pass
