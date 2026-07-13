![Science Radar logo](science_radar-small.png "Generated with Nano Banana Pro")

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![CrewAI](https://img.shields.io/badge/crewai-1.12.2-orange)
![License](https://img.shields.io/badge/license-MIT-green)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/emmecola/science-radar)

Science Radar is a multi-agent pipeline built with [CrewAI](https://crewai.com) that monitors a scientific topic of your choice, selects the most relevant and novel source from recent news and academic papers, and produces a publication-ready illustrated essay.

## What it does

Each run executes a five-step pipeline:

1. **Scout** — fetches recent news (NewsAPI) and academic papers (Semantic Scholar) for the configured topic.
2. **Critique & curate** — multiple agents score each source for novelty, scientific rigour, and societal impact. An arbiter selects the single best source and produces a curation brief.
3. **Write** — a writer agent drafts a ~700-word essay aimed at an intelligent non-specialist reader.
4. **Review & revise** — the editorial critic and fact-checker audit the article. If either flags issues, the writer incorporates the feedback and the cycle repeats. Up to `MAX_REVISION_LOOPS` revisions are attempted (see [Configuration](#configuration)). The loop ends as soon as both reviewers approve, or when the cap is reached.
5. **Illustrate** — an illustrator agent writes an image prompt and generates a cover illustration via MeliousAI.

Three files may be saved to the `output/` directory:

- `article_<timestamp>.md` — the final illustrated essay, ready to publish. Written when both reviewers approve the article.
- `draft_<timestamp>.md` — written instead of `article_<timestamp>.md` when the revision cap is hit before approval. Treat as human-review-required.
- `pipeline_<timestamp>.md` — a full audit trail with scout data, curation results, first draft, all review cycles and revisions, illustration prompt + URL, environmental impact, and API cost. The status reported in the report is `COMPLETE` when both reviewers approved and `REVIEW_REQUIRED` when the cap was hit.

## Installation

**Requirements:** Python ≥ 3.10, < 3.14 and [uv](https://docs.astral.sh/uv/).

```bash
# Install uv if you don't have it
pip install uv

# Clone the repo and install dependencies
git clone https://codeberg.org/emmecola/science-radar.git
cd science-radar
uv sync
```

## Configuration

Copy `.env.example` to `.env` and fill in the required values:

```bash
cp .env.example .env
```

### API keys

| Variable | Required | Description |
|---|---|---|
| `MELIOUS_API_KEY` | Yes | MeliousAI API key for all LLM agents and image generation |
| `NEWSAPI_KEY` | Yes | NewsAPI key for news scouting |
| `BRAVE_API_KEY` | Yes | Brave Search key for web fact-checking |
| `SEMANTIC_SCHOLAR_API_KEY` | No | Semantic Scholar key (optional, raises rate limits) |

### Models

The pipeline uses five model slots, each tunable independently. For the current defaults shipped in `.env.example`, see that file; the slots are:

| Variable | Role |
|---|---|
| `SCOUT_MODEL` | Source critique |
| `CURATOR_MODEL` | Curation scoring |
| `CRITIC_MODEL` | Editorial critique, fact-check, arbitration |
| `WRITER_MODEL` | Writing |
| `ILLUSTRATION_MODEL` | Illustration prompt writing |
| `MELIOUS_IMAGE_MODEL` | Image generation |

> **Tip:** MeliousAI supports routing flavors via suffixes. Append `:speed` for faster responses (recommended for most agents), `:balanced` for quality (default), or `:eco` for greener routing. See [Melious routing docs](https://melious.ai/docs/concepts/routing).

### Pipeline configuration

Edit [src/science_radar/config.py](src/science_radar/config.py) to change the topic and tune the pipeline:

```python
TOPIC = "your topic description"          # plain-language label used in the essay
TOPIC_NEWSAPI = "your NewsAPI query"      # see https://newsapi.org/docs/endpoints/everything
TOPIC_SEMANTIC = "your Semantic Scholar query"  # see https://api.semanticscholar.org/api-docs/

NEWS_LIMIT = 100            # number of news articles to fetch
PAPERS_LIMIT = 50           # number of papers to fetch
NEWS_DAYS_LIMIT = 7         # look back this many days for news
PAPERS_DAYS_LIMIT = 7       # look back this many days for papers
MAX_REVISION_LOOPS = 5      # max writer revisions after the initial draft
```

## Running

```bash
uv run science_radar
```

Output files are written to `output/` in the project root.

---

*This codebase was developed with AI coding assistants.*