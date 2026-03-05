#!/usr/bin/env python3
"""
Explore the ESMIS page structure to find all available reports
"""

import time
from playwright.sync_api import sync_playwright


BASE_URL = "https://esmis.nal.usda.gov"
PUBLICATION_URL = f"{BASE_URL}/publication/clay-county-livestock-auction-ashland-al"


def explore_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print(f"Navigating to {PUBLICATION_URL}")
        page.goto(PUBLICATION_URL, wait_until="networkidle")
        time.sleep(2)

        # Get page title
        title = page.title()
        print(f"\nPage title: {title}")

        # Look for pagination elements
        print("\n=== Looking for pagination ===")
        pager_elements = page.query_selector_all('.pager, .pagination, [class*="pager"], [class*="page"]')
        print(f"Found {len(pager_elements)} pager-like elements")

        for el in pager_elements[:5]:
            text = el.inner_text()[:100] if el.inner_text() else ""
            cls = el.get_attribute("class")
            print(f"  Class: {cls}, Text: {text}")

        # Look for "load more" or "show all" buttons
        print("\n=== Looking for load more / show all ===")
        buttons = page.query_selector_all('button, a.btn, input[type="button"]')
        for btn in buttons:
            text = btn.inner_text().strip() if btn.inner_text() else ""
            if text:
                print(f"  Button: {text}")

        # Look for dropdowns or filters
        print("\n=== Looking for filters/dropdowns ===")
        selects = page.query_selector_all('select')
        for sel in selects:
            name = sel.get_attribute("name") or sel.get_attribute("id") or "unnamed"
            options = sel.query_selector_all("option")
            print(f"  Select '{name}': {len(options)} options")
            for opt in options[:5]:
                print(f"    - {opt.inner_text()}")

        # Look for year links
        print("\n=== Looking for year/date links ===")
        links = page.query_selector_all('a')
        year_links = []
        for link in links:
            text = link.inner_text().strip() if link.inner_text() else ""
            href = link.get_attribute("href") or ""
            if any(str(y) in text for y in range(2015, 2026)) or "archive" in href.lower() or "history" in href.lower():
                year_links.append((text, href))

        for text, href in year_links[:20]:
            print(f"  {text}: {href}")

        # Check for iframe or dynamic content containers
        print("\n=== Looking for iframes ===")
        iframes = page.query_selector_all('iframe')
        print(f"Found {len(iframes)} iframes")

        # Look at the table structure
        print("\n=== Table structure ===")
        tables = page.query_selector_all('table')
        print(f"Found {len(tables)} tables")

        for i, table in enumerate(tables[:3]):
            rows = table.query_selector_all('tr')
            print(f"  Table {i+1}: {len(rows)} rows")

        # Get all unique href patterns
        print("\n=== PDF link patterns ===")
        pdf_links = page.query_selector_all('a[href*=".PDF"], a[href*=".pdf"]')
        for link in pdf_links[:5]:
            href = link.get_attribute("href")
            print(f"  {href}")

        # Check the page source for API endpoints
        print("\n=== Looking for API/data endpoints ===")
        content = page.content()
        import re
        api_patterns = re.findall(r'(https?://[^"\s]+(?:api|json|data)[^"\s]*)', content)
        for api in set(api_patterns)[:10]:
            print(f"  {api}")

        browser.close()


if __name__ == "__main__":
    explore_page()
