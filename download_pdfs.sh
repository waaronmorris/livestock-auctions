#!/bin/bash

# Download Clay County Livestock Auction PDFs from USDA ESMIS
BASE_URL="https://esmis.nal.usda.gov"
OUTPUT_DIR="pdfs"

mkdir -p "$OUTPUT_DIR"

# Array of PDF paths with dates
declare -A PDFS=(
    ["2025-09-30"]="/sites/default/release-files/qj72p715b/x920hz72c/k356c5266/AMS_1989.PDF"
    ["2025-09-23"]="/sites/default/release-files/qj72p715b/jq087j65f/xd07js55t/AMS_1989.PDF"
    ["2025-09-16"]="/sites/default/release-files/qj72p715b/4742c8609/zg64wm387/AMS_1989.PDF"
    ["2025-09-09"]="/sites/default/release-files/qj72p715b/7d27bs84r/1257ct154/AMS_1989.PDF"
    ["2025-09-02"]="/sites/default/release-files/qj72p715b/05743r66s/q237ks19j/AMS_1989.PDF"
    ["2025-08-26"]="/sites/default/release-files/qj72p715b/8c97nn51m/j67334348/AMS_1989.PDF"
    ["2025-08-19"]="/sites/default/release-files/qj72p715b/6q184k34w/66830385s/AMS_1989.PDF"
    ["2025-08-12"]="/sites/default/release-files/qj72p715b/mk61th64b/8c97nn34z/AMS_1989.PDF"
    ["2025-08-05"]="/sites/default/release-files/qj72p715b/jh345r812/mw22x5865/AMS_1989.PDF"
    ["2025-07-29"]="/sites/default/release-files/qj72p715b/7h14cp484/nc582k56r/AMS_1989.PDF"
)

echo "Downloading Clay County Livestock Auction PDFs..."

for date in "${!PDFS[@]}"; do
    url="${BASE_URL}${PDFS[$date]}"
    output_file="${OUTPUT_DIR}/clay_county_auction_${date}.pdf"

    echo "Downloading: $date -> $output_file"
    curl -s -o "$output_file" "$url"

    if [ $? -eq 0 ]; then
        echo "  Success: $(ls -lh "$output_file" | awk '{print $5}')"
    else
        echo "  Failed!"
    fi
done

echo ""
echo "Download complete. Files saved to $OUTPUT_DIR/"
ls -la "$OUTPUT_DIR"
