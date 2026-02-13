from smolagents import tool
from playwright.sync_api import sync_playwright
import structlog
import time
import os
import platform
import glob
import re
import urllib.request

logger = structlog.get_logger()

@tool
def visit_page(url: str) -> str:
    """
    Visits a web page using a real browser (Playwright) and returns the text content.
    
    Args:
        url: The URL to visit.
    """
    try:
        # Ensure correct Playwright platform on Apple Silicon
        if platform.machine() == "arm64" and not os.getenv("PLAYWRIGHT_HOST_PLATFORM_OVERRIDE"):
            os.environ["PLAYWRIGHT_HOST_PLATFORM_OVERRIDE"] = "mac-arm64"

        def _find_chrome_testing_executable():
            base = os.path.expanduser("~/Library/Caches/ms-playwright")
            pattern = os.path.join(base, "chromium-*/chrome-mac-*/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing")
            matches = glob.glob(pattern)
            return matches[0] if matches else None

        with sync_playwright() as p:
            # Launch browser with fallbacks
            browser = None
            last_error = None

            chrome_testing = _find_chrome_testing_executable()
            launch_attempts = [
                {"headless": True, "args": ["--no-sandbox"]},
            ]
            if chrome_testing:
                launch_attempts.append({"headless": True, "executable_path": chrome_testing, "args": ["--no-sandbox"]})
                launch_attempts.append({"headless": False, "executable_path": chrome_testing, "args": ["--no-sandbox"]})

            for attempt in launch_attempts:
                try:
                    browser = p.chromium.launch(**attempt)
                    break
                except Exception as e:
                    last_error = e
                    continue

            if not browser:
                raise RuntimeError(str(last_error))

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
        # Fallback to simple HTTP fetch if Playwright fails
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
            title_match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else "Unknown"
            text_preview = re.sub(r"<[^>]+>", " ", html)
            text_preview = re.sub(r"\s+", " ", text_preview).strip()
            return f"Title: {title}\n\nContent Preview:\n{text_preview[:2000]}..."
        except Exception:
            return f"Browser Error: {str(e)}"
