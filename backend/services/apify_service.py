from __future__ import annotations

import asyncio
from typing import List

from apify_client import ApifyClient
from config import settings
from utils.logger import get_logger
from tenacity import retry, stop_after_attempt, wait_exponential

logger = get_logger(__name__)

_client: ApifyClient = None


def get_apify_client() -> ApifyClient:
    global _client
    if _client is None:
        _client = ApifyClient(settings.apify_api_token)
    return _client


def _sync_scrape_website(url: str, max_pages: int) -> List[dict]:
    """Blocking Apify website scrape — run via asyncio.to_thread."""
    client = get_apify_client()
    run = client.actor("apify/website-content-crawler").call(
        run_input={
            "startUrls": [{"url": url}],
            "maxCrawlPages": max_pages,
            "crawlerType": "cheerio",  # faster, no JS rendering needed for most sites
        }
    )
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    return items


def _sync_search_google(query: str, max_results: int) -> List[dict]:
    """Blocking Apify Google search — run via asyncio.to_thread."""
    client = get_apify_client()
    run = client.actor("apify/google-search-scraper").call(
        run_input={
            "queries": query,
            "maxPagesPerQuery": 1,
            "resultsPerPage": max_results,
        }
    )
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    return items


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=30))
async def scrape_website(url: str, max_pages: int = 3) -> List[dict]:
    """Async website scrape via Apify Website Content Crawler."""
    logger.info("Starting Apify scrape", url=url)
    items = await asyncio.to_thread(_sync_scrape_website, url, max_pages)
    logger.info("Apify scrape complete", url=url, pages=len(items))
    return items


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=30))
async def search_google(query: str, max_results: int = 10) -> List[dict]:
    """Async Google search via Apify."""
    logger.info("Starting Apify Google search", query=query)
    items = await asyncio.to_thread(_sync_search_google, query, max_results)
    logger.info("Apify search complete", query=query, results=len(items))
    return items
