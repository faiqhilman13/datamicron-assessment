from typing import List, Dict
import os
from dotenv import load_dotenv
from exa_py import Exa

load_dotenv()


class ExaWebSearch:
    """Web search using Exa API"""

    def __init__(self):
        api_key = os.getenv("EXA_API_KEY")
        if not api_key:
            print("WARNING: EXA_API_KEY not found in environment variables")
            self.enabled = False
            self.client = None
        else:
            self.client = Exa(api_key=api_key)
            self.enabled = True
            print("✓ Exa API client initialized")

    def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """
        Perform web search using Exa MCP

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            List of search results with title, url, and text content
        """
        try:
            # For now, this is a placeholder that will be integrated with MCP
            # In the actual implementation, this would call the Exa MCP server

            print(f"[Web Search] Searching for: {query}")

            # Placeholder: In production, this would use the MCP integration
            # The actual implementation will be done when connecting to MCP
            results = self._search_via_mcp(query, num_results)

            return results

        except Exception as e:
            print(f"Error in web search: {e}")
            return []

    def _search_via_mcp(self, query: str, num_results: int) -> List[Dict]:
        """
        Call Exa API for web search

        Returns:
            List of raw search results from Exa
        """
        if not self.enabled or not self.client:
            print("[Web Search] ERROR: Exa API not initialized (missing API key)")
            return []

        try:
            print(f"[Web Search] Calling Exa API with query: '{query}'")

            # Use the search() method with proper contents parameter
            # According to Exa docs, search() returns text contents by default
            response = self.client.search(
                query,
                num_results=num_results,
                type="auto",  # Let Exa choose the best search type
                contents={"text": {"max_characters": 10000}}  # Get full text content
            )

            print(f"[Web Search] ✓ Got {len(response.results)} results from Exa")

            # Convert Exa results to our format
            results = []
            for result in response.results:
                results.append({
                    "title": result.title,
                    "url": result.url,
                    "text": result.text if hasattr(result, 'text') else "",
                    "score": result.score if hasattr(result, 'score') else 0.8,
                    "published_date": result.published_date if hasattr(result, 'published_date') else None
                })

            return results

        except Exception as e:
            print(f"[Web Search] ERROR: {e}")
            import traceback
            traceback.print_exc()
            return []

    def format_results(self, raw_results: List[Dict]) -> List[Dict]:
        """
        Format Exa search results to standardized format

        Args:
            raw_results: Raw results from Exa API

        Returns:
            Formatted results
        """
        formatted = []

        for result in raw_results:
            formatted.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "text": result.get("text", ""),
                "score": result.get("score", 0.5),
                "published_date": result.get("publishedDate", "")
            })

        return formatted


# Integration function to be called from RAG service
def perform_web_search(query: str, num_results: int = 5) -> List[Dict]:
    """
    Convenience function for web search

    Args:
        query: Search query
        num_results: Number of results

    Returns:
        List of formatted search results
    """
    searcher = ExaWebSearch()
    results = searcher.search(query, num_results)
    return searcher.format_results(results) if results else []


def test_web_search():
    """Test web search functionality"""
    searcher = ExaWebSearch()

    query = "Malaysian economy 2025 headwinds"
    print(f"Testing web search for: {query}")

    results = searcher.search(query, num_results=3)

    if results:
        print(f"\nFound {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.get('title', 'N/A')}")
            print(f"   URL: {result.get('url', 'N/A')}")
            print(f"   Preview: {result.get('text', '')[:150]}...")
    else:
        print("\nNo results found (MCP integration pending)")


if __name__ == "__main__":
    test_web_search()
