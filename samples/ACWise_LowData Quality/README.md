# AC Wise Low Quality Data Template

## Overview
This folder contains a sample PDF from the AC Wise Low Quality Data source.

## Template Details
**Name:** AC Wise Low Quality  
**Status:** ✅ Calibrated  
**Last Updated:** 2025-12-21

## Layout Specifications
- **Columns:** 3
- **Rows:** 6 per page
- **Page Size:** A4 @ 300 DPI (2480 × 3509 px)

## Coordinates (in % of page)
- **Left Margin:** 1%
- **Right Margin:** 1%
- **Top Margin:** 7%
- **Bottom Margin:** 4%

## Known Issues
- Low image quality (as per folder name)
- Smaller font size compared to Boothlist Division
- Photo quality may be poor, which could affect contrast

## Calibration Method
Analyzed using `calibrate_ac_wise.py` script which:
1. Loaded the sample PDF at 300 DPI
2. Measured page dimensions
3. Identified grid structure (3×6)
4. Calculated optimal margins

## Files
- `2024-EROLLGEN-S13-72-FinalRoll-Revision2-MAR-01.pdf` — Sample AC Wise PDF
- `preview.jpg` — Preview image of first page at 300 DPI
