import json
import os
from urllib.parse import quote
import requests
from datetime import datetime, timedelta

from science_radar.config import TOPIC_SEMANTIC, PAPERS_LIMIT, PAPERS_DAYS_LIMIT
from science_radar.lib.api_retry import get_with_retry


def search_papers(query: str = TOPIC_SEMANTIC, days: int = PAPERS_DAYS_LIMIT) -> str:
    """Search recent papers from the last N days on a given topic.

    Note: Semantic Scholar API is rate-limited. Set SEMANTIC_SCHOLAR_API_KEY
    in your .env file for higher rate limits.
    """
    semantic_api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    headers = {}
    if semantic_api_key:
        headers["x-api-key"] = semantic_api_key

    params = {
        "query": query,
        "fields": "title,abstract,url,publicationDate,externalIds",
        "publicationDateOrYear": f"{(datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')}:",
        "sort": "publicationDate:desc",
    }

    try:
        response = get_with_retry(
            "Semantic Scholar",
            "https://api.semanticscholar.org/graph/v1/paper/search/bulk",
            params=params,
            headers=headers,
            timeout=30,
        )
    except requests.exceptions.RetryError:
        return json.dumps(
            {
                "error": (
                    "Paper search failed: Semantic Scholar rate limit exceeded after retries. "
                    "Set SEMANTIC_SCHOLAR_API_KEY for higher limits."
                )
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": f"Paper search failed: {e}"}, indent=2)

    papers = response.json().get("data", [])[:PAPERS_LIMIT]

    return json.dumps(
        [
            {
                "title": p.get("title"),
                "abstract": (p.get("abstract") or "")[:1000],
                "url": (
                    f"https://doi.org/{(p.get('externalIds') or {}).get('DOI')}"
                    if (p.get('externalIds') or {}).get('DOI')
                    else p.get("url")
                ),
                "doi": (p.get("externalIds") or {}).get("DOI"),
            }
            for p in papers
        ],
        indent=2,
    )


def lookup_paper_by_doi(doi_or_url: str) -> str:
    """Fetch metadata + abstract for one paper by DOI (or doi.org URL).

    Returns JSON with title, authors, year, venue, abstract, open-access PDF URL.
    Accepts bare DOIs ("10.xxxx/yyyy") or doi.org URLs.
    """
    semantic_api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    headers = {}
    if semantic_api_key:
        headers["x-api-key"] = semantic_api_key

    if doi_or_url is None:
        return json.dumps({"error": "No DOI provided."}, indent=2)

    raw = doi_or_url.strip()
    lowered = raw.lower()
    if lowered.startswith("https://doi.org/"):
        raw = raw[len("https://doi.org/"):]
    elif lowered.startswith("http://doi.org/"):
        raw = raw[len("http://doi.org/"):]
    elif lowered.startswith("doi.org/"):
        raw = raw[len("doi.org/"):]

    raw = raw.strip()

    if not raw:
        return json.dumps({"error": "Could not extract DOI from input."}, indent=2)
    if not raw.lower().startswith("10."):
        return json.dumps({"error": "Not a DOI URL or bare DOI; use web_search for non-academic pages."}, indent=2)

    encoded = quote(raw, safe="/.+-:()")
    url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{encoded}"
    params = {
        "fields": "title,abstract,year,venue,journal,authors.name,openAccessPdf,externalIds,citationCount,referenceCount",
    }

    try:
        response = get_with_retry(
            "Semantic Scholar",
            url,
            params=params,
            headers=headers,
            timeout=30,
        )
    except requests.exceptions.HTTPError as e:
        status = getattr(getattr(e, "response", None), "status_code", None)
        if status == 404:
            return json.dumps(
                {"error": f"DOI not found in Semantic Scholar: {raw}", "doi": raw},
                indent=2,
            )
        return json.dumps(
            {"error": f"Semantic Scholar lookup failed: HTTP {status}"},
            indent=2,
        )
    except requests.exceptions.RetryError:
        return json.dumps(
            {
                "error": (
                    "Semantic Scholar rate limit exceeded after retries. "
                    "Set SEMANTIC_SCHOLAR_API_KEY for higher limits."
                )
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {"error": f"Semantic Scholar lookup failed: {e}"},
            indent=2,
        )

    data = response.json()
    abstract = data.get("abstract") or ""
    oa = data.get("openAccessPdf") or {}
    external = data.get("externalIds") or {}
    doi = external.get("DOI") or raw
    authors = [
        a.get("name")
        for a in (data.get("authors") or [])
        if a.get("name")
    ]

    return json.dumps(
        {
            "title": data.get("title"),
            "authors": authors,
            "year": data.get("year"),
            "venue": data.get("venue"),
            "journal": ((data.get("journal") or {}).get("name") or data.get("venue")),
            "abstract": abstract if abstract else None,
            "doi": doi,
            "source_url": f"https://doi.org/{doi}",
            "open_access_pdf_url": oa.get("url"),
            "abstract_source": "semantic_scholar" if abstract else "none",
        },
        indent=2,
    )
