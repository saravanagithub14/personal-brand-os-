# Task 004: Social and Analytics

## Goal
Connect the content workflow to social platforms and performance data.

## Implement
- SocialPlatformAdapter
- platform adapters
- mock adapters
- social connection state
- approval-gated publishing
- Celery scheduling
- publishing logs
- analytics metrics
- analytics dashboard
- AnalyticsAgent

## Acceptance criteria
- [ ] Connected/not-connected/mock states are visible
- [ ] Mock publishing never claims real publishing
- [ ] Approval is required before publish
- [ ] Scheduled posts run asynchronously
- [ ] Failed jobs are visible
- [ ] Metrics are sourced from real data only
- [ ] Analytics filters by platform/content/pillar/format/date
- [ ] Recommendations are based on stored metrics
