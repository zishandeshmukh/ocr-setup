#!/usr/bin/env python3
"""Analyze AC Wise PDF EPIC positions to identify extraction issues."""

import os
import re
import io
from collections import defaultdict
from google.cloud import vision
import fitz  # PyMuPDF

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-cloud-vision-key.json'

PDF_PATH = 'samples/ACWise_LowData Quality/2024-EROLLGEN-S13-72-FinalRoll-Revision2-MAR-01.pdf'
PAGE_NUM = 3

print(f"Analyzing AC Wise PDF: {PDF_PATH}")
print(f"Analyzing page {PAGE_NUM}...\n")

# Initialize GCV client
client = vision.ImageAnnotatorClient()
print("✅ Google Cloud Vision client initialized")

# Open PDF
pdf_document = fitz.open(PDF_PATH)
page_count = pdf_document.page_count
print(f"Total pages: {page_count}")

# Get the page (0-indexed)
page_obj = pdf_document[PAGE_NUM - 1]

# Render page to image at 300 DPI
zoom = 300 / 72
mat = fitz.Matrix(zoom, zoom)
pix = page_obj.get_pixmap(matrix=mat)

# Save temporarily
temp_dir = 'temp'
os.makedirs(temp_dir, exist_ok=True)
temp_image_path = os.path.join(temp_dir, f'ac_wise_page{PAGE_NUM}.jpg')
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

# Sort EPICs by y, then x
epics_sorted = sorted(epics, key=lambda e: (e['y'], e['x']))

print("All EPIC positions (y, x, x_min, x_max):")
print("-" * 80)
for i, ep in enumerate(epics_sorted, 1):
    print(f"{i:3}. y={ep['y']:7.1f}  x={ep['x']:7.1f}  x_range=[{ep['x_min']:5.0f}, {ep['x_max']:5.0f}]  | {ep['text']}")

# Group EPICs into rows
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

print("\n" + "=" * 80)
print(f"Row structure ({len(rows)} rows detected):")
print("=" * 80)
for i, row in enumerate(rows, 1):
    row_sorted = sorted(row, key=lambda e: e['x'])
    epic_list = ', '.join([e['text'] for e in row_sorted])
    avg_y = sum(e['y'] for e in row) / len(row)
    print(f"Row {i}: {len(row)} EPICs at y≈{avg_y:.1f}")
    print(f"        {epic_list}")

# Analyze margins
print("\n" + "=" * 80)
print("Current AC Wise template margins:")
print("=" * 80)
print(f"  Left: 1% = {page_width * 0.01:.1f}px")
print(f"  Right: 1% = {page_width * 0.01:.1f}px")
print(f"  Top: 7% = {page_height * 0.07:.1f}px")
print(f"  Bottom: 4% = {page_height * 0.04:.1f}px")

epic_x_values = [e['x'] for e in epics]
epic_x_min_values = [e['x_min'] for e in epics]
epic_x_max_values = [e['x_max'] for e in epics]

print("\n" + "=" * 80)
print("EPIC X-position analysis:")
print("=" * 80)
print(f"  Leftmost EPIC center: {min(epic_x_values):.1f}px")
print(f"  Leftmost EPIC start: {min(epic_x_min_values):.1f}px")
print(f"  Rightmost EPIC center: {max(epic_x_values):.1f}px")
print(f"  Rightmost EPIC end: {max(epic_x_max_values):.1f}px")
print(f"  Page width: {page_width}px")

# Check if EPICs are near edges
left_margin_px = page_width * 0.01
right_margin_px = page_width * 0.01

epics_near_left = [e for e in epics if e['x_min'] < left_margin_px + 50]
epics_near_right = [e for e in epics if e['x_max'] > (page_width - right_margin_px - 50)]

print(f"\n  EPICs within 50px of left margin: {len(epics_near_left)}")
if epics_near_left:
    for e in epics_near_left[:3]:
        print(f"    {e['text']} at x={e['x_min']:.1f}")

print(f"  EPICs within 50px of right margin: {len(epics_near_right)}")
if epics_near_right:
    for e in epics_near_right[:3]:
        print(f"    {e['text']} at x={e['x_max']:.1f}")

pdf_document.close()
print("\n✅ Analysis complete!")
