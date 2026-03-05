#!/usr/bin/env python3
"""
Download Clay County Livestock Auction PDFs from USDA ESMIS
"""

import os
import requests
from pathlib import Path

BASE_URL = "https://esmis.nal.usda.gov"
OUTPUT_DIR = Path("pdfs")
OUTPUT_DIR.mkdir(exist_ok=True)

# PDF paths with dates from the webpage
PDFS = {
    "2025-09-30": "/sites/default/release-files/qj72p715b/x920hz72c/k356c5266/AMS_1989.PDF",
    "2025-09-23": "/sites/default/release-files/qj72p715b/jq087j65f/xd07js55t/AMS_1989.PDF",
    "2025-09-16": "/sites/default/release-files/qj72p715b/4742c8609/zg64wm387/AMS_1989.PDF",
    "2025-09-09": "/sites/default/release-files/qj72p715b/7d27bs84r/1257ct154/AMS_1989.PDF",
    "2025-09-02": "/sites/default/release-files/qj72p715b/05743r66s/q237ks19j/AMS_1989.PDF",
    "2025-08-26": "/sites/default/release-files/qj72p715b/8c97nn51m/j67334348/AMS_1989.PDF",
    "2025-08-19": "/sites/default/release-files/qj72p715b/6q184k34w/66830385s/AMS_1989.PDF",
    "2025-08-12": "/sites/default/release-files/qj72p715b/mk61th64b/8c97nn34z/AMS_1989.PDF",
    "2025-08-05": "/sites/default/release-files/qj72p715b/jh345r812/mw22x5865/AMS_1989.PDF",
    "2025-07-29": "/sites/default/release-files/qj72p715b/7h14cp484/nc582k56r/AMS_1989.PDF",
}

def download_pdfs():
    print("Downloading Clay County Livestock Auction PDFs...")

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })

    for date, path in sorted(PDFS.items(), reverse=True):
        url = f"{BASE_URL}{path}"
        output_file = OUTPUT_DIR / f"clay_county_auction_{date}.pdf"

        print(f"Downloading: {date} -> {output_file}")

        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()

            with open(output_file, 'wb') as f:
                f.write(response.content)

            size = os.path.getsize(output_file)
            print(f"  Success: {size / 1024:.1f} KB")

        except Exception as e:
            print(f"  Failed: {e}")

    print(f"\nDownload complete. Files saved to {OUTPUT_DIR}/")
    for f in sorted(OUTPUT_DIR.glob("*.pdf")):
        print(f"  {f.name} ({os.path.getsize(f) / 1024:.1f} KB)")

if __name__ == "__main__":
    download_pdfs()
