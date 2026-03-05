#!/usr/bin/env python3
"""Check for 2026 reports on ESMIS."""

import time
from playwright.sync_api import sync_playwright

BASE_URL = "https://esmis.nal.usda.gov"
PUBLICATION_URL = f"{BASE_URL}/publication/clay-county-livestock-auction-ashland-al"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_context().new_page()

    print(f"Navigating to {PUBLICATION_URL}")
    page.goto(PUBLICATION_URL, wait_until="networkidle")
    time.sleep(2)

    # Check the date filter dropdown for 2026 options
    print("\n=== Checking date filter for 2026 ===")
    select = page.query_selector('select[name="date"]')
    if select:
        options = select.query_selector_all("option")
        for opt in options[:20]:
            text = opt.inner_text().strip()
            if "2026" in text or "January" in text or "February" in text or "March" in text:
                print(f"  Found: {text}")

    # Get latest reports on page
    print("\n=== Latest reports on page ===")
    links = page.query_selector_all('a[href*=".PDF"], a[href*=".pdf"]')
    for link in links[:5]:
        text = link.evaluate("el => (el.closest('tr') || el.parentElement).innerText")
        print(f"  {text[:60]}...")

    browser.close()
