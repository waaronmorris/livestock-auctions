#!/usr/bin/env python3
"""Debug PDF structure to understand table format."""

import pdfplumber
from pathlib import Path

pdf_path = Path("pdfs/clay_county_auction_2025-09-30.pdf")

with pdfplumber.open(pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages):
        print(f"\n{'='*60}")
        print(f"PAGE {page_num + 1}")
        print("="*60)

        text = page.extract_text()
        if text:
            print("\n--- TEXT EXTRACT (first 2000 chars) ---")
            print(text[:2000])

        tables = page.extract_tables()
        print(f"\n--- TABLES: {len(tables)} found ---")

        for i, table in enumerate(tables):
            print(f"\nTable {i+1}: {len(table)} rows")
            for row in table[:15]:  # First 15 rows
                print(f"  {row}")
