# Clay County Livestock Auction Analysis

Interactive market analysis dashboard for the Clay County Livestock Auction in Lineville, Alabama. Built with [Marimo](https://marimo.io) and Plotly.

## Features

- **Price Trends**: Monthly average prices by cattle type (BRED COW, BULL, COW, HEIFER, STEER)
- **Volume Analysis**: Monthly head count by category (FEEDER, REPLACEMENT, SLAUGHTER)
- **Weight vs Price**: Scatter plot with recency-weighted linear regression by market type
- **Year-over-Year Comparison**: Annual price trends by cattle type
- **Interactive Filters**: Filter by category, cattle type, and year

## Data

- **Source**: USDA Agricultural Marketing Service (AMS)
- **Report**: Clay County Livestock Auction, Lineville, AL (AMS_1989)
- **Records**: 15,584 auction records
- **Date Range**: May 2019 – March 2026
- **Updated**: Weekly

## Installation

```bash
# Clone the repository
git clone https://github.com/waaronmorris/livestock-auctions.git
cd livestock-auctions

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install marimo pandas plotly statsmodels numpy

# Run the dashboard
marimo run app.py
```

## Usage

```bash
# Run in view mode
marimo run app.py

# Run in edit mode (for development)
marimo edit app.py
```

The dashboard will be available at http://localhost:2718

## Deployment

### Cloudflare Pages (Free)

Export as a static WASM-powered site that runs entirely in the browser:

```bash
# Export to HTML with WASM support
marimo export html-wasm app.py -o dist --mode run

# Deploy to Cloudflare Pages
npx wrangler pages deploy dist
```

Or connect your GitHub repo to Cloudflare Pages with build command:
```
marimo export html-wasm app.py -o dist --mode run
```

## Project Structure

```
livestock-auctions/
├── app.py                     # Marimo dashboard application
├── data/
│   └── clay_county_auction_data.csv  # Extracted auction data
├── pdfs/                      # Source PDF reports (not tracked)
├── download_new_reports.py    # Script to download new USDA reports
├── extract_pdf_data.py        # Script to extract data from PDFs
└── sync_reports.py            # Automated sync script
```

## Market Analysis

The dashboard provides insights into cattle market dynamics:

- **Feeder cattle** (HEIFER, STEER, BULL): Price decreases with weight as heavier animals cost more to finish
- **Slaughter cattle** (COW, BULL): Price increases with weight as heavier animals yield more meat
- **BRED COW**: Sold by head (not weight), prices reflect breeding value

The recency-weighted regression uses exponential decay to weight recent data more heavily, accounting for inflation and market changes.
