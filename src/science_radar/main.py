#!/usr/bin/env python
import json
import warnings
from datetime import datetime
from pathlib import Path

from science_radar.config import MAX_REVISION_LOOPS, OUTPUT_DIR, TOPIC, TOPIC_NEWSAPI, TOPIC_SEMANTIC
from science_radar.crew import ScienceRadar
from science_radar.env_impact import captured_costs, captured_impacts, set_current_step
from science_radar.lib import search_news, search_papers
from science_radar.report import billing_markdown, flush_report, impact_markdown, impact_totals, save_article
from science_radar.reviews import (
    EditorialReview,
    FactCheckReport,
    editorial_approved,
    fact_check_approved,
    parse_review,
)

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
        set_current_step("Critique + Curate")
        curation_result = crew.critique_crew().kickoff(inputs={
            "topic": TOPIC,
            "news_results": news_results,
            "paper_results": paper_results,
        })

        _curation_intermediates = {
            t.name: t.raw for t in curation_result.tasks_output
        }

        # Step 2: Curate
        for label, raw in list(_curation_intermediates.items())[:-1]:
            sections[label] = raw
        sections["Curation Brief (Arbiter)"] = curation_result.raw
        print("  OK")

        # Step 3: Write
        write_time = datetime.now()
        print("\n3. WRITING ARTICLE...")
        set_current_step("Write")
        article = crew.writing_crew().kickoff(inputs={"curation_brief": curation_result.raw})
        sections["First Draft"] = article.raw
        print("  OK")

        # Step 4: Review and revise until both reviewers approve or the cap is reached
        review_time = datetime.now()
        current_article = article.raw
        revision_count = 0
        editorial_ok = False
        facts_ok = False
        stop_reason = "MAX_REVISIONS_REACHED"

        for review_cycle in range(MAX_REVISION_LOOPS + 1):
            print(f"\n4. REVIEW CYCLE {review_cycle}...")

            set_current_step(f"Review {review_cycle} (editorial)")
            critique = crew.critique_writing_crew().kickoff(inputs={"article": current_article})
            editorial_review = parse_review(critique.raw, EditorialReview)
            editorial_ok = editorial_approved(editorial_review)
            sections[f"Review {review_cycle} - Editorial"] = editorial_review.model_dump_json(indent=2)

            set_current_step(f"Review {review_cycle} (fact-check)")
            fact_check = crew.fact_check_crew().kickoff(inputs={
                "article": current_article,
                "curation_brief": curation_result.raw,
            })
            fact_report = parse_review(fact_check.raw, FactCheckReport)
            facts_ok = fact_check_approved(fact_report)
            sections[f"Review {review_cycle} - Fact Check"] = fact_report.model_dump_json(indent=2)

            print(
                f"  Editorial: {'APPROVED' if editorial_ok else 'REVISE'}; "
                f"Fact check: {'APPROVED' if facts_ok else 'REVISE'}"
            )

            if editorial_ok and facts_ok:
                stop_reason = "APPROVED"
                break

            if revision_count >= MAX_REVISION_LOOPS:
                break

            revision_count += 1
            print(f"\n  REVISION {revision_count}...")
            set_current_step(f"Revision {revision_count}")
            revision = crew.revision_crew().kickoff(inputs={
                "article": current_article,
                "curation_brief": curation_result.raw,
                "editorial_critique": (
                    "APPROVED: no editorial changes required."
                    if editorial_ok
                    else editorial_review.model_dump_json()
                ),
                "fact_check": (
                    "APPROVED: no factual changes required."
                    if facts_ok
                    else fact_report.model_dump_json()
                ),
            })
            current_article = revision.raw
            sections[f"Revision {revision_count}"] = current_article
            print("  OK")

        converged = editorial_ok and facts_ok
        if converged:
            article_file = output_dir / f"article_{timestamp}.md"
            status = "COMPLETE"
        else:
            article_file = output_dir / f"draft_{timestamp}.md"
            status = "REVIEW_REQUIRED"

        sections["Revision Outcome"] = (
            f"- Revisions performed: {revision_count}\n"
            f"- Stop reason: {stop_reason}\n"
            f"- Output: {article_file.name}"
        )

        # Step 5: Illustrate (SOFT FAIL)
        illustrate_time = datetime.now()
        print("\n5. ILLUSTRATION...")
        illustration = None
        illustration_path = None
        illustration_prompt = None
        try:
            set_current_step("Illustrate")
            illustration = crew.illustrate_crew().kickoff(
                inputs={"revised_article": current_article}
            )

            # Extract illustration path and prompt from output
            try:
                ill_data = json.loads(illustration.raw)
                if isinstance(ill_data, dict):
                    if "image_path" in ill_data:
                        illustration_path = Path(ill_data["image_path"])
                    if "prompt" in ill_data:
                        illustration_prompt = ill_data["prompt"]
            except (json.JSONDecodeError, KeyError, ValueError):
                pass

            # Build a nicely formatted Illustration section for the pipeline report
            if illustration_prompt:
                sections["Illustration"] = (
                    "**Prompt used for image generation:**\n\n"
                    f"> {illustration_prompt}\n\n"
                    "**Generated Illustration:**\n\n"
                    f"{illustration_path.name if illustration_path else '(unknown path)'}"
                )
            else:
                sections["Illustration"] = illustration.raw

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

    if captured_impacts:
        sections["Environmental Impact"] = impact_markdown(captured_impacts)
        totals = impact_totals(captured_impacts)
    else:
        sections["Environmental Impact"] = "(no environment_impact reported by the API)"

    if captured_costs:
        sections["API Cost"] = billing_markdown(captured_costs)
    else:
        sections["API Cost"] = "(no billing_cost reported by the API)"

    # Save article with illustration
    save_article(article_file, current_article, illustration_path)

    # Final report flush (overwrites incremental)
    _flush(status)

    end_time = datetime.now()
    duration = end_time - start_time
    print(f"\nPIPELINE COMPLETE!")
    print(f"Started at:      {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Curation at:     {critique_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Writing at:      {write_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Review at:       {review_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Revisions:       {revision_count} ({stop_reason})")
    print(f"Status:          {status}")
    print(f"Illustration at: {illustrate_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Ended at:        {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration:        {duration}")
    print(f"Article:         {article_file}")
    print(f"Pipeline report: {pipeline_file}")

    if captured_impacts:
        print(
            f"Total environmental impact: "
            f"{totals['energy_kwh']:.4f} kWh, "
            f"{totals['carbon_g_co2']:.2f} g CO2, "
            f"{totals['water_liters']:.4f} L water"
        )
    else:
        print("Environmental impact: none reported")

    if captured_costs:
        total_credits = sum(float(c["value"].get("credits", 0)) for c in captured_costs)
        print(f"Total API cost: €{total_credits:.2f}")
    else:
        print("API cost: none reported")

    return article_file, pipeline_file


if __name__ == "__main__":
    run_pipeline()
