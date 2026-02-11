from smolagents import tool
from duckduckgo_search import DDGS
import structlog

logger = structlog.get_logger()

@tool
def web_search(query: str, max_results: int = 5) -> str:
    """
    Performs a web search using DuckDuckGo and returns the results.
    
    Args:
        query: The search query.
        max_results: Number of results to return (default 5).
    """
    try:
        logger.info("web_search", query=query)
        results = DDGS().text(query, max_results=max_results)
        
        if not results:
            return "No results found."
            
        formatted = []
        for i, res in enumerate(results):
            formatted.append(f"[{i+1}] {res['title']}\n{res['href']}\n{res['body']}\n")
            
        return "\n".join(formatted)
        
    except Exception as e:
        return f"Search Error: {str(e)}"
