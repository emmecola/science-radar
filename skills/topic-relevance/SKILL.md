---
name: topic-relevance
description: Guidelines for deciding whether a source is on-topic,
             given a topic definition provided at runtime.
---

## Purpose

You will receive a list of sources and a topic definition.
Your job is to remove sources that are off-topic.
You are NOT evaluating quality, credibility, or importance — only relevance.

## How to Interpret the Topic

The topic definition is your single source of truth. Apply it neither too literally nor too loosely: keep sources where the topic is a **primary subject**, not merely mentioned in passing.

## Decision Rules

1. **Keep** if the source's main argument or finding directly concerns
   the topic
2. **Keep** if the source provides essential context without which
   the topic cannot be understood (e.g. a regulatory framework directly
   governing the topic)
3. **Discard** if the topic appears only as an example, footnote,
   or passing reference
4. **Discard** if the connection requires more than one inferential step

## Handling Ambiguous Cases

When a source could go either way, apply this tiebreaker in order:
1. Would a domain expert consider this source when researching the topic? → Keep
2. Does the title or abstract foreground the topic? → Keep
3. If still unclear → Discard. Downstream agents can only work with
   what you pass through; false positives cost more than false negatives.

## Output Format

Return a JSON array of approved sources with a brief reason for each.
Never discard without a reason. Never keep without confirming the rule
that justifies it.