#!/usr/bin/env python3
"""
Extract livestock auction data from USDA PDF reports by parsing text.
"""

import re
from pathlib import Path

import pandas as pd
import pdfplumber
from tqdm import tqdm


OUTPUT_DIR = Path("data")
PDF_DIR = Path("pdfs")


def extract_date_from_filename(filename: str) -> str:
    """Extract date from filename like 'clay_county_auction_2025-09-30.pdf'."""
    match = re.search(r"(\d{4}-\d{2}-\d{2})", filename)
    return match.group(1) if match else None


def parse_auction_summary(text: str) -> dict:
    """Extract auction summary data from PDF text."""
    summary = {}

    # Total receipts
    match = re.search(r"Total Receipts:\s*(\d+)", text)
    if match:
        summary["total_receipts"] = int(match.group(1))

    # Feeder cattle
    match = re.search(r"Feeder Cattle:\s*(\d+)", text)
    if match:
        summary["feeder_cattle"] = int(match.group(1))

    # Slaughter cattle
    match = re.search(r"Slaughter Cattle:\s*(\d+)", text)
    if match:
        summary["slaughter_cattle"] = int(match.group(1))

    # Replacement cattle
    match = re.search(r"Replacement Cattle:\s*(\d+)", text)
    if match:
        summary["replacement_cattle"] = int(match.group(1))

    return summary


def parse_data_line(line: str) -> dict | None:
    """Parse a data line like '2 535 535 385.00 385.00' or '2 715-725 720 315.00-320.00 317.52'."""
    # Pattern for standard feeder cattle lines: Head WtRange AvgWt PriceRange AvgPrice
    # Examples:
    #   2 535 535 385.00 385.00
    #   2 715-725 720 315.00-320.00 317.52
    #   7 355-390 374 370.00-380.00 375.93

    # Clean the line
    line = line.strip()
    if not line or not line[0].isdigit():
        return None

    # Split by whitespace
    parts = line.split()
    if len(parts) < 5:
        return None

    try:
        head = int(parts[0])

        # Parse weight range (could be "535" or "715-725")
        wt_range = parts[1]
        if "-" in wt_range:
            wt_parts = wt_range.split("-")
            wt_min = float(wt_parts[0])
            wt_max = float(wt_parts[1])
        else:
            wt_min = wt_max = float(wt_range)

        # Parse avg weight
        avg_wt = float(parts[2])

        # Parse price range (could be "385.00" or "315.00-320.00")
        price_range = parts[3]
        if "-" in price_range:
            price_parts = price_range.split("-")
            price_min = float(price_parts[0])
            price_max = float(price_parts[1])
        else:
            price_min = price_max = float(price_range)

        # Parse avg price
        avg_price = float(parts[4])

        # Check for dressing (6th column for slaughter cattle)
        dressing = parts[5] if len(parts) > 5 and parts[5] in ["Average", "Low", "High"] else None

        return {
            "head_count": head,
            "weight_min": wt_min,
            "weight_max": wt_max,
            "avg_weight": avg_wt,
            "price_min": price_min,
            "price_max": price_max,
            "avg_price": avg_price,
            "dressing": dressing,
        }
    except (ValueError, IndexError):
        return None


def parse_bred_cow_line(line: str) -> dict | None:
    """Parse bred cow lines like '2-8 T2 3 3000.00 3000.00'."""
    line = line.strip()
    parts = line.split()

    if len(parts) < 5:
        return None

    try:
        # Age Stage Head PriceRange AvgPrice
        age = parts[0]
        stage = parts[1]
        head = int(parts[2])

        # For bred cows, there's usually no weight, just price
        # Could be: 2-8 T2 3 3000.00 3000.00
        # Or with weight range (empty): 2-8 T2 3 [empty] [empty] 3000.00 3000.00

        # Find price values (look for decimal numbers)
        prices = [p for p in parts[2:] if "." in p]
        if len(prices) >= 2:
            price_range = prices[0]
            avg_price = float(prices[-1])

            if "-" in price_range:
                price_parts = price_range.split("-")
                price_min = float(price_parts[0])
                price_max = float(price_parts[1])
            else:
                price_min = price_max = float(price_range)

            return {
                "head_count": head,
                "age": age,
                "stage": stage,
                "price_min": price_min,
                "price_max": price_max,
                "avg_price": avg_price,
                "weight_min": None,
                "weight_max": None,
                "avg_weight": None,
                "dressing": None,
            }
    except (ValueError, IndexError):
        return None

    return None


def extract_cattle_data(pdf_path: Path) -> list[dict]:
    """Extract all cattle data from a PDF."""
    records = []
    auction_date = extract_date_from_filename(pdf_path.name)

    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            full_text += page_text + "\n"

    # Get auction summary
    summary = parse_auction_summary(full_text)

    # Split text into lines
    lines = full_text.split("\n")

    current_category = "FEEDER"
    current_cattle_type = None
    current_grade = None

    for i, line in enumerate(lines):
        line_upper = line.upper().strip()

        # Detect category changes
        if "FEEDER CATTLE" in line_upper and "SUPPLY" not in line_upper:
            current_category = "FEEDER"
            continue
        elif "SLAUGHTER CATTLE" in line_upper:
            current_category = "SLAUGHTER"
            continue
        elif "REPLACEMENT CATTLE" in line_upper:
            current_category = "REPLACEMENT"
            continue

        # Detect cattle type and grade headers
        if "STEERS - MEDIUM AND LARGE 1" in line_upper and "2" not in line_upper:
            current_cattle_type = "STEER"
            current_grade = "M&L 1"
            continue
        elif "STEERS - MEDIUM AND LARGE 2" in line_upper:
            current_cattle_type = "STEER"
            current_grade = "M&L 2"
            continue
        elif "STEERS - MEDIUM AND LARGE 3" in line_upper:
            current_cattle_type = "STEER"
            current_grade = "M&L 3"
            continue
        elif "HEIFERS - MEDIUM AND LARGE 1" in line_upper and "2" not in line_upper:
            current_cattle_type = "HEIFER"
            current_grade = "M&L 1"
            continue
        elif "HEIFERS - MEDIUM AND LARGE 2" in line_upper:
            current_cattle_type = "HEIFER"
            current_grade = "M&L 2"
            continue
        elif "HEIFERS - MEDIUM AND LARGE 3" in line_upper:
            current_cattle_type = "HEIFER"
            current_grade = "M&L 3"
            continue
        elif "BULLS - MEDIUM AND LARGE 1" in line_upper and "2" not in line_upper:
            current_cattle_type = "BULL"
            current_grade = "M&L 1"
            current_category = "FEEDER"
            continue
        elif "BULLS - MEDIUM AND LARGE 2" in line_upper:
            current_cattle_type = "BULL"
            current_grade = "M&L 2"
            current_category = "FEEDER"
            continue
        elif "BULLS - MEDIUM AND LARGE 3" in line_upper:
            current_cattle_type = "BULL"
            current_grade = "M&L 3"
            current_category = "FEEDER"
            continue
        elif "BULLS - 1-2" in line_upper or "BULLS - 1" in line_upper:
            current_cattle_type = "BULL"
            current_grade = "1-2"
            current_category = "SLAUGHTER"
            continue
        elif "COWS - BONER" in line_upper:
            current_cattle_type = "COW"
            current_grade = "Boner 80-85%"
            current_category = "SLAUGHTER"
            continue
        elif "COWS - LEAN" in line_upper:
            current_cattle_type = "COW"
            current_grade = "Lean 85-90%"
            current_category = "SLAUGHTER"
            continue
        elif "BRED COWS - MEDIUM AND LARGE 1-2" in line_upper:
            current_cattle_type = "BRED COW"
            current_grade = "M&L 1-2"
            current_category = "REPLACEMENT"
            continue
        elif "BRED COWS - MEDIUM AND LARGE 3" in line_upper:
            current_cattle_type = "BRED COW"
            current_grade = "M&L 3"
            current_category = "REPLACEMENT"
            continue

        # Skip header lines
        if "HEAD" in line_upper and "WT RANGE" in line_upper:
            continue
        if "AGE" in line_upper and "STAGE" in line_upper:
            continue

        # Try to parse data line
        if current_cattle_type is None:
            continue

        if current_cattle_type == "BRED COW":
            parsed = parse_bred_cow_line(line)
        else:
            parsed = parse_data_line(line)

        if parsed:
            record = {
                "auction_date": auction_date,
                "category": current_category,
                "cattle_type": current_cattle_type,
                "grade": current_grade,
                **parsed,
                "total_receipts": summary.get("total_receipts"),
                "feeder_cattle_total": summary.get("feeder_cattle"),
                "slaughter_cattle_total": summary.get("slaughter_cattle"),
                "replacement_cattle_total": summary.get("replacement_cattle"),
            }

            # Add age/stage columns for non-bred cows
            if "age" not in record:
                record["age"] = None
            if "stage" not in record:
                record["stage"] = None

            records.append(record)

    return records


def extract_all_pdfs():
    """Extract data from all PDFs and save to CSV."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files to process")

    all_records = []

    for pdf_path in tqdm(pdf_files, desc="Extracting PDFs"):
        try:
            records = extract_cattle_data(pdf_path)
            all_records.extend(records)
        except Exception as e:
            print(f"\nError processing {pdf_path.name}: {e}")
            continue

    if not all_records:
        print("No records extracted!")
        return None

    # Create DataFrame
    df = pd.DataFrame(all_records)

    # Reorder columns
    column_order = [
        "auction_date", "category", "cattle_type", "grade",
        "head_count", "weight_min", "weight_max", "avg_weight",
        "price_min", "price_max", "avg_price", "dressing",
        "age", "stage",
        "total_receipts", "feeder_cattle_total", "slaughter_cattle_total", "replacement_cattle_total"
    ]
    df = df[[c for c in column_order if c in df.columns]]

    # Sort by date and category
    df["auction_date"] = pd.to_datetime(df["auction_date"])
    df = df.sort_values(["auction_date", "category", "cattle_type", "grade", "avg_weight"])

    # Save to CSV
    output_file = OUTPUT_DIR / "clay_county_auction_data.csv"
    df.to_csv(output_file, index=False)
    print(f"\nSaved {len(df)} records to {output_file}")

    # Print summary
    print(f"\nData Summary:")
    print(f"  Date range: {df['auction_date'].min().date()} to {df['auction_date'].max().date()}")
    print(f"  Total records: {len(df)}")
    print(f"\n  Records by category:")
    print(df.groupby("category").size().to_string())
    print(f"\n  Records by cattle type:")
    print(df.groupby("cattle_type").size().to_string())

    return df


if __name__ == "__main__":
    extract_all_pdfs()
