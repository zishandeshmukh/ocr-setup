#!/usr/bin/env python3
"""Analyze Mahanagarpalika PDF layout to find EPIC positions and calculate margins."""

import os
import re
import io
from collections import defaultdict
from google.cloud import vision
import fitz  # PyMuPDF

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-cloud-vision-key.json'

PDF_PATH = 'samples/Mahanagarpalika/DraftList_Ward_11.pdf'
# Try page 3 first (pages 1-2 might be cover pages)
PAGE_NUM = 3

print(f"Analyzing Mahanagarpalika PDF: {PDF_PATH}")
print(f"Analyzing page {PAGE_NUM}...\n")

# Initialize GCV client
client = vision.ImageAnnotatorClient()
print("✅ Google Cloud Vision client initialized")

# Open PDF
pdf_document = fitz.open(PDF_PATH)
page_count = pdf_document.page_count
print(f"Total pages: {page_count}")

if PAGE_NUM > page_count:
    print(f"⚠️ Only {page_count} pages available, analyzing page {min(PAGE_NUM, page_count)}")
    PAGE_NUM = min(PAGE_NUM, page_count)

# Get the page (0-indexed)
page_obj = pdf_document[PAGE_NUM - 1]

# Render page to image at 300 DPI
zoom = 300 / 72
mat = fitz.Matrix(zoom, zoom)
pix = page_obj.get_pixmap(matrix=mat)

# Save temporarily
temp_dir = 'temp'
os.makedirs(temp_dir, exist_ok=True)
temp_image_path = os.path.join(temp_dir, f'mahanagarpalika_page{PAGE_NUM}.jpg')
pix.save(temp_image_path, output="jpeg", jpg_quality=95)

# Get image dimensions
page_width, page_height = pix.width, pix.height
print(f"Page dimensions: {page_width} x {page_height} px at 300 DPI\n")

# Run OCR on the image
with io.open(temp_image_path, 'rb') as image_file:
    content = image_file.read()

image = vision.Image(content=content)
response = client.document_text_detection(
    image=image,
    image_context={'language_hints': ['mr', 'hi', 'en']}
)

if response.error.message:
    raise Exception(f"OCR Error: {response.error.message}")

# Get page data
full_anno = response.full_text_annotation
if not full_anno or not full_anno.pages:
    raise Exception("No page data")

page = full_anno.pages[0]

# Extract all words
words = []
for block in page.blocks:
    for para in block.paragraphs:
        for word in para.words:
            text = ''.join([symbol.text for symbol in word.symbols])
            vertices = word.bounding_box.vertices
            x_coords = [v.x for v in vertices]
            y_coords = [v.y for v in vertices]
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            x_center = (x_min + x_max) / 2
            y_center = (y_min + y_max) / 2
            words.append({
                'text': text,
                'x': x_center,
                'y': y_center,
                'x_min': x_min,
                'x_max': x_max,
                'y_min': y_min,
                'y_max': y_max
            })

print(f"OCR: {len(words)} word annotations\n")

# Find EPICs (3 letters + 7 digits)
epic_pattern = re.compile(r'^[A-Z]{3}\d{7}$')
epics = [w for w in words if epic_pattern.match(w['text'])]

print(f"Found: {len(epics)} EPIC tokens\n")

if not epics:
    print("⚠️ No EPICs found! Trying to find partial matches...")
    # Look for tokens that might be EPICs
    partial_pattern = re.compile(r'[A-Z]{2,3}\d{5,7}')
    partial_epics = [w for w in words if partial_pattern.match(w['text'])]
    print(f"Found {len(partial_epics)} partial EPIC-like tokens:")
    for pe in partial_epics[:10]:
        print(f"  {pe['text']} at ({pe['x']:.1f}, {pe['y']:.1f})")
    print("\n⚠️ This page may not have voter data. Try analyzing a different page.")
else:
    # Sort EPICs by y, then x
    epics_sorted = sorted(epics, key=lambda e: (e['y'], e['x']))

    print("All EPIC positions (y, x):")
    print("-" * 60)
    for i, ep in enumerate(epics_sorted, 1):
        print(f"{i:3}. y={ep['y']:7.1f}  x={ep['x']:7.1f}  | {ep['text']}")

    # Detect rows (Y-spacing analysis)
    print("\n" + "=" * 60)
    print("Y-spacing between consecutive EPICs:")
    print("=" * 60)
    for i in range(len(epics_sorted) - 1):
        y_diff = epics_sorted[i+1]['y'] - epics_sorted[i]['y']
        marker = " <-- NEW ROW" if y_diff > 100 else ""
        print(f"EPIC {i+1} -> {i+2}: {y_diff:6.1f} px{marker}")

    # Group EPICs into rows (threshold = 50px)
    rows = []
    current_row = []
    for ep in epics_sorted:
        if not current_row:
            current_row.append(ep)
        else:
            y_diff = abs(ep['y'] - current_row[0]['y'])
            if y_diff < 50:
                current_row.append(ep)
            else:
                rows.append(current_row)
                current_row = [ep]
    if current_row:
        rows.append(current_row)

    print("\n" + "=" * 60)
    print(f"Row structure ({len(rows)} rows detected):")
    print("=" * 60)
    for i, row in enumerate(rows, 1):
        row_sorted = sorted(row, key=lambda e: e['x'])
        x_positions = [f"{int(e['x'])}" for e in row_sorted]
        avg_y = sum(e['y'] for e in row) / len(row)
        print(f"Row {i}: {len(row)} EPICs at y≈{avg_y:.1f}, x=[{', '.join(x_positions)}]")

    # Analyze columns
    print("\n" + "=" * 60)
    print("Column analysis:")
    print("=" * 60)
    
    # Use simple binning based on expected 3 columns
    col_width = page_width / 3
    col_assignments = defaultdict(list)
    for ep in epics:
        col_idx = int(ep['x'] / col_width)
        col_assignments[col_idx].append(ep['x'])

    for col_idx in sorted(col_assignments.keys()):
        x_vals = col_assignments[col_idx]
        avg_x = sum(x_vals) / len(x_vals)
        print(f"Column {col_idx + 1}: avg x={avg_x:.1f} ({len(x_vals)} samples)")

    # Calculate margins
    if len(rows) > 1:
        epic_y_values = [e['y'] for e in epics]
        epic_x_values = [e['x'] for e in epics]
        
        top_epic = min(epic_y_values)
        bottom_epic = max(epic_y_values)
        left_epic = min(epic_x_values)
        right_epic = max(epic_x_values)
        
        # Calculate row spacing
        row_centers = [sum(e['y'] for e in row) / len(row) for row in rows]
        spacings = [row_centers[i+1] - row_centers[i] for i in range(len(row_centers) - 1)]
        avg_row_spacing = sum(spacings) / len(spacings) if spacings else 0
        
        print("\n" + "=" * 60)
        print("Layout measurements:")
        print("=" * 60)
        print(f"Page height: {page_height} px")
        print(f"Row span: {top_epic:.1f} to {bottom_epic:.1f} ({bottom_epic - top_epic:.1f} px)")
        print(f"Average row spacing: {avg_row_spacing:.1f} px")
        print(f"First EPIC Y: {top_epic:.1f}")
        print(f"Last EPIC Y: {bottom_epic:.1f}")
        print(f"Leftmost EPIC X: {left_epic:.1f}")
        print(f"Rightmost EPIC X: {right_epic:.1f}")
        
        # Suggest margins for 10-row grid
        print("\n" + "=" * 60)
        print("Suggested template margins (for 10-row grid):")
        print("=" * 60)
        
        top_margin = int(top_epic - 30)
        left_margin = 65  # Standard left margin like other templates
        right_margin = int(page_width - right_epic - 200)
        
        # Calculate bottom for 10 rows
        if avg_row_spacing > 0:
            usable_height = 10 * avg_row_spacing
            bottom_margin = int(page_height - top_margin - usable_height)
        else:
            bottom_margin = int(page_height - bottom_epic - 150)
        
        print(f"  Left:   {left_margin}")
        print(f"  Right:  {right_margin}")
        print(f"  Top:    {top_margin}")
        print(f"  Bottom: {bottom_margin}")
        print(f"  Rows:   10")
        print(f"  Cols:   3")

pdf_document.close()
print("\n✅ Analysis complete!")
