#!/usr/bin/env python3
"""Check mymarketnews for 2026 reports."""

import time
from playwright.sync_api import sync_playwright

URL = "https://mymarketnews.ams.usda.gov/filerepo/reports?field_slug_id_value=&name=&field_slug_title_value=Clay+County&field_published_date_value=&field_report_date_end_value=&field_api_market_types_target_id=All&order=&sort="

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_context().new_page()

    print(f"Navigating to MyMarketNews...")
    try:
        page.goto(URL, wait_until="networkidle", timeout=30000)
        time.sleep(3)

        # Get page content
        text = page.content()

        # Look for 2026 references
        if "2026" in text:
            print("Found references to 2026!")

        # Get all report links
        print("\n=== Reports found ===")
        rows = page.query_selector_all('tr, .views-row')
        for row in rows[:15]:
            row_text = row.inner_text().strip()
            if row_text and ("Clay" in row_text or "2025" in row_text or "2026" in row_text):
                print(f"  {row_text[:100]}...")

    except Exception as e:
        print(f"Error: {e}")

    browser.close()
