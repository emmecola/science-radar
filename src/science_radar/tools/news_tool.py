from crewai.tools import tool

from science_radar.config import TOPIC_NEWSAPI, NEWS_DAYS_LIMIT
from science_radar.lib.news import search_news as _search_news


@tool("search_news")
def search_news(query: str = TOPIC_NEWSAPI, days: int = NEWS_DAYS_LIMIT) -> str:
    """Search recent news articles from the last N days on a given topic.
    
    Use specific queries related to the topic for best results.
    """
    return _search_news(query, days)
