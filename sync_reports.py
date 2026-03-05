#!/usr/bin/env python3
"""
Sync Clay County Livestock Auction reports from MyMarketNews.
Uses Firefox via Playwright to access the site and download PDFs.
"""

import os
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "https://mymarketnews.ams.usda.gov"
REPORTS_URL = f"{BASE_URL}/filerepo/reports?field_slug_title_value=Clay+County"
AMS_DIRECT_URL = "https://www.ams.usda.gov/mnreports/ams_1989.pdf"
OUTPUT_DIR = Path("pdfs")


def get_existing_dates() -> set:
    """Get dates of already downloaded PDFs."""
    existing = set()
    for pdf in OUTPUT_DIR.glob("*.pdf"):
        match = re.search(r"(\d{4}-\d{2}-\d{2})", pdf.name)
        if match:
            existing.add(match.group(1))
    return existing


def sync_reports():
    """Download all new reports from MyMarketNews."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    existing_dates = get_existing_dates()
    print(f"Found {len(existing_dates)} existing PDFs")

    new_downloads = []

    with sync_playwright() as p:
        # Use Firefox - works better with this site
        print("Launching Firefox...")
        browser = p.firefox.launch(headless=True)
        context = browser.new_context(
            accept_downloads=True,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = context.new_page()

        print(f"Accessing {REPORTS_URL}")
        page.goto(REPORTS_URL, timeout=60000)
        time.sleep(3)

        # Collect all report info
        reports_to_download = []
        rows = page.query_selector_all("tr")
        print(f"Found {len(rows)} rows in table")

        for row in rows[1:]:  # Skip header
            try:
                cells = row.query_selector_all("td")
                if len(cells) < 6:
                    continue

                report_date = cells[4].inner_text().strip()
                link = row.query_selector('a[href*=".pdf"]')
                if not link:
                    continue

                href = link.get_attribute("href")

                if report_date not in existing_dates:
                    # Construct full URL
                    if href.startswith("/"):
                        full_url = f"{BASE_URL}{href}"
                    elif not href.startswith("http"):
                        full_url = f"{BASE_URL}/{href}"
                    else:
                        full_url = href

                    reports_to_download.append((report_date, full_url))
                else:
                    print(f"  Already have: {report_date}")

            except Exception as e:
                continue

        print(f"\nFound {len(reports_to_download)} new reports to download")

        # Download each PDF
        for report_date, url in reports_to_download:
            output_file = OUTPUT_DIR / f"clay_county_auction_{report_date}.pdf"
            print(f"\nDownloading: {report_date}")
            print(f"  URL: {url}")

            try:
                # Create a new page for download
                download_page = context.new_page()

                # Set up download handler
                with download_page.expect_download(timeout=120000) as download_info:
                    download_page.goto(url, timeout=60000, wait_until="commit")

                download = download_info.value

                # Save the file
                download.save_as(output_file)
                download_page.close()

                if output_file.exists():
                    size = os.path.getsize(output_file)
                    print(f"  Saved: {output_file.name} ({size / 1024:.1f} KB)")
                    new_downloads.append(report_date)
                else:
                    print(f"  Failed to save file")

            except Exception as e:
                print(f"  Error: {e}")
                # Try direct request as fallback
                try:
                    import requests
                    response = requests.get(url, timeout=120)
                    response.raise_for_status()
                    with open(output_file, "wb") as f:
                        f.write(response.content)
                    if output_file.exists():
                        size = os.path.getsize(output_file)
                        print(f"  Saved via fallback: {output_file.name} ({size / 1024:.1f} KB)")
                        new_downloads.append(report_date)
                except Exception as e2:
                    print(f"  Fallback also failed: {e2}")

        browser.close()

    # Summary
    print(f"\n{'='*60}")
    print(f"Download complete!")
    print(f"New reports downloaded: {len(new_downloads)}")
    print(f"Total PDFs in folder: {len(list(OUTPUT_DIR.glob('*.pdf')))}")

    if new_downloads:
        print("\nNew reports:")
        for d in sorted(new_downloads, reverse=True):
            print(f"  {d}")

    return new_downloads


def update_extracted_data():
    """Re-run extraction on all PDFs to update the CSV."""
    print("\nUpdating extracted data...")
    import subprocess
    result = subprocess.run(
        ["python", "extract_pdf_data.py"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")


if __name__ == "__main__":
    new_reports = sync_reports()

    if new_reports:
        update_extracted_data()
