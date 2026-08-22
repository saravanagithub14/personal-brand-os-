# Architecture

## High-level architecture

Browser
-> Django templates / future SPA
-> Django REST API
-> Domain services
-> PostgreSQL
-> Redis
-> Celery workers / beat
-> External AI and social adapters

## Django apps

- accounts
- dashboard
- brand
- content
- calendar
- ai_agents
- research
- news
- social
- analytics
- projects
- media
- notifications

## Layering

### Presentation
Views, DRF viewsets, serializers, templates.

### Application/domain services
Business workflows such as ContentGenerationService, CalendarService, PublishingService, KnowledgeRetrievalService, AnalyticsService.

### Integrations
AI providers, social platform adapters, news/RSS/API clients, storage.

### Persistence
Django ORM and PostgreSQL.

### Background processing
Celery + Redis.

## AI flow

User request
-> AgentManager
-> select agent
-> retrieve brand context
-> retrieve relevant knowledge
-> execute agent
-> validate structured output
-> store output/version
-> show user
-> human approval where required

## Social flow

Content
-> platform-specific variant
-> approval
-> SocialPlatformAdapter
-> schedule/publish
-> retrieve metrics
-> analytics storage

## Important boundaries
- AI agents must not directly contain social publishing logic.
- Social adapters must not contain content strategy logic.
- Scrapers should only ingest and normalize source data.
- AI research services should process normalized source data.
- Analytics should consume stored metrics and never invent missing values.
