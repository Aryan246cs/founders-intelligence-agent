from __future__ import annotations

from apify_client import ApifyClient
from config import settings
from utils.logger import get_logger
from tenacity import retry, stop_after_attempt, wait_exponential

logger = get_logger(__name__)

_client = None


def get_apify_client() -> ApifyClient:
    global _client
    if _client is None:
        _client = ApifyClient(settings.apify_api_token)
    return _client


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=30))
async def scrape_website(url: str, max_pages: int = 5) -> list[dict]:
    """Scrape a website using Apify's web scraper actor."""
    client = get_apify_client()
    logger.info("Starting Apify scrape", url=url)

    run = client.actor("apify/web-scraper").call(
        run_input={
            "startUrls": [{"url": url}],
            "maxPagesPerCrawl": max_pages,
            "pageFunction": """
            async function pageFunction(context) {
                const { page, request } = context;
                const title = await page.title();
                const text = await page.evaluate(() => document.body.innerText);
                return { url: request.url, title, text: text.slice(0, 5000) };
            }
        """,
        }
    )

    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    logger.info("Apify scrape complete", url=url, pages=len(items))
    return items


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=30))
async def search_google(query: str, max_results: int = 10) -> list[dict]:
    """Run a Google search via Apify's Google Search Scraper."""
    client = get_apify_client()
    logger.info("Starting Apify Google search", query=query)

    run = client.actor("apify/google-search-scraper").call(
        run_input={
            "queries": query,
            "maxPagesPerQuery": 1,
            "resultsPerPage": max_results,
        }
    )

    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    logger.info("Apify search complete", query=query, results=len(items))
    return items
