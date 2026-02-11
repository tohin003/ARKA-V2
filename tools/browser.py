from smolagents import tool
from playwright.sync_api import sync_playwright
import structlog
import time

logger = structlog.get_logger()

@tool
def visit_page(url: str) -> str:
    """
    Visits a web page using a real browser (Playwright) and returns the text content.
    
    Args:
        url: The URL to visit.
    """
    try:
        with sync_playwright() as p:
            # Launch browser (headless=True for speed, False for debugging if needed)
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            logger.info("browser_visit", url=url)
            page.goto(url, timeout=30000)
            
            # Wait for content
            time.sleep(2) 
            
            title = page.title()
            content = page.inner_text("body")
            
            browser.close()
            
            return f"Title: {title}\n\nContent Preview:\n{content[:2000]}..."
            
    except Exception as e:
        return f"Browser Error: {str(e)}"
