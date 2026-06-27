import time
import requests


_RETRY_DELAYS = [5, 15, 30]  # seconds between retries on 429


def get_with_retry(label: str, url: str, **kwargs) -> requests.Response:
    """GET request with exponential backoff on 429 rate limit.

    Args:
        label: Human-readable name used in log messages (e.g. "NewsAPI").
        url: The URL to request.
        **kwargs: Additional keyword arguments passed to requests.get().

    Returns:
        A successful requests.Response.

    Raises:
        requests.exceptions.RetryError if all retries are exhausted on 429.
        requests.HTTPError on non-429 HTTP errors.
    """
    for attempt, delay in enumerate([0] + _RETRY_DELAYS):
        if delay:
            print(
                f"{label} rate limit hit — retrying in {delay}s "
                f"(attempt {attempt + 1}/{len(_RETRY_DELAYS) + 1})..."
            )
            time.sleep(delay)
        response = requests.get(url, **kwargs)
        if response.status_code == 429:
            continue
        response.raise_for_status()
        return response

    raise requests.exceptions.RetryError(
        f"{label} rate limit exceeded after retries."
    )
