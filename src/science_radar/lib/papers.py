import json
import os
import time
from datetime import datetime, timedelta

import requests

from science_radar.config import TOPIC_SEMANTIC, PAPERS_LIMIT, DAYS_LIMIT

_RETRY_DELAYS = [5, 15, 30]  # seconds between retries on 429


def search_papers(query: str = TOPIC_SEMANTIC, days: int = DAYS_LIMIT) -> str:
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

    for attempt, delay in enumerate([0] + _RETRY_DELAYS):
        if delay:
            print(f"Semantic Scholar rate limit hit — retrying in {delay}s (attempt {attempt + 1}/{len(_RETRY_DELAYS) + 1})...")
            time.sleep(delay)
        try:
            response = requests.get(
                "https://api.semanticscholar.org/graph/v1/paper/search/bulk",
                params=params,
                headers=headers,
                timeout=30,
            )
            if response.status_code == 429:
                continue
            response.raise_for_status()
            papers = response.json().get("data", [])[:PAPERS_LIMIT]

            return json.dumps(
                [
                    {
                        "title": p.get("title"),
                        "abstract": (p.get("abstract") or "")[:1000],
                        "url": p.get("url"),
                        "doi": (p.get("externalIds") or {}).get("DOI"),
                    }
                    for p in papers
                ],
                indent=2,
            )
        except Exception as e:
            return json.dumps({"error": f"Paper search failed: {e}"}, indent=2)

    return json.dumps({"error": "Paper search failed: Semantic Scholar rate limit exceeded after retries. Set SEMANTIC_SCHOLAR_API_KEY for higher limits."}, indent=2)