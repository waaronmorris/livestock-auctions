#!/usr/bin/env python3
"""
Download Clay County reports using the MARS API and alternative sources.
"""

import os
import re
import time
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

OUTPUT_DIR = Path("pdfs")

# Known report URLs
MARS_API = "https://www.ams.usda.gov/mnreports/ams_1989.pdf"  # Latest report
ESMIS_BASE = "https://esmis.nal.usda.gov"


def get_existing_dates() -> set:
    """Get dates of already downloaded PDFs."""
    existing = set()
    for pdf in OUTPUT_DIR.glob("*.pdf"):
        match = re.search(r"(\d{4}-\d{2}-\d{2})", pdf.name)
        if match:
            existing.add(match.group(1))
    return existing


def download_via_playwright():
    """Use Playwright to download PDFs directly through the browser."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    existing_dates = get_existing_dates()
    print(f"Found {len(existing_dates)} existing PDFs")

    new_downloads = []

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        context = browser.new_context(
            accept_downloads=True,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = context.new_page()

        # First get the list of reports
        print("Getting report list from MyMarketNews...")
        url = "https://mymarketnews.ams.usda.gov/filerepo/reports?field_slug_title_value=Clay+County"
        page.goto(url, timeout=60000)
        time.sleep(3)

        # Collect all download links and dates
        reports = []
        rows = page.query_selector_all("tr")

        for row in rows[1:]:
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
                    reports.append((report_date, href))
            except:
                continue

        print(f"Found {len(reports)} new reports to download")

        # Download each report using Playwright's download handler
        for report_date, href in reports:
            try:
                if href.startswith("/"):
                    full_url = f"https://mymarketnews.ams.usda.gov{href}"
                elif not href.startswith("http"):
                    full_url = f"https://mymarketnews.ams.usda.gov/{href}"
                else:
                    full_url = href

                output_file = OUTPUT_DIR / f"clay_county_auction_{report_date}.pdf"

                print(f"  Downloading: {report_date}")

                # Navigate to PDF and download
                with page.expect_download(timeout=60000) as download_info:
                    page.goto(full_url, timeout=60000)

                download = download_info.value
                download.save_as(output_file)

                if output_file.exists():
                    size = os.path.getsize(output_file)
                    print(f"    Saved: {output_file.name} ({size / 1024:.1f} KB)")
                    new_downloads.append(report_date)
                else:
                    print(f"    Failed to save")

            except Exception as e:
                print(f"    Error: {e}")

                # Try alternative: direct page content
                try:
                    page.goto(full_url, timeout=30000)
                    time.sleep(2)
                    # If it's a PDF viewer, try to get the content
                except:
                    pass

                continue

        browser.close()

    print(f"\n{'='*50}")
    print(f"Downloaded {len(new_downloads)} new reports")

    return new_downloads


def download_latest_from_ams():
    """Download the latest report from AMS direct link."""
    print("\nTrying AMS direct link for latest report...")

    try:
        response = requests.get(MARS_API, timeout=60)
        response.raise_for_status()

        # Save with today's approximate date
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        output_file = OUTPUT_DIR / f"clay_county_auction_{today}_latest.pdf"

        with open(output_file, "wb") as f:
            f.write(response.content)

        size = os.path.getsize(output_file)
        print(f"  Saved latest report: {output_file.name} ({size / 1024:.1f} KB)")
        return True

    except Exception as e:
        print(f"  Error: {e}")
        return False


if __name__ == "__main__":
    # Try Playwright download first
    new_reports = download_via_playwright()

    # Also try direct AMS link
    if not new_reports:
        download_latest_from_ams()
