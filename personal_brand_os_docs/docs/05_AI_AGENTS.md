# AI Agents

## AgentManager
Central orchestration layer.

Flow:
request -> agent selection -> context retrieval -> execution -> validation -> persistence -> human review

## ContentStrategistAgent
Inputs:
brand profile, content history, analytics, news, trends, projects, pillars.

Outputs:
topic, reason, platform, format, hook, pillar, audience, priority, suggested date.

## ContentIdeaAgent
Generate ideas from brand, projects, news, trends, audience, previous content, and pillars.

## ContentWriterAgent
Generate platform-specific content while respecting brand voice, audience, platform constraints, pillar, and technical depth.

## ScriptWriterAgent
Generate hook, pattern interrupt, introduction, explanation, example, CTA, timestamps, on-screen text, B-roll, visual directions, caption, title, and thumbnail concept.

Support 30 sec, 45 sec, 60 sec, 90 sec, 3 min, 5 min, and 10 min formats.

## RepurposingAgent
Transform one master asset into platform-specific versions. Do not copy the same text across platforms.

## ContentReviewerAgent
Evaluate clarity, hook, factual accuracy, usefulness, originality, brand alignment, platform fit, CTA quality, and hallucination risk. Return score, strengths, weaknesses, improvements, and claims requiring verification. Never auto-approve.

## NewsResearchAgent
Summarize articles, classify topic and technology, explain why they matter, score brand relevance, and generate content angles.

## AnalyticsAgent
Analyze stored metrics to identify best topics, hooks, formats, platforms, weak content, posting patterns, and gaps. Recommendations must be data-backed.

## KnowledgeRetriever
Methods:
- search()
- retrieve_context()
- get_project_context()
- get_brand_context()
- get_content_history()

## AI provider abstraction
Interface methods:
- generate_text()
- generate_structured()
- embed()
- summarize()

Providers:
OpenAI, Anthropic, Google, Groq, Ollama.

The application must not depend directly on a single provider.
