# UI/UX Specification

## Design System & Aesthetic
Organic, tactile **Hand-Drawn Productivity System** replacing generic corporate flat SaaS styles.

- **100% Handwritten Typography**: Global use of Google Fonts (`Patrick Hand`, `Kalam`, `Caveat`) across all headings, body copy, tables, navigation, badges, and form controls.
- **Organic Wobbly Sketchy Shapes**: No perfect geometric shapes or sharp digital rules. Containers, cards, inputs, and buttons use sketchy irregular border radii (`border-radius: 255px 15px 225px 15px/15px 225px 15px 255px`) and staggered organic rotations (`-0.4deg` to `+0.4deg`).
- **Sketchy Divider Lines**: Dashed and hand-ruled borders (`border-bottom: 2px dashed`) for table headers, card headers, and section dividers.

---

## Dual Theme System (Whiteboard & Chalkboard)

### ✏️ Whiteboard Light Mode
- **Surface**: Light whiteboard surface (`#f6f8fb`) with repeating radial dot-grid texture (`24px` grid).
- **Cards**: Glossy white dry-erase cards (`#ffffff`) with vibrant blue marker borders (`#2563eb`) and offset marker drop-shadows.
- **Typography & Accents**: Blue marker handwritten font (`#0052cc`) for headings, primary action buttons, and active menu states.

### 🖍️ Chalkboard Slate Dark Mode
- **Surface**: True matte charcoal slate background (`#202020` / `#1c1c1c`, non-navy) with repeating dual-radial slate grain noise texture (`24px` & `48px`).
- **Chalk Stroke Texture Effect**: Applied `text-shadow: 0 0 1px rgba(255,255,255,0.5), 0 0 2px rgba(255,255,255,0.3)` and `letter-spacing: 0.5px` to simulate dusty chalk stroke edges on all text.
- **Chalk Outlines**: Digital box-shadow glows removed. Cards are defined purely by hand-ruled off-white chalk outlines (`rgba(232, 232, 224, 0.6)`).
- **Desaturated Chalk Pastels (~40% desaturated)**:
  - Daily: Dusty Rose Chalk (`#d9a3a3`)
  - Weekly: Soft Mint Chalk (`#a3d9c4`)
  - Monthly: Soft Lavender Chalk (`#b8a3d9`)
  - Yearly: Soft Gold / Cream Chalk (`#d9caac`)
  - Off-White Chalk Text: `#e8e8e0` (non-glaring off-white meeting WCAG AA contrast).

### Theme Switcher
- **Toggle Switch**: Fixed top navbar button (`🖍️ Chalkboard` ↔ `✏️ Whiteboard`).
- **Smooth Crossfade**: 250ms CSS transition across background, text, border, and card elements.
- **System Preference & Persistence**: Respects OS `prefers-color-scheme` initially, allows manual toggling, and persists selection in `localStorage`.

---

## Sidebar Navigation
- 📊 Dashboard
- 🌐 Public Portfolio (Opens shareable showcase)
- 👤 Brand Strategy
- 📝 Content Bank
- 💡 Ideas Bank
- 🎯 Content Pillars
- 📅 Calendar
- 🚀 Projects Hub
- 🤖 AI Studio (Phase 3)
- 🌐 Social (Phase 4)

---

## Dashboard Layout & Core Sections

### 1. Header Card
- Greeting, Profile Name, Professional Title, and Niche.
- "＋ Create Content" primary marker button.

### 2. Quick Stat Counters
- Ideas Bank Count, Drafts & Editing Count, Scheduled / Approved Count.

### 3. 📋 Brand Execution & Maintenance Schedule (Whiteboard Schedule)
- Hand-drawn tactile routine for personal brand maintenance.
- **4 Color-Coded Category Cards**:
  - **Daily Routines (Dusty Rose / Coral)**: Review daily AI news, engage on niche posts, capture ideas (accompanied by Plant line SVG 🌱).
  - **Weekly Execution (Soft Mint / Teal)**: Generate weekly AI plan, draft 3 posts, repurpose script, run AI content review (accompanied by Coffee cup line SVG ☕).
  - **Monthly Growth (Soft Lavender / Purple)**: Update Knowledge Base & GitHub projects, audit pillar allocation %, refresh positioning statement (accompanied by Spark line SVG ⚡).
  - **Yearly Milestones (Soft Gold / Amber)**: Annual personal brand audit, publish flagship case study, align career roadmap (accompanied by Trophy line SVG 🏆).
- **Interactive Checkboxes**: Wobbly rough loop checkboxes (`border-radius: 48% 52%...`) that fill with checkmark `✓` on click with local storage persistence across reloads.

### 4. 🌐 Public Portfolio Pages & Showcase Hub
- Banner with direct link to `/portfolio/<username>/` and "📋 Copy Link" button.
- Live status cards for Public Brand Page, Projects Hub count, Published Articles count, and External Website URL.

### 5. Recent Content Activity & OS Overview
- Recent Content Activity table with status indicators and last modified dates.
- Operating System Overview card (Active Pillars, Registered Projects, Published Items, Brand Profile status).

---

## Public Portfolio Page (`/portfolio/` & `/portfolio/<username>/`)
- Publicly accessible page (no login required) for personal brand showcasing:
  - **Brand Header**: Name, Professional Title, Bio, Niche, Positioning Statement, and Social links (Website, GitHub, LinkedIn, Twitter/X, YouTube).
  - **Core Expertise & Skills**: Badges for expertise domains and technology stack.
  - **Projects Portfolio Showcase**: Registered software projects with tech stack tags, descriptions, GitHub links, and Live Demo buttons.
  - **Published Content Feed**: Grid of live published articles and posts.

---

## Content Editor & AI Studio Layout
- Left panel: Editor with selected-text transformations.
- Right panel: AI Assistant for content generation, hook improvement, rewriting, expanding, technical/beginner conversions, CTA & hashtag generation, and platform repurposing.
