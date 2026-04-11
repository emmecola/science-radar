from crewai.tools import tool

from science_radar.config import TOPIC_SEMANTIC, DAYS_LIMIT
from science_radar.lib.papers import search_papers as _search_papers


@tool("search_papers")
def search_papers(query: str = TOPIC_SEMANTIC, days: int = DAYS_LIMIT) -> str:
    """Search recent academic papers from the last N days on a given topic.
    
    Use specific queries related to the topic for best results.
    """
    return _search_papers(query, days)
