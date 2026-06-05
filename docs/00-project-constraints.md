# Task 00 — Project Constraints

## Purpose

Define the operating boundaries for the local-first `ai-job-search` fork before implementation begins.

This document exists to prevent scope creep, accidental Terms-of-Service risk, runaway cloud spending, and unrealistic automation goals.

## Feature Mapping

This task supports:

- Local-first application workflow
- Low-cost or no-additional-cost operation
- Safe-ish LinkedIn job capture boundary
- Human review before submission
- Clear implementation limits for Codex/agent work
- Future provider portability

## Primary Constraints

The project will prioritize:

- Windows 11 compatibility
- Local model execution through Ollama
- NVIDIA RTX 3060 12GB as the baseline GPU
- No paid cloud API requirement for first-pass scoring
- Human-triggered job capture
- Manual final application submission
- Reusable profile/document curation
- Provider abstraction so OpenAI, Anthropic, Ollama, or manual workflows can be swapped later

## LinkedIn Safety Boundary

The project should avoid acting like a LinkedIn crawler or bot.

Allowed target behavior for v1:

- User opens one job posting manually.
- User clicks a browser extension button.
- The extension captures only the currently visible job posting.
- The captured data is saved locally.
- The generated application materials are reviewed manually.
- The user submits applications manually.

Avoid:

- Crawling LinkedIn search results
- Infinite-scroll extraction
- Bulk job collection
- Easy Apply automation
- Recruiter scraping
- Profile scraping
- Applicant scraping
- Auto-DM, auto-connect, or auto-follow behavior
- Logged-in browser automation using cookies or stealth drivers

## Budget Constraint

The initial implementation should not require:

- Claude Pro or Max
- Claude API credits
- OpenAI API credits
- Paid scraping services
- Paid job board APIs
- Additional GPUs
- Hosted cloud infrastructure

Paid model providers may be added later through a provider abstraction, but the v1 path should function without them.

## Technical Constraint

The project should treat local model output as advisory.

Local models may:

- Score fit
- Extract requirements
- Identify keywords
- Draft rough application material
- Suggest resume targeting angles
- Produce checklists

Local models should not:

- Submit applications
- Invent experience
- Overwrite final resume files without review
- Claim unverified skills or achievements
- Decide to apply without user approval

## Data Constraint

All generated claims must trace back to curated profile facts.

The project should maintain:

- Known facts
- Allowed claims
- Disallowed claims
- Skills inventory
- Project inventory
- Experience bullet bank
- Job preferences

## Non-Goals

This project does not aim to:

- Build a LinkedIn bot
- Auto-apply to jobs
- Replace human review
- Maximize application count at the expense of quality
- Scrape job boards at scale
- Hide automation from websites
- Circumvent anti-bot systems

## Acceptance Criteria

This task is complete when the repo contains a constraints document that:

- Clearly states local-first goals
- Clearly states LinkedIn automation limits
- Clearly states budget limits
- Clearly states human-review requirements
- Can be referenced by later implementation prompts
