import json
import re


def parse_critic_output(raw: str) -> list[dict]:
    """Extract and validate the JSON array of approved sources from the source-critic output.

    Handles common agent output formats: bare JSON, JSON wrapped in markdown
    code blocks (``json ... ```), or JSON with surrounding prose.

    Returns:
        A list of dicts, each requiring keys: 'title', 'url', 'reason'.

    Raises:
        ValueError if no valid JSON array is found or required fields are missing.
    """
    text = raw.strip()

    # Extract from markdown code block if present: ```json ... ```
    block = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if block:
        text = block.group(1).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Source critique output is not valid JSON: {e}") from e

    if not isinstance(data, list):
        raise ValueError(
            f"Source critique output must be a JSON array, got {type(data).__name__}"
        )

    required = {"title", "url", "reason"}
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(
                f"Source critique item {i} must be an object, got {type(item).__name__}"
            )
        missing = required - set(item.keys())
        if missing:
            raise ValueError(
                f"Source critique item {i} missing required fields: {', '.join(sorted(missing))}"
            )

    return data
