#!/usr/bin/env python3
"""
Check if detected EPICs are being assigned to correct grid blocks.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from backend.ocr_engine import OCREngine
import fitz
import re

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-cloud-vision-key.json'

def check_epic_grid_assignment():
    """Check which grid cell each EPIC falls into"""
    
    ocr_engine = OCREngine()
    
    # Load PDF
    pdf_path = 'samples/ACWise_LowData Quality/2024-EROLLGEN-S13-72-FinalRoll-Revision2-MAR-01.pdf'
    pdf = fitz.open(pdf_path)
    page_num = 2  # Page 3
    
    # Render page
    page = pdf[page_num]
    zoom = 300 / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    
    temp_dir = 'temp'
    os.makedirs(temp_dir, exist_ok=True)
    temp_image_path = os.path.join(temp_dir, f'ac_wise_grid_check.jpg')
    pix.save(temp_image_path, output="jpeg", jpg_quality=95)
    
    image_W, image_H = pix.width, pix.height
    print(f"Page dimensions: {image_W} x {image_H} px")
    
    # Template margins (updated to match api.py ac_wise_calibrated)
    L = 65
    R = 85
    T = 117
    B = 82
    ROWS = 10
    COLS = 3
    
    # Calculate usable area
    work_w = image_W - L - R
    work_h = image_H - T - B
    
    box_w = work_w // COLS
    box_h = work_h // ROWS
    
    print(f"\nGrid calculation:")
    print(f"  Usable area: {work_w} x {work_h} px")
    print(f"  Block size: {box_w} x {box_h} px")
    print(f"  Grid: {ROWS} rows x {COLS} cols\n")
    
    # Run OCR
    full_text, word_annotations = ocr_engine.run_ocr(temp_image_path)
    print(f"OCR: {len(word_annotations)} word annotations\n")
    
    # Find all EPICs
    epic_positions = []
    
    for ann in word_annotations[1:]:  # Skip first (full text)
        word = ann.description
        clean = re.sub(r'[^A-Za-z0-9]', '', word).upper()
        
        # Check if it matches EPIC pattern
        if re.match(r'^[A-Z]{3}[0-9]{7}$', clean):
            vertices = ann.bounding_poly.vertices
            y_coords = [v.y for v in vertices]
            x_coords = [v.x for v in vertices]
            y_center = sum(y_coords) / len(y_coords)
            x_center = sum(x_coords) / len(x_coords)
            
            # Calculate which grid cell this EPIC belongs to
            rel_x = x_center - L
            rel_y = y_center - T
            
            c = int(rel_x / box_w)
            r = int(rel_y / box_h)
            
            # Clamp to grid bounds
            c = max(0, min(c, COLS - 1))
            r = max(0, min(r, ROWS - 1))
            
            epic_positions.append({
                'epic': clean,
                'x': x_center,
                'y': y_center,
                'row': r,
                'col': c,
                'grid_pos': f"[{r},{c}]"
            })
    
    # Sort by row, then column
    epic_positions.sort(key=lambda e: (e['row'], e['col']))
    
    print(f"Found {len(epic_positions)} EPICs\n")
    print("=" * 80)
    print("EPIC → Grid Cell Mapping:")
    print("=" * 80)
    
    for ep in epic_positions:
        print(f"{ep['epic']}  →  Block{ep['grid_pos']}  (y={ep['y']:.0f}, x={ep['x']:.0f})")
    
    # Check for duplicate assignments
    print(f"\n" + "=" * 80)
    print("Grid cell occupancy:")
    print("=" * 80)
    
    from collections import defaultdict
    grid_map = defaultdict(list)
    
    for ep in epic_positions:
        key = f"[{ep['row']},{ep['col']}]"
        grid_map[key].append(ep['epic'])
    
    empty_cells = []
    multi_cells = []
    
    for r in range(ROWS):
        for c in range(COLS):
            key = f"[{r},{c}]"
            epics = grid_map.get(key, [])
            
            if len(epics) == 0:
                empty_cells.append(key)
            elif len(epics) > 1:
                multi_cells.append((key, epics))
            elif len(epics) == 1:
                print(f"✅ Block{key}: {epics[0]}")
    
    if empty_cells:
        print(f"\n❌ Empty cells ({len(empty_cells)}):")
        for cell in empty_cells:
            print(f"   {cell}")
    
    if multi_cells:
        print(f"\n⚠️ Cells with multiple EPICs:")
        for cell, epics in multi_cells:
            print(f"   {cell}: {', '.join(epics)}")
    
    pdf.close()
    print(f"\n✅ Grid assignment check complete!")

if __name__ == '__main__':
    check_epic_grid_assignment()
