from pathlib import Path

# Central output directory for all pipeline artifacts
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "output"

# Topic configuration - change TOPIC to switch topics
TOPIC = "GMO and genome editing in agriculture or food sector"

# Search queries for the topic
TOPIC_NEWSAPI = '(GMO OR biotech OR biotechnology OR NGT OR "genome edited" OR "genome-edited" OR CRISPR OR "genome editing" OR "genetically modified" OR "genetically engineered") AND (crop OR crops OR agriculture OR plants OR food OR agrifood)'
TOPIC_SEMANTIC = '(GMO | biotech | NGT | "genome edited" | "genome-edited" | CRISPR | "genome editing" | "genetically modified" | "genetically engineered") + (crop | agriculture | plants | food | agrifood)'

# Search limits
NEWS_LIMIT = 100
PAPERS_LIMIT = 50
NEWS_DAYS_LIMIT = 7
PAPERS_DAYS_LIMIT = 7

# Maximum number of writer revisions after the initial draft
MAX_REVISION_LOOPS = 5
