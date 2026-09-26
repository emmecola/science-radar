---
name: editorial-revision
description: Rubric for scoring a science essay on structure, clarity,
             and engagement, checking hard-rule compliance, and for
             producing actionable revision notes.
---

## Purpose

You will receive a science essay. Score it on three dimensions, check it
against the writer's hard rules, and produce actionable revision notes.
You are NOT rewriting — only evaluating and directing.

Do not assess factual accuracy or source quality. Source verification and
attribution accuracy are handled separately by the fact checker. If you notice
a missing or suspect citation, leave it to the fact checker rather than flagging
it here — recommending a citation you cannot yourself verify forces the writer
to invent one.

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

## Hard-Rule Compliance

Beyond the three dimensions, check the article against the writer's hard
rules. These are mechanical requirements — a violation
is a defect even when the prose otherwise scores well. Check every one:

- The article begins directly with the headline
- The headline is short, punchy and journalistic
- Total length is 680–720 words
- No Markdown dividers (`---` or similar) anywhere in the text
- No headings anywhere in the text

When you find a violation:

- Cap the **structure** score at 6.
- Emit a revision note for every violation and place these notes first in the
  `revision_notes` array. Prefix the `issue` field with `[HARD RULE]` so the
  writer prioritises them.

## Output Format

Return a JSON object matching this structure:

```json
{
  "structure": <1–10>,
  "clarity": <1–10>,
  "engagement": <1–10>,
  "revision_notes": [
    {
      "location": "<paragraph or sentence>",
      "issue": "<specific problem>",
      "required_fix": "<specific change required>"
    }
  ]
}
```

Do not calculate an overall score or verdict. The application derives approval
from the three scores. Include a revision note for every dimension below 7 and
a separate note for every hard-rule violation. Notes must identify the
paragraph or sentence, point to the exact problem, and state what needs to
change. Return no text outside the structured object.

## Tool Use

Use available web search tools when you need to clarify the meaning of 
an obscure term or concept the writer used.

Do NOT search to verify factual claims or to evaluate citations — that is the
fact checker's role. Do not search to supplement the article's content — your
role is evaluation, not enrichment.
