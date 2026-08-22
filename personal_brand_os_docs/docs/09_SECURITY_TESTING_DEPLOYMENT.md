# Security, Testing, Docker and Deployment

## Security
Implement CSRF protection, secure authentication, permission checks, environment variables, upload validation, upload size limits, safe HTML rendering, API authentication, secure sessions, and encrypted/secure storage for social tokens.

## Testing
Test:
- models
- views
- APIs
- AI services
- agent workflows
- news ingestion
- duplicate detection
- calendar
- permissions
- social adapters
- content workflow

Target at least 80% coverage for core business logic.

## Docker
Create:
- Dockerfile
- docker-compose.yml
- docker-compose.dev.yml

Services:
- web
- db
- redis
- worker
- beat

Expected local command:
`docker compose up`

## Production target
Initial deployment:
Internet -> Caddy/Nginx -> Gunicorn -> Django -> PostgreSQL/Redis/Celery

Prepare the architecture for later migration to AWS RDS, S3, CloudFront, and managed Redis.

## Environment variables
Use `.env` for:
SECRET_KEY
DEBUG
DATABASE_URL
REDIS_URL
OPENAI_API_KEY
ANTHROPIC_API_KEY
GROQ_API_KEY
GOOGLE_API_KEY
NEWS_API_KEY
YOUTUBE_API_KEY
SOCIAL_PLATFORM_KEYS

Never commit `.env`.
