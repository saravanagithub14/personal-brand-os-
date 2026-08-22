# Research and News System

## Source types
- RSS
- Google News
- Hacker News
- Reddit
- arXiv
- Hugging Face
- Official AI company blogs/announcements
- GitHub trending
- Major AI publications

## Ingestion pipeline
Source scheduler
-> fetch
-> normalize
-> deduplicate
-> persist
-> relevance processing
-> AI analysis
-> content-angle generation

## NewsArticle
Store title, URL, source, summary, published_at, discovered_at, category, tags, relevance_score, processed, and content_hash.

## Duplicate prevention
Normalize URLs where appropriate and calculate content hashes. Use database uniqueness where possible.

## Safety and compliance
Do not scrape aggressively. Prefer official APIs, RSS feeds, and permitted access. Respect robots.txt, rate limits, and terms of service. Do not represent unavailable engagement metrics as real.

## Daily AI Brief
Show top five relevant items, why each matters, brand relevance, and possible content angles. Provide a "Turn into Content" action.

## Trend scoring
Score 0-100 using available signals such as recency, engagement signals when legitimately available, brand relevance, and content saturation. Never claim exact metrics unless an API supplies them.
