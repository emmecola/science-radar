import json
import os
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
                    if (p.get("externalIds") or {}).get("DOI")
                    else p.get("url")
                ),
                "doi": (p.get("externalIds") or {}).get("DOI"),
            }
            for p in papers
        ],
        indent=2,
    )
