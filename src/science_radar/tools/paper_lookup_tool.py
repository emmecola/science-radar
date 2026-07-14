from crewai.tools import tool

from science_radar.lib.papers import lookup_paper_by_doi as _lookup_paper_by_doi


@tool("get_paper")
def get_paper(doi_or_url: str) -> str:
    """Fetch metadata and abstract for one academic paper by DOI.

    Use this whenever you have a specific paper DOI to verify against the source
    (title, authors, year, venue, abstract, open-access PDF URL when available).
    Accepts a bare DOI ("10.xxxx/yyyy") or a doi.org URL
    ("https://doi.org/10.xxxx/yyyy"). Returns JSON.

    Call this tool ONCE per paper, then audit every claim from that paper
    against the single returned abstract. Do not call it once per claim.

    Do NOT use this tool for news articles, blog posts, government pages,
    or other non-academic URLs — use web_search for those.
    """
    return _lookup_paper_by_doi(doi_or_url)
