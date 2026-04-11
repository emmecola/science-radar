#!/usr/bin/env python
import json
import re
import warnings
from datetime import datetime
from pathlib import Path

from science_radar.config import TOPIC, TOPIC_NEWSAPI, TOPIC_SEMANTIC
from science_radar.crew import ScienceRadar
from science_radar.lib import search_news, search_papers

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def _fetch_news() -> str:
    return search_news(TOPIC_NEWSAPI)


def _fetch_papers() -> str:
    return search_papers(TOPIC_SEMANTIC)


def _save_error_report(output_dir: Path, timestamp: str, error_msg: str) -> Path:
    """Save an error report file when the pipeline fails."""
    error_file = output_dir / f"error_{timestamp}.md"
    error_content = f"""# Pipeline Error Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Topic
{TOPIC}

## Error
{error_msg}
"""
    with open(error_file, "w") as f:
        f.write(error_content)
    return error_file


def run_pipeline():
    start_time = datetime.now()
    print(f"SCIENCE RADAR: {TOPIC}")
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Use project root for output directory (src/science_radar/main.py -> project root is 3 levels up)
    project_root = Path(__file__).resolve().parent.parent.parent
    output_dir = project_root / "output"
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    crew = ScienceRadar()

    # Step 1: Scouts (deterministic — direct API calls, no LLM)
    print("\n1. SCOUTING SOURCES...")
    news_results = _fetch_news()
    paper_results = _fetch_papers()

    # Check for API errors before proceeding
    news_data = json.loads(news_results)
    paper_data = json.loads(paper_results)
    errors = []
    if isinstance(news_data, dict) and "error" in news_data:
        errors.append(f"News API failed: {news_data['error']}")
    if isinstance(paper_data, dict) and "error" in paper_data:
        errors.append(f"Paper API failed: {paper_data['error']}")
    if errors:
        error_msg = "; ".join(errors)
        print(f"\nERROR: {error_msg}")
        error_file = _save_error_report(output_dir, timestamp, error_msg)
        print(f"Error report saved to: {error_file}")
        return None, None

    # Step 2: Critique + Curate
    print("\n2. SOURCE CRITIQUE + CURATION...")
    curation_result = crew.critique_crew().kickoff(inputs={
        "topic": TOPIC,
        "news_results": news_results,
        "paper_results": paper_results,
    })

    # Step 3: Write
    print("\n3. WRITING ARTICLE...")
    article = crew.writing_crew().kickoff(inputs={"curation_brief": curation_result.raw})

    # Step 4: Editorial critique
    print("\n4. EDITORIAL CRITIQUE...")
    critique = crew.critique_writing_crew().kickoff(inputs={"article": article.raw})

    # Step 5: Fact check
    print("\n5. FACT CHECK...")
    fact_check = crew.fact_check_crew().kickoff(inputs={
        "article": article.raw,
        "curation_brief": curation_result.raw,
    })

    # Step 6: Revise
    print("\n6. REVISING ARTICLE...")
    revised_article = crew.revision_crew().kickoff(inputs={
        "article": article.raw,
        "editorial_critique": critique.raw,
        "fact_check": fact_check.raw,
    })

    # Step 7: Illustrate
    print("\n7. ILLUSTRATION...")
    illustration = crew.illustrate_crew().kickoff(inputs={"revised_article": revised_article.raw})

    # Save final output
    article_file = output_dir / f"article_{timestamp}.md"
    pipeline_file = output_dir / f"pipeline_{timestamp}.md"

    # Extract illustration URL from illustrator output
    illustration_url = None
    url_match = re.search(r'https?://[^\s\)]+', illustration.raw)
    if url_match:
        illustration_url = url_match.group()

    illustration_md = f"\n![Illustration]({illustration_url})\n" if illustration_url else ""

    with open(article_file, "w") as f:
        f.write(illustration_md + "\n" + revised_article.raw)

    news_count = len(news_data) if isinstance(news_data, list) else 0
    papers_count = len(paper_data) if isinstance(paper_data, list) else 0

    pipeline_content = f"""# Pipeline Report — {datetime.now().strftime('%Y-%m-%d')}

## Topic
{TOPIC}

## Sources Analyzed
- News articles: {news_count}
- Papers: {papers_count}

## Raw News Results
{news_results}

## Raw Paper Results
{paper_results}

## Curation Brief
{curation_result.raw}

## First Draft
{article.raw}

## Editorial Score
{critique.raw}

## Fact Check Status
{fact_check.raw}

## Revised Article
{revised_article.raw}

## Illustration
{illustration.raw}
"""

    with open(pipeline_file, "w") as f:
        f.write(pipeline_content)

    end_time = datetime.now()
    duration = end_time - start_time
    print(f"\nPIPELINE COMPLETE!")
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Ended at:   {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration:   {duration}")
    print(f"Article: {article_file}")
    print(f"Pipeline report: {pipeline_file}")
    return article_file, pipeline_file


if __name__ == "__main__":
    run_pipeline()
