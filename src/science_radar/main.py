#!/usr/bin/env python
import json
import warnings
from datetime import datetime
from pathlib import Path

from science_radar.config import OUTPUT_DIR, TOPIC, TOPIC_NEWSAPI, TOPIC_SEMANTIC
from science_radar.crew import ScienceRadar
from science_radar.env_impact import captured_costs, captured_impacts, set_current_step
from science_radar.lib import search_news, search_papers
from science_radar.report import billing_markdown, flush_report, impact_markdown, impact_totals, save_article

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
        set_current_step("Critique + Curate")
        curation_result = crew.critique_crew().kickoff(inputs={
            "topic": TOPIC,
            "news_results": news_results,
            "paper_results": paper_results,
        })

        _curation_intermediates = {
            t.name: t.raw for t in curation_result.tasks_output
        }

        for label, raw in _curation_intermediates.items():
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

        # Step 4: Editorial critique
        editorial_time = datetime.now()
        print("\n4. EDITORIAL CRITIQUE...")
        set_current_step("Editorial Critique")
        critique = crew.critique_writing_crew().kickoff(inputs={"article": article.raw})
        sections["Editorial Score"] = critique.raw
        print("  OK")

        # Step 5: Fact check
        factcheck_time = datetime.now()
        print("\n5. FACT CHECK...")
        set_current_step("Fact Check")
        fact_check = crew.fact_check_crew().kickoff(inputs={
            "article": article.raw,
            "curation_brief": curation_result.raw,
        })
        sections["Fact Check Status"] = fact_check.raw
        print("  OK")

        # Step 6: Revise
        revise_time = datetime.now()
        print("\n6. REVISING ARTICLE...")
        set_current_step("Revise")
        revised_article = crew.revision_crew().kickoff(inputs={
            "article": article.raw,
            "editorial_critique": critique.raw,
            "fact_check": fact_check.raw,
        })
        sections["Revised Article"] = revised_article.raw
        print("  OK")

        # Step 7: Verify revised article
        verify_time = datetime.now()
        print("\n7. VERIFYING REVISED ARTICLE...")
        set_current_step("Verify (editorial)")
        revise_critique = crew.critique_writing_crew().kickoff(inputs={"article": revised_article.raw})
        sections["Revised Article Editorial"] = revise_critique.raw
        set_current_step("Verify (fact-check)")
        revise_fact_check = crew.fact_check_crew().kickoff(inputs={
            "article": revised_article.raw,
            "curation_brief": curation_result.raw,
        })
        sections["Revised Article Fact Check"] = revise_fact_check.raw
        print("  OK")

        # Step 8: Second revision
        second_revise_time = datetime.now()
        print("\n8. SECOND REVISION...")
        set_current_step("Second Revision")
        final_article = crew.revision_crew().kickoff(inputs={
            "article": revised_article.raw,
            "editorial_critique": revise_critique.raw,
            "fact_check": revise_fact_check.raw,
        })
        sections["Second Revision"] = final_article.raw
        print("  OK")

        # Step 9: Illustrate (SOFT FAIL)
        illustrate_time = datetime.now()
        print("\n9. ILLUSTRATION...")
        illustration = None
        illustration_path = None
        illustration_prompt = None
        try:
            set_current_step("Illustrate")
            illustration = crew.illustrate_crew().kickoff(
                inputs={"revised_article": final_article.raw}
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
    save_article(article_file, final_article.raw, illustration_path)

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
    print(f"Verify at:       {verify_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"2nd revision at: {second_revise_time.strftime('%Y-%m-%d %H:%M:%S')}")
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
        print(f"Total pipeline cost: €{total_credits:.2f}")
    else:
        print("API cost: none reported")

    return article_file, pipeline_file


if __name__ == "__main__":
    run_pipeline()
