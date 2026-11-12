# Agent instructions

## Scope

Implement only the CheckStock test assignment described in `docs/specification.md`.
Do not add authentication, marketplace integrations, queues, Redis, microservices,
analytics, forecasting or procurement logic from the larger Raketa brief.

## Workflow

1. Read `docs/specification.md`, `docs/architecture.md` and
   `docs/implementation-plan.md` before changing code.
2. Work in small stages and keep the application runnable after each stage.
3. Write or update tests for each business transition before moving on.
4. Show changed files, checks executed and remaining risks after every stage.
5. Do not change an agreed business invariant without documenting the decision.

## Engineering rules

- API routes validate HTTP input and delegate to application services.
- Business transitions belong in services and execute inside one DB transaction.
- Repositories contain persistence queries and row locking; no business decisions.
- Derived quantities (`available`, in-transit totals) have one source of truth.
- All quantities are integer and strictly positive in commands.
- Critical command endpoints require `Idempotency-Key`.
- Never log credentials, complete request bodies or database URLs.
- Use UTC timestamps in persistence and ISO 8601 in API responses.
- Keep the solution appropriate for a one-day prototype.

## Commits

Use Conventional Commits in English: `feat:`, `fix:`, `test:`, `docs:`,
`refactor:`, `chore:`, `build:` or `ci:`.

