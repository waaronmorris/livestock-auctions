#!/usr/bin/env python3
"""
Download new Clay County Livestock Auction reports from MyMarketNews using Firefox.
"""

import os
import re
import time
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

BASE_URL = "https://mymarketnews.ams.usda.gov"
REPORTS_URL = f"{BASE_URL}/filerepo/reports?field_slug_id_value=&name=&field_slug_title_value=Clay+County&field_published_date_value=&field_report_date_end_value=&field_api_market_types_target_id=All&order=&sort="
OUTPUT_DIR = Path("pdfs")


def get_existing_dates() -> set:
    """Get dates of already downloaded PDFs."""
    existing = set()
    for pdf in OUTPUT_DIR.glob("*.pdf"):
        match = re.search(r"(\d{4}-\d{2}-\d{2})", pdf.name)
        if match:
            existing.add(match.group(1))
    return existing


def download_new_reports():
    OUTPUT_DIR.mkdir(exist_ok=True)
    existing_dates = get_existing_dates()
    print(f"Found {len(existing_dates)} existing PDFs")

    new_downloads = []

    with sync_playwright() as p:
        # Use Firefox - it works better with this site
        browser = p.firefox.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = context.new_page()

        print(f"Accessing MyMarketNews...")
        page.goto(REPORTS_URL, timeout=60000)
        time.sleep(3)

        # Get all report rows
        rows = page.query_selector_all("tr")
        print(f"Found {len(rows)} rows")

        for row in rows[1:]:  # Skip header
            try:
                cells = row.query_selector_all("td")
                if len(cells) < 6:
                    continue

                # Get report date (column 5, index 4)
                report_date = cells[4].inner_text().strip()

                # Get download link
                link = row.query_selector('a[href*=".pdf"]')
                if not link:
                    continue

                href = link.get_attribute("href")

                # Check if we already have this date
                if report_date in existing_dates:
                    print(f"  Already have: {report_date}")
                    continue

                # Construct full URL
                if href.startswith("http"):
                    full_url = href
                elif href.startswith("/"):
                    full_url = f"{BASE_URL}{href}"
                else:
                    full_url = f"{BASE_URL}/{href}"

                output_file = OUTPUT_DIR / f"clay_county_auction_{report_date}.pdf"

                print(f"  Downloading: {report_date}")

                # Use Playwright to trigger download via JavaScript click
                try:
                    download_page = context.new_page()
                    with download_page.expect_download(timeout=180000) as download_info:
                        download_page.evaluate(f'''() => {{
                            const a = document.createElement("a");
                            a.href = "{full_url}";
                            a.download = "temp.pdf";
                            document.body.appendChild(a);
                            a.click();
                        }}''')

                    download = download_info.value
                    download.save_as(output_file)
                    download_page.close()

                    if output_file.exists():
                        size = os.path.getsize(output_file)
                        print(f"    Saved: {output_file.name} ({size / 1024:.1f} KB)")
                        new_downloads.append(report_date)
                    else:
                        print(f"    Failed to save file")
                except Exception as download_err:
                    print(f"    Playwright download error: {download_err}")
                    # Fallback to requests with longer timeout
                    try:
                        response = requests.get(full_url, timeout=180)
                        response.raise_for_status()
                        with open(output_file, "wb") as f:
                            f.write(response.content)
                        size = os.path.getsize(output_file)
                        print(f"    Saved via fallback: {output_file.name} ({size / 1024:.1f} KB)")
                        new_downloads.append(report_date)
                    except Exception as req_err:
                        print(f"    Fallback also failed: {req_err}")

            except Exception as e:
                print(f"    Error: {e}")
                continue

        browser.close()

    print(f"\n{'='*50}")
    print(f"Downloaded {len(new_downloads)} new reports")
    if new_downloads:
        print("New dates:")
        for d in sorted(new_downloads, reverse=True):
            print(f"  {d}")

    return new_downloads


if __name__ == "__main__":
    download_new_reports()
