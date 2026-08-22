# Personal Brand OS - Agent Instructions

## Mission
Build Personal Brand OS, a production-quality Django-based operating system for managing a personal brand across content planning, AI-assisted creation, research, scheduling, publishing, and analytics.

## Core principles
1. Do not build a simple CRUD dashboard.
2. Build modular systems with clear boundaries.
3. AI assists the user, but the user remains in control.
4. Every AI-generated item must remain editable.
5. Never publish AI-generated content without explicit human approval.
6. Never fabricate personal achievements, analytics, engagement metrics, or publishing success.
7. Keep AI provider integrations behind an abstraction.
8. Keep social platform integrations behind adapters.
9. Keep scraping/ingestion separate from AI processing.
10. Keep analytics separate from publishing.
11. Do not build the entire product in one step.
12. Do not mark a feature complete until it is implemented, tested, and verified.

## Stack
- Python
- Django
- Django REST Framework
- PostgreSQL
- Redis
- Celery
- django-environ
- Gunicorn
- Django templates for MVP
- Bootstrap or Tailwind CSS
- pytest or Django TestCase

## Architecture rules
- Use separate Django apps by domain.
- Put business logic in service layers, not views.
- Use reusable services and adapters.
- Use database transactions where appropriate.
- Use Celery for background work.
- Use structured JSON internally for AI agent outputs.
- Store AI outputs and versions.
- Make external integrations replaceable.
- Prefer PostgreSQL full-text search initially, with an architecture that can support vector search.
- Support pgvector when available.

## Security
- Never hardcode secrets.
- Read credentials from environment variables.
- Protect CSRF and sessions.
- Validate uploads and enforce size limits.
- Secure social access tokens.
- Apply permissions to APIs and dashboard actions.
- Never expose provider keys to the frontend.

## Development behavior
Before coding a major feature:
1. Read the relevant specification documents.
2. Inspect the existing implementation.
3. Identify dependencies and affected modules.
4. State the implementation plan.
5. Implement only the requested scope.
6. Run tests.
7. Run migrations where needed.
8. Verify UI/API behavior.
9. Update documentation.
10. Stop before moving to the next major phase unless explicitly asked.

If a requirement is ambiguous and affects architecture or data integrity, ask for clarification rather than guessing.

## Git
- Small logical commits.
- One feature per commit.
- Never commit `.env`, credentials, database files, media files, or virtual environments.
