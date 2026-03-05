#!/usr/bin/env python3
"""
Scrape all Clay County Livestock Auction PDFs from USDA ESMIS using Playwright
Handles pagination to get all historical reports
"""

import os
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


BASE_URL = "https://esmis.nal.usda.gov"
PUBLICATION_URL = f"{BASE_URL}/publication/clay-county-livestock-auction-ashland-al"
OUTPUT_DIR = Path("pdfs")


def extract_date_from_text(text: str) -> str | None:
    """Extract date from text like 'Sep 30 2025' and convert to YYYY-MM-DD format."""
    months = {
        "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04",
        "MAY": "05", "JUN": "06", "JUL": "07", "AUG": "08",
        "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12"
    }

    # Pattern: Month Day Year (e.g., "SEP 30 2025" or "Sep 30 2025")
    pattern = r"(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+(\d{1,2})\s+(\d{4})"
    match = re.search(pattern, text.upper())

    if match:
        month_name, day, year = match.groups()
        month = months[month_name]
        day = day.zfill(2)
        return f"{year}-{month}-{day}"

    return None


def download_pdf(page, href: str, date: str, downloaded: set) -> bool:
    """Download a single PDF file."""
    if date in downloaded:
        return False

    if href.startswith("/"):
        full_url = f"{BASE_URL}{href}"
    elif href.startswith("http"):
        full_url = href
    else:
        full_url = f"{BASE_URL}/{href}"

    output_file = OUTPUT_DIR / f"clay_county_auction_{date}.pdf"

    if output_file.exists():
        print(f"  Already exists: {output_file.name}")
        downloaded.add(date)
        return False

    print(f"  Downloading: {date}")

    try:
        # Use requests for direct download (more reliable)
        import requests
        response = requests.get(full_url, timeout=30)
        response.raise_for_status()

        with open(output_file, 'wb') as f:
            f.write(response.content)

        downloaded.add(date)
        size = os.path.getsize(output_file)
        print(f"    Saved: {output_file.name} ({size / 1024:.1f} KB)")
        return True

    except Exception as e:
        print(f"    Error: {e}")
        return False


def scrape_page(page, downloaded: set) -> int:
    """Scrape all PDFs from the current page view."""
    count = 0

    # Find all PDF links
    pdf_links = page.query_selector_all('a[href*=".PDF"], a[href*=".pdf"]')

    for link in pdf_links:
        try:
            href = link.get_attribute("href")
            if not href:
                continue

            # Get text near the link to extract date
            parent_text = link.evaluate("el => (el.closest('tr') || el.parentElement).innerText")
            date = extract_date_from_text(parent_text)

            if not date:
                continue

            if download_pdf(page, href, date, downloaded):
                count += 1

        except Exception as e:
            continue

    return count


def scrape_all_pdfs():
    OUTPUT_DIR.mkdir(exist_ok=True)
    downloaded = set()
    total_downloaded = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print(f"Navigating to {PUBLICATION_URL}")
        page.goto(PUBLICATION_URL, wait_until="networkidle")
        time.sleep(2)

        # Scrape the first page
        print("\n=== Page 1 ===")
        count = scrape_page(page, downloaded)
        total_downloaded += count

        # Navigate through pagination
        page_num = 2
        max_pages = 100  # Safety limit

        while page_num <= max_pages:
            # Look for the next page link
            next_link = page.query_selector(f'.usa-pagination__item a:has-text("{page_num}")')

            if not next_link:
                # Try the "Next" link
                next_link = page.query_selector('.usa-pagination__arrow a:has-text("Next")')

            if not next_link:
                print(f"\nNo more pages found after page {page_num - 1}")
                break

            print(f"\n=== Page {page_num} ===")

            try:
                next_link.click()
                time.sleep(2)  # Wait for page to load

                count = scrape_page(page, downloaded)
                total_downloaded += count

                if count == 0:
                    # Check if we got any new links at all
                    pdf_links = page.query_selector_all('a[href*=".PDF"], a[href*=".pdf"]')
                    if len(pdf_links) == 0:
                        print("  No PDF links found on this page")
                        break

                page_num += 1

            except Exception as e:
                print(f"  Error navigating: {e}")
                break

        browser.close()

    # Print summary
    print(f"\n{'='*60}")
    print(f"Download complete!")
    print(f"Total files downloaded this run: {total_downloaded}")
    print(f"Total files in {OUTPUT_DIR}/: {len(list(OUTPUT_DIR.glob('*.pdf')))}")
    print(f"\nFiles by year:")

    files = sorted(OUTPUT_DIR.glob("*.pdf"))
    years = {}
    for f in files:
        year = f.name.split("_")[-1][:4]
        years[year] = years.get(year, 0) + 1

    for year in sorted(years.keys(), reverse=True):
        print(f"  {year}: {years[year]} files")


if __name__ == "__main__":
    scrape_all_pdfs()
