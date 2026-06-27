#!/usr/bin/env python
import json
import warnings
from datetime import datetime
from pathlib import Path

from science_radar.config import OUTPUT_DIR, TOPIC, TOPIC_NEWSAPI, TOPIC_SEMANTIC
from science_radar.crew import ScienceRadar
from science_radar.lib import search_news, search_papers
from science_radar.report import flush_report, save_article

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def _fetch_news() -> str:
    return search_news(TOPIC_NEWSAPI)


def _fetch_papers() -> str:
    return search_papers(TOPIC_SEMANTIC)


def run_pipeline():
    start_time = datetime.now()
    print(f"SCIENCE RADAR: {TOPIC}")
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    output_dir = OUTPUT_DIR
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    article_file = output_dir / f"article_{timestamp}.md"
    pipeline_file = output_dir / f"pipeline_{timestamp}.md"

    # Incremental audit-trail accumulator
    sections = {}

    def _flush(status: str) -> None:
        flush_report(pipeline_file, TOPIC, sections, status)

    crew = ScienceRadar()

    try:
        # Step 1: Scouts (deterministic — direct API calls, no LLM)
        print("\n1. SCOUTING SOURCES...")
        news_results = _fetch_news()
        paper_results = _fetch_papers()
        news_data = json.loads(news_results)
        paper_data = json.loads(paper_results)
        errors = []
        if isinstance(news_data, dict) and "error" in news_data:
            errors.append(f"News API failed: {news_data['error']}")
        if isinstance(paper_data, dict) and "error" in paper_data:
            errors.append(f"Paper API failed: {paper_data['error']}")
        if errors:
            raise RuntimeError("; ".join(errors))

        sections["Raw News Results"] = news_results
        sections["Raw Paper Results"] = paper_results
        print("  OK")

        # Step 2: Critique + Curate
        critique_time = datetime.now()
        print("\n2. SOURCE CRITIQUE + CURATION...")
        curation_result = crew.critique_crew().kickoff(inputs={
            "topic": TOPIC,
            "news_results": news_results,
            "paper_results": paper_results,
        })

        _task_labels = [
            "Source Critique",
            "Novelty Curation",
            "Science Curation",
            "Impact Curation",
            "Curation Arbiter (Final)",
        ]
        _curation_intermediates = {
            label: t.raw for label, t in zip(_task_labels, curation_result.tasks_output)
        }
        for label, raw in _curation_intermediates.items():
            sections[label] = raw
        sections["Curation Brief (Arbiter)"] = curation_result.raw
        print("  OK")

        # Step 3: Write
        write_time = datetime.now()
        print("\n3. WRITING ARTICLE...")
        article = crew.writing_crew().kickoff(inputs={"curation_brief": curation_result.raw})
        sections["First Draft"] = article.raw
        print("  OK")

        # Step 4: Editorial critique
        editorial_time = datetime.now()
        print("\n4. EDITORIAL CRITIQUE...")
        critique = crew.critique_writing_crew().kickoff(inputs={"article": article.raw})
        sections["Editorial Score"] = critique.raw
        print("  OK")

        # Step 5: Fact check
        factcheck_time = datetime.now()
        print("\n5. FACT CHECK...")
        fact_check = crew.fact_check_crew().kickoff(inputs={
            "article": article.raw,
            "curation_brief": curation_result.raw,
        })
        sections["Fact Check Status"] = fact_check.raw
        print("  OK")

        # Step 6: Revise
        revise_time = datetime.now()
        print("\n6. REVISING ARTICLE...")
        revised_article = crew.revision_crew().kickoff(inputs={
            "article": article.raw,
            "editorial_critique": critique.raw,
            "fact_check": fact_check.raw,
        })
        sections["Revised Article"] = revised_article.raw
        print("  OK")

        # Step 7: Illustrate (SOFT FAIL)
        illustrate_time = datetime.now()
        print("\n7. ILLUSTRATION...")
        illustration = None
        illustration_path = None
        try:
            illustration = crew.illustrate_crew().kickoff(
                inputs={"revised_article": revised_article.raw}
            )
            sections["Illustration"] = illustration.raw

            # Extract illustration path from output
            try:
                ill_data = json.loads(illustration.raw)
                if isinstance(ill_data, dict) and "image_path" in ill_data:
                    illustration_path = Path(ill_data["image_path"])
            except (json.JSONDecodeError, KeyError, ValueError):
                pass

            print("  OK")
        except Exception as e:
            sections["Illustration"] = f"(SKIPPED) Illustration failed: {e}"
            print(f"  WARNING: {e}")
            print("  Continuing without illustration...")

    except Exception as e:
        print(f"\nPIPELINE FAILED: {e}")
        _flush(f"FAILED: {e}")
        raise

    # Save final outputs
    news_count = len(news_data) if isinstance(news_data, list) else 0
    papers_count = len(paper_data) if isinstance(paper_data, list) else 0
    sections["Sources Analyzed"] = f"- News articles: {news_count}\n- Papers: {papers_count}"

    # Save article with illustration
    save_article(article_file, revised_article.raw, illustration_path)

    # Final report flush (overwrites incremental)
    _flush("COMPLETE")

    end_time = datetime.now()
    duration = end_time - start_time
    print(f"\nPIPELINE COMPLETE!")
    print(f"Started at:      {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Curation at:     {critique_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Writing at:      {write_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Editorial at:    {editorial_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Fact-check at:   {factcheck_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Revision at:     {revise_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Illustration at: {illustrate_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Ended at:        {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration:        {duration}")
    print(f"Article:         {article_file}")
    print(f"Pipeline report: {pipeline_file}")
    return article_file, pipeline_file


if __name__ == "__main__":
    run_pipeline()
