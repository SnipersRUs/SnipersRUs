#!/usr/bin/env python3
"""
Web Search Module - Free tier web search using DuckDuckGo
Provides Google-like search capabilities for the LLM
"""
import requests
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class WebSearcher:
    """Free web search using DuckDuckGo (no API key needed)"""

    def __init__(self):
        self.base_url = "https://api.duckduckgo.com/"
        self.instant_answer_url = "https://api.duckduckgo.com/"
        self.search_url = "https://html.duckduckgo.com/html/"

    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search the web for information

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of search results with title, snippet, and URL
        """
        try:
            # Use DuckDuckGo instant answer API (free, no key needed)
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            }

            response = requests.get(self.instant_answer_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            results = []

            # Get instant answer if available
            if data.get('AbstractText'):
                results.append({
                    "title": data.get('Heading', 'Instant Answer'),
                    "snippet": data.get('AbstractText', ''),
                    "url": data.get('AbstractURL', ''),
                    "type": "instant_answer"
                })

            # Get related topics
            for topic in data.get('RelatedTopics', [])[:max_results - len(results)]:
                if isinstance(topic, dict) and 'Text' in topic:
                    results.append({
                        "title": topic.get('Text', '').split(' - ')[0] if ' - ' in topic.get('Text', '') else topic.get('Text', ''),
                        "snippet": topic.get('Text', ''),
                        "url": topic.get('FirstURL', ''),
                        "type": "related_topic"
                    })

            # If no results, try HTML scraping (fallback)
            if not results:
                return self._scrape_search(query, max_results)

            return results[:max_results]

        except Exception as e:
            logger.warning(f"Web search error: {e}")
            return self._scrape_search(query, max_results)

    def _scrape_search(self, query: str, max_results: int) -> List[Dict]:
        """Fallback: Simple web scraping (basic implementation)"""
        # For now, return empty - can be enhanced later
        return []

    def format_search_results(self, results: List[Dict], query: str) -> str:
        """Format search results for LLM context"""
        if not results:
            return f"No recent web search results found for '{query}'. Provide general information based on your training data."

        formatted = f"**Recent Web Search Results for '{query}':**\n\n"
        for i, result in enumerate(results[:3], 1):  # Top 3 results
            formatted += f"{i}. **{result.get('title', 'Result')}**\n"
            formatted += f"   {result.get('snippet', '')[:200]}...\n"
            if result.get('url'):
                formatted += f"   Source: {result.get('url')}\n"
            formatted += "\n"

        formatted += "\n**Instructions:** Use this information to provide a comprehensive, helpful answer. Cite sources when possible."
        return formatted


# Alternative: Use DuckDuckGo HTML search (more reliable)
def search_duckduckgo(query: str, max_results: int = 3) -> List[Dict]:
    """
    Search using DuckDuckGo HTML (more reliable than API)
    Returns simplified results
    """
    try:
        from bs4 import BeautifulSoup

        url = "https://html.duckduckgo.com/html/"
        params = {"q": query}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        results = []

        # Parse search results
        for result in soup.find_all('div', class_='result')[:max_results]:
            title_elem = result.find('a', class_='result__a')
            snippet_elem = result.find('a', class_='result__snippet')

            if title_elem:
                title = title_elem.get_text(strip=True)
                url = title_elem.get('href', '')
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''

                results.append({
                    "title": title,
                    "snippet": snippet[:300],
                    "url": url,
                    "type": "web_result"
                })

        return results

    except Exception as e:
        logger.warning(f"DuckDuckGo search error: {e}")
        return []



