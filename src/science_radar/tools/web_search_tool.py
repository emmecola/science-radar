import json
import os

import requests
from crewai.tools import tool


@tool("web_search")
def web_search(query: str) -> str:
    """Search the web using Brave Search for context, verification, and supporting sources."""
    if not os.getenv("BRAVE_API_KEY"):
        return json.dumps({"error": "BRAVE_API_KEY environment variable is not set"}, indent=2)

    try:
        response = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={
                "Accept": "application/json",
                "X-Subscription-Token": os.getenv("BRAVE_API_KEY"),
            },
            params={"q": query, "count": 5},
            timeout=30,
        )
        response.raise_for_status()
        results = response.json().get("web", {}).get("results", [])

        return json.dumps(
            [
                {
                    "title": r.get("title"),
                    "snippet": r.get("description"),
                    "url": r.get("url"),
                }
                for r in results
            ],
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": f"Web search failed: {e}"}, indent=2)