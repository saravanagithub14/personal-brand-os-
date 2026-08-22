# Database Design

## Core entities

### Account
User authentication and profile.

### BrandProfile
Fields:
name, professional_title, short_bio, long_bio, positioning_statement, niche, target_audience, expertise, skills, languages, content_goals, career_story, achievements, education, experience, workshops, publications, portfolio_url and social profile URLs.

### BrandVoice
tone, sentence_length, vocabulary_preferences, words_to_avoid, phrases_to_avoid, preferred_hooks, cta_style, technical_depth, audience_level.

### ContentPillar
name, description, target_audience, preferred_platforms, content_formats, allocation_percentage, active.

### ContentItem
id, title, idea, content_type, platform, pillar, status, priority, scheduled_at, published_at, created_at, updated_at, hook, body, CTA, hashtags, keywords, references, source_urls, script, caption, visual_instructions, thumbnail_idea.

### ContentVersion
content_item, version_number, content_snapshot, created_by, created_at, change_reason.

### ContentApproval
content_item, reviewer, status, notes, approved_at, version reference.

### Project
title, description, problem, solution, technologies, github_url, demo_url, images, category, date, status.

### KnowledgeItem
title, source, content, tags, category, created_at, updated_at, embedding metadata where applicable.

### NewsSource
name, url, source_type, rss_url, category, active.

### NewsArticle
title, url, source, summary, published_at, discovered_at, category, tags, relevance_score, processed, content_hash.

### Trend
topic, keyword, platform, source, velocity, relevance, detected_at.

### MediaAsset
filename, file, type, size, tags, project, content_item, created_at.

### SocialAccount
user, platform, account identifier, connection state, token reference, metadata.

### AnalyticsMetric
platform, content, pillar, format, metric date, followers, views, likes, comments, shares, saves, clicks, engagement_rate, watch_time, reach.

### Notification
user, type, title, body, read state, created_at.

### PromptTemplate
name, agent, system_prompt, user_prompt, version, active, created_at.

## Data integrity
- Use foreign keys and explicit relationships.
- Add unique constraints for external IDs and content hashes where appropriate.
- Add indexes for common filters.
- Store timestamps consistently.
- Use transactions for approval/publishing workflows.
