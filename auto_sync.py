#!/usr/bin/env python3
"""
Auto-sync Clay County Livestock Auction reports.
Downloads new reports and updates the extracted data CSV.

Run manually or via cron:
    # Weekly on Tuesday (reports typically published Monday)
    0 6 * * 2 cd /path/to/livestock-auctions && .venv/bin/python auto_sync.py >> sync.log 2>&1
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("pdfs")
LOG_PREFIX = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"


def log(msg: str):
    print(f"{LOG_PREFIX} {msg}")


def run_script(script_name: str) -> tuple[bool, str]:
    """Run a Python script and return success status and output."""
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=600
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Script timed out after 10 minutes"
    except Exception as e:
        return False, str(e)


def main():
    log("Starting auto-sync...")

    # Count existing PDFs
    existing_count = len(list(OUTPUT_DIR.glob("*.pdf")))
    log(f"Found {existing_count} existing PDFs")

    # Run download script
    log("Downloading new reports from MyMarketNews...")
    success, output = run_script("download_new_reports.py")

    if not success:
        log(f"Download script failed: {output}")
        return 1

    # Check if we downloaded any new files
    new_count = len(list(OUTPUT_DIR.glob("*.pdf")))
    downloaded = new_count - existing_count

    if downloaded > 0:
        log(f"Downloaded {downloaded} new report(s)")

        # Re-run extraction
        log("Updating extracted data...")
        success, output = run_script("extract_pdf_data.py")

        if not success:
            log(f"Extraction failed: {output}")
            return 1

        log("Extraction complete")
    else:
        log("No new reports found")

    log(f"Sync complete. Total PDFs: {new_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
