import json
import os
import requests
from datetime import datetime, timedelta

from science_radar.config import TOPIC_NEWSAPI, NEWS_LIMIT, NEWS_DAYS_LIMIT
from science_radar.lib.api_retry import get_with_retry


def search_news(query: str = TOPIC_NEWSAPI, days: int = NEWS_DAYS_LIMIT) -> str:
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

    try:
        response = get_with_retry(
            "NewsAPI",
            "https://newsapi.org/v2/everything",
            params=params,
            timeout=30,
        )
    except requests.exceptions.RetryError:
        return json.dumps(
            {"error": "News search failed: NewsAPI rate limit exceeded after retries."}, indent=2
        )
    except Exception as e:
        return json.dumps({"error": f"News search failed: {e}"}, indent=2)

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
