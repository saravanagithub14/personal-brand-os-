# Social Platform and Publishing Architecture

## Adapter interface
Create a generic SocialPlatformAdapter.

Methods:
- authenticate()
- get_profile()
- create_post()
- upload_media()
- schedule_post()
- publish_post()
- get_posts()
- get_metrics()

## Platforms
- Instagram
- Facebook
- LinkedIn
- YouTube
- X
- Threads
- Reddit

Each platform gets its own adapter.

## Connection states
- Connected
- Not connected
- Mock mode

Never fake a successful publish.

## Publishing workflow
IDEA
-> RESEARCH
-> AI DRAFT
-> HUMAN EDIT
-> AI REVIEW
-> APPROVED
-> SCHEDULED
-> PUBLISHED
-> ANALYZED

## Approval
Every approval should record who approved, when, what changed, AI version, and content version.

## Scheduling
Publishing should be asynchronous through Celery. Failed jobs must be logged and surfaced to the user.

## Future extensibility
The content system must not know platform-specific API details. Platform adapters translate generic content into provider-specific requests.
