# OpenAI Usage Restrictions & Token Budgeting Policy

This document defines the daily token limits, free tier allowances, and model routing rules for Personal Brand OS.

---

## 📊 Daily Token Allowances

### 1. Flagship Models (High-Tier Quota)
- **Daily Limit**: **250,000 tokens / day**
- **Eligible Models**: `gpt-5.4`, `gpt-5.2`, `gpt-5.1`, `gpt-5`, `gpt-4.1`, `gpt-4o`, `o1`, `o3`.
- **Usage Policy**: Reserved strictly for high-impact strategic tasks:
  - Deep Brand Review & Strategy Audits
  - Complex Multilingual Script Generation
  - Long-form Article Synthesis

### 2. Mini & Nano Models (High-Volume Quota)
- **Daily Limit**: **2,500,000 tokens / day**
- **Eligible Models**: `gpt-5.4-mini`, `gpt-5.4-nano`, `gpt-5-mini`, `gpt-5-nano`, `gpt-4.1-mini`, `gpt-4.1-nano`, `gpt-4o-mini`, `o3-mini`, `o4-mini`.
- **Usage Policy**: Primary default models for high-frequency operations:
  - Content Repurposing (1-click X/IG/LinkedIn drafts)
  - Daily AI News Summaries & Hook Generation
  - Title & Idea Brainstorming
  - Social Handle Metadata Parsing

---

## ⚡ Model Routing & Quota Enforcement Rules

1. **Automatic Fallback Routing**:
   - Default all routine AI agent calls to `gpt-4o-mini` or `gpt-5-mini`.
   - If Flagship daily usage exceeds 200,000 tokens (80% quota), automatically throttle or fall back to mini/nano tier to prevent paid overrun.

2. **Daily Token Tracking**:
   - Log estimated input + output token counts in `AgentExecutionLog`.
   - Track daily accumulated token usage per tier (`FLAGSHIP` vs `MINI_NANO`).

3. **Billing Overrun Prevention**:
   - Any usage beyond 250k (Flagship) or 2.5M (Mini/Nano) per day triggers a warning alert before calling external paid endpoints.
