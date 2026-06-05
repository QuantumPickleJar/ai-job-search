# Task 02 — Model Provider Abstraction

## Purpose

Create a model-provider abstraction so cloud-consuming functions can be redirected to local models without rewriting the entire project around one vendor.

This task creates the seam between the application workflow and the LLM backend.

## Feature Mapping

This task supports:

- Converting Claude-consuming functions to local model-consuming functions
- Future OpenAI API compatibility
- Future Anthropic API compatibility
- Ollama local model execution
- Manual fallback workflows
- Lower-cost experimentation

## Design Principle

The application should not call Anthropic, OpenAI, or Ollama directly from workflow code.

Workflow code should call:

```ts
modelProvider.complete(request)
```

Provider-specific code should be isolated behind adapter classes or functions.

## Target Interface

```ts
export interface ModelProvider {
  complete(request: ModelRequest): Promise<ModelResponse>;
}

export interface ModelRequest {
  systemPrompt: string;
  userPrompt: string;
  temperature?: number;
  maxTokens?: number;
  responseFormat?: "text" | "json";
}

export interface ModelResponse {
  text: string;
  raw?: unknown;
}
```

## Provider Targets

Create or plan for:

```text
providers/
  ollama-provider.ts
  openai-provider.ts
  anthropic-provider.ts
  manual-provider.ts
```

Initial implementation priority:

1. `ollama-provider.ts`
2. `manual-provider.ts` if useful
3. `openai-provider.ts` later
4. `anthropic-provider.ts` later

## Ollama Provider Behavior

The Ollama provider should:

- Use `http://localhost:11434/api/chat`
- Read the model name from configuration
- Default to `qwen2.5:14b`
- Support text responses
- Support JSON-requested responses
- Return raw provider output for debugging
- Time out cleanly with a useful error message

## Configuration

Suggested environment variables:

```env
MODEL_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:14b
```

## Error Handling

The provider should produce clear errors for:

- Ollama is not running
- Model is not pulled
- Local endpoint is unreachable
- Response is empty
- JSON parsing failed
- Model output is malformed

## Anti-Pattern to Avoid

Avoid workflow functions like:

```ts
askClaudeToReviewJob()
generateWithAnthropic()
callOpenAIForResume()
```

Prefer:

```ts
modelProvider.complete({
  systemPrompt,
  userPrompt,
  responseFormat: "json"
})
```

## Acceptance Criteria

This task is complete when:

- The repo has a documented provider interface.
- Ollama is identified as the initial provider.
- Workflow code can be designed around a provider abstraction.
- Vendor-specific code can be isolated.
- Later cloud providers can be added without changing every workflow function.

## Non-Goals

This task does not require:

- Full repo migration
- Browser extension work
- Resume PDF generation
- Job board capture
- Claude Code command replacement
- Batch application processing
