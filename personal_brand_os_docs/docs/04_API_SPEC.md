# API Specification

Base path: `/api/`

## Core endpoints

### Brand
- GET/PUT `/api/brand/`

### Content
- GET/POST `/api/content/`
- GET/PUT/PATCH `/api/content/<id>/`
- POST `/api/content/generate/`
- POST `/api/content/repurpose/`
- POST `/api/content/review/`

### Scripts
- GET/POST `/api/scripts/`
- POST `/api/scripts/generate/`

### Calendar
- GET `/api/calendar/`
- POST `/api/calendar/reschedule/`
- POST `/api/calendar/duplicate/`

### Projects
- GET/POST `/api/projects/`
- GET/PUT/PATCH `/api/projects/<id>/`
- POST `/api/projects/<id>/create-content/`

### News
- GET `/api/news/`
- POST `/api/news/<id>/turn-into-content/`

### Research
- GET/POST `/api/research/`

### Social
- GET `/api/social/`
- POST `/api/social/<platform>/connect/`
- POST `/api/social/<platform>/publish/`
- POST `/api/social/<platform>/schedule/`
- GET `/api/social/<platform>/metrics/`

### Analytics
- GET `/api/analytics/`
- GET `/api/analytics/content/`
- GET `/api/analytics/platform/`

### Agents
- GET `/api/agents/`
- POST `/api/agents/<agent>/run/`

## API rules
- Use DRF serializers.
- Apply authentication and object-level permissions.
- Validate inputs.
- Return structured error responses.
- Long-running AI, scraping, publishing, and analytics jobs should be asynchronous.
- Do not expose provider credentials.
