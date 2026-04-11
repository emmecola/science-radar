---
name: editorial-revision
description: Rubric for scoring a science essay on structure, clarity,
             engagement, and sources, and for producing actionable revision notes.
---

## Purpose

You will receive a science essay. Score it on four dimensions and produce
actionable revision notes. You are NOT rewriting — only evaluating and directing.

## Scoring Dimensions

Score each dimension 1–10. Apply the criteria below strictly and consistently.

### Structure (1–10)
- **9–10**: Clear hook, logical progression, each section earns its place;
  the essay tells a coherent story from opening to close
- **7–8**: Mostly well-organised; one section feels out of place or underdeveloped
- **5–6**: Sections exist but do not build on each other; the reader loses the thread
- **1–4**: No discernible structure; paragraphs could be reordered without loss

### Clarity (1–10)
- **9–10**: Every paragraph has a clear purpose; no jargon without explanation;
  reader never needs to re-read to understand
- **7–8**: Occasional dense passage or undefined term; recoverable without effort
- **5–6**: Structure is confusing or key concepts are unexplained
- **1–4**: Reader cannot follow the argument without prior domain knowledge

### Engagement (1–10)
- **9–10**: Strong hook; varied sentence rhythm; concrete examples throughout;
  reader is carried forward
- **7–8**: Competent but flat in places; hook works but middle sags
- **5–6**: Academic register, passive constructions, no memorable moments
- **1–4**: Dry throughout; no reason for a non-specialist to continue reading

### Sources (1–10)
- **9–10**: Inline links present and correctly attributed; sources are primary
  or high-quality secondary
- **7–8**: Most claims linked; one or two sourcing gaps
- **5–6**: Sparse links; some claims float without attribution
- **1–4**: No inline links or sources are unverifiable

## Output Format

Return a JSON object followed by revision notes:

```json
{
  "structure": <1–10>,
  "clarity": <1–10>,
  "engagement": <1–10>,
  "sources": <1–10>,
  "overall": <average to one decimal>,
  "verdict": "APPROVE" | "REVISE"
}
```

Use `"APPROVE"` only if all four scores are 7 or above.

After the JSON, add a **Revision Notes** section listing specific, actionable
changes ordered by priority. Each note must identify the paragraph or sentence
it refers to. Do not give general advice — point to the exact problem and
state what needs to change.

## Tool Use

Use available web search tools when:
- A source link is missing and you want to confirm whether one exists
- You need to verify that an inline link points to a real, accessible URL

Do NOT search to verify factual claims — that is the fact checker's role.
Do not search to supplement the article's content — your role is evaluation, not enrichment.
