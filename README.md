![Science Radar logo](science_radar-small.png "Generated with Nano Banana Pro")

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![CrewAI](https://img.shields.io/badge/crewai-1.12.2-orange)
![License](https://img.shields.io/badge/license-MIT-green)

Science Radar is a multi-agent pipeline built with built with [CrewAI](https://crewai.com) that monitors a scientific topic of your choice, selects the most relevant and novel source from recent news and academic papers, and produces a publication-ready illustrated essay.

## What it does

Each run executes a fixed seven-step pipeline:

1. **Scout** — fetches recent news (NewsAPI) and academic papers (Semantic Scholar) for the configured topic.
2. **Critique & curate** — multiple agents score each source for novelty, scientific rigour, and societal impact. An arbiter selects the single best source and produces a curation brief.
3. **Write** — a writer agent drafts a ~700-word essay aimed at an intelligent non-specialist reader.
4. **Editorial critique** — an editorial agent reviews the draft for structure, clarity, engagement, and sourcing quality.
5. **Fact-check** — a fact-checker verifies every claim against the curation brief and the web.
6. **Revise** — the writer incorporates all editorial and fact-check feedback into a final draft.
7. **Illustrate** — an illustrator agent writes an image prompt and generates a cover illustration via fal.ai.

Two files are saved to the `output/` directory:

- `article_<timestamp>.md` — the final illustrated essay, ready to publish.
- `pipeline_<timestamp>.md` — a full audit trail with scout data, curation brief, first draft, critique, fact-check, revised article, and illustration prompt + URL.

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
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key for all LLM agents |
| `FAL_KEY` | Yes | fal.ai key for image generation |
| `NEWSAPI_KEY` | Yes | NewsAPI key for news scouting |
| `BRAVE_API_KEY` | Yes | Brave Search key for web fact-checking |
| `SEMANTIC_SCHOLAR_API_KEY` | No | Semantic Scholar key (optional, raises rate limits) |

### Models

The pipeline uses four model slots, each tunable independently:

| Variable | Default | Role |
|---|---|---|
| `SCOUT_MODEL` | `anthropic/claude-haiku-4-5` | Source critique |
| `CRITIC_MODEL` | `anthropic/claude-sonnet-4-6` | Editorial critique, fact-check, arbitration |
| `CURATOR_MODEL` | `anthropic/claude-opus-4-6` | Curation scoring |
| `WRITER_MODEL` | `anthropic/claude-sonnet-4-6` | Writing and illustration |
| `FAL_MODEL` | `fal-ai/flux/dev` | Image generation |

### Topic

Edit [src/science_radar/config.py](src/science_radar/config.py) to change the topic:

```python
TOPIC = "your topic description"          # plain-language label used in the essay
TOPIC_NEWSAPI = "your NewsAPI query"      # see https://newsapi.org/docs/endpoints/everything
TOPIC_SEMANTIC = "your Semantic Scholar query"  # see https://api.semanticscholar.org/api-docs/
```

You can also tune how many sources are fetched and how far back to look:

```python
NEWS_LIMIT = 30    # number of news articles to fetch
PAPERS_LIMIT = 30  # number of papers to fetch
DAYS_LIMIT = 7     # look back this many days
```

## Running

```bash
uv run science_radar
```

Output files are written to `output/` in the project root.

---

*This codebase was developed with AI coding assistants.*
