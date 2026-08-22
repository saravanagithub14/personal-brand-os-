# Requirements

## MVP 1
- Authentication
- Brand profile
- Brand voice
- Content database
- Content pillars
- Content editor
- Content calendar
- Projects
- Basic AI generation
- Main dashboard

## MVP 2
- AI agents
- Script generation
- Repurposing
- Knowledge base
- News scraper
- AI news analysis
- Daily AI brief

## MVP 3
- Social platform connections
- Scheduling
- Publishing
- Analytics

## MVP 4
- Advanced automation
- Vector search
- Advanced analytics
- Agent orchestration
- Trend detection
- Notifications

## Functional requirements

### Brand
Store professional identity, positioning, niche, audience, expertise, skills, tone, writing style, languages, goals, career story, achievements, education, experience, projects, workshops, publications, and social profiles.

### Content
Support ideas, drafts, AI-generated content, editing, approval, scheduling, publishing, and archiving.

Content types include Reel, Carousel, LinkedIn Post, X Post, X Thread, YouTube Video, YouTube Short, Blog, Newsletter, Reddit Post, Story, Facebook Post, and Threads Post.

Statuses:
IDEA -> RESEARCHING -> DRAFT -> AI_GENERATED -> EDITING -> APPROVED -> SCHEDULED -> PUBLISHED -> ARCHIVED

### Content editor
Support hook, body, CTA, hashtags, keywords, references, source URLs, script, caption, visual instructions, and thumbnail idea.

### Calendar
Month, week, day, pipeline, platform, and pillar views. Support rescheduling, duplication, platform conversion, date movement, filtering, and opening the editor.

### AI
Agents include strategist, idea generator, research/news researcher, writer, script writer, repurposer, reviewer, and analytics agent.

### Research/news
Use configurable sources such as RSS feeds, Google News, Hacker News, Reddit, arXiv, Hugging Face, official AI company sources, GitHub trending, and major AI publications. Respect APIs, RSS, robots.txt, rate limits, and terms of service.

### Social
Support an adapter architecture for Instagram, Facebook, LinkedIn, YouTube, X, Threads, and Reddit. Mock adapters are acceptable when credentials or APIs are unavailable, but the UI must clearly say Mock mode.

### Analytics
Track metrics only when supplied by a real source. Never invent analytics.

### Projects
Projects can become sources for content generation. The system should generate project stories, LinkedIn case studies, Reel ideas, X threads, YouTube ideas, and carousel outlines.

### Notifications
Start with in-app notifications. Design for email later.
