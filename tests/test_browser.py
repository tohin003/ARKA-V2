from tools.browser import visit_page
import pytest

def test_browser_tool():
    print("🧪 Testing Phase 3.3: Browser Tool...")
    
    url = "https://example.com"
    print(f"Visiting {url}...")
    
    result = visit_page(url)
    
    print("\n---------- Result ----------")
    print(result)
    print("----------------------------")
    
    if "Example Domain" in result and "Title:" in result:
        print("✅ Browser visit successful.")
    else:
        print("❌ Browser visit failed or content unexpected.")

if __name__ == "__main__":
    test_browser_tool()
