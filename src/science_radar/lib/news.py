import json
import os
import time
from datetime import datetime, timedelta

import requests

from science_radar.config import TOPIC_NEWSAPI, NEWS_LIMIT, DAYS_LIMIT

_RETRY_DELAYS = [5, 15, 30]  # seconds between retries on 429


def search_news(query: str = TOPIC_NEWSAPI, days: int = DAYS_LIMIT) -> str:
    """Search recent news articles from the last N days on a given topic."""
    if not os.getenv("NEWSAPI_KEY"):
        return json.dumps({"error": "NEWSAPI_KEY environment variable is not set"}, indent=2)

    params = {
        "q": query,
        "from": (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"),
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": NEWS_LIMIT,
        "apiKey": os.getenv("NEWSAPI_KEY"),
    }

    for attempt, delay in enumerate([0] + _RETRY_DELAYS):
        if delay:
            print(f"NewsAPI rate limit hit — retrying in {delay}s (attempt {attempt + 1}/{len(_RETRY_DELAYS) + 1})...")
            time.sleep(delay)
        try:
            response = requests.get(
                "https://newsapi.org/v2/everything",
                params=params,
                timeout=30,
            )
            if response.status_code == 429:
                continue
            response.raise_for_status()
            articles = response.json().get("articles", [])[:NEWS_LIMIT]

            return json.dumps(
                [
                    {
                        "title": a.get("title"),
                        "url": a.get("url"),
                        "source": (a.get("source") or {}).get("name"),
                        "summary": a.get("description"),
                    }
                    for a in articles
                ],
                indent=2,
            )
        except Exception as e:
            return json.dumps({"error": f"News search failed: {e}"}, indent=2)

    return json.dumps({"error": "News search failed: NewsAPI rate limit exceeded after retries."}, indent=2)