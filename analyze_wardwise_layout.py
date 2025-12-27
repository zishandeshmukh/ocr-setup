"""
Empirical calibration script for Wardwise template.
Analyzes EPIC positions to determine optimal grid margins and row/column layout.
"""

import os
import fitz
from backend.ocr_engine import OCREngine
from backend.api import load_template
import re
from collections import defaultdict

def analyze_wardwise_layout():
    """Analyze Wardwise sample PDF to determine optimal template configuration"""
    
    print("\n=== Wardwise Template Calibration ===\n")
    
    # Find sample PDF
    sample_dir = "samples/WardWiseData"
    pdf_files = [f for f in os.listdir(sample_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        print("ERROR: No PDF found")
        return
    
    pdf_path = os.path.join(sample_dir, pdf_files[0])
    print(f"Sample PDF: {pdf_files[0]}")
    
    pdf = fitz.open(pdf_path)
    total_pages = pdf.page_count
    print(f"Total pages: {total_pages}")
    
    # Analyze a content page (skip first which might be cover)
    test_page = 2 if total_pages > 2 else 1
    
    print(f"\nAnalyzing page {test_page + 1}...\n")
    
    page = pdf[test_page]
    pix = page.get_pixmap(dpi=300)
    
    # Get page dimensions at 300 DPI
    page_width_px = int(page.rect.width * 300 / 72)
    page_height_px = int(page.rect.height * 300 / 72)
    print(f"Page dimensions at 300 DPI: {page_width_px} x {page_height_px} px")
    
    # Save temporarily for OCR
    temp_img = "temp_wardwise_analysis.png"
    pix.save(temp_img)
    
    ocr_engine = OCREngine()
    
    try:
        # Run OCR
        full_text, word_annotations = ocr_engine.run_ocr(temp_img)
        print(f"OCR extracted {len(word_annotations)} word annotations")
        
        # Find all EPIC-like tokens (3 letters + 7 digits = 10 chars)
        epic_pattern = re.compile(r'^[A-Z]{3}[0-9]{7}$')
        
        epic_positions = []
        all_word_centers = []
        
        for ann in word_annotations[1:]:  # Skip first (full text)
            word = ann.description
            vertices = ann.bounding_poly.vertices
            
            if len(vertices) < 4:
                continue
            
            y_coords = [v.y for v in vertices]
            x_coords = [v.x for v in vertices]
            
            y_center = sum(y_coords) / len(y_coords)
            x_center = sum(x_coords) / len(x_coords)
            
            all_word_centers.append((x_center, y_center))
            
            # Check if it looks like an EPIC
            clean = re.sub(r'[^A-Za-z0-9]', '', word).upper()
            if epic_pattern.match(clean):
                epic_positions.append({
                    'word': word,
                    'clean': clean,
                    'x': x_center,
                    'y': y_center,
                    'y_min': min(y_coords),
                    'y_max': max(y_coords)
                })
        
        print(f"\nFound {len(epic_positions)} EPIC tokens")
        
        if len(epic_positions) < 5:
            print("WARNING: Too few EPICs detected. May not be a voter data page.")
        
        # Sort EPICs by Y position
        epic_positions.sort(key=lambda e: e['y'])
        
        print(f"\nEPIC Y-positions (first 10):")
        for i, epic in enumerate(epic_positions[:10]):
            print(f"  {i+1:2d}. y={epic['y']:7.1f} x={epic['x']:7.1f} | {epic['word']}")
        
        # Calculate Y-spacing between consecutive EPICs
        y_diffs = []
        for i in range(1, len(epic_positions)):
            diff = epic_positions[i]['y'] - epic_positions[i-1]['y']
            y_diffs.append(diff)
        
        if y_diffs:
            # Filter out small differences (same row) to get row spacing
            row_spacings = [d for d in y_diffs if d > 50]  # Significant jumps indicate new row
            
            if row_spacings:
                avg_row_spacing = sum(row_spacings) / len(row_spacings)
                print(f"\nAverage row spacing: {avg_row_spacing:.1f} px")
        
        # Analyze column structure using EPIC X-positions
        epic_x_positions = [e['x'] for e in epic_positions]
        epic_x_positions.sort()
        
        # Try to detect columns by clustering X positions
        print(f"\nAnalyzing column structure...")
        print(f"EPIC X-position range: {min(epic_x_positions):.1f} to {max(epic_x_positions):.1f}")
        
        # Bin EPICs by X position to detect columns
        x_bins = defaultdict(int)
        bin_width = (max(epic_x_positions) - min(epic_x_positions)) / 10
        
        for x in epic_x_positions:
            bin_idx = int((x - min(epic_x_positions)) / bin_width) if bin_width > 0 else 0
            x_bins[bin_idx] += 1
        
        print(f"\nEPIC horizontal distribution:")
        for i in sorted(x_bins.keys()):
            bar = '█' * (x_bins[i] // 2)
            print(f"  Bin {i:2d}: {x_bins[i]:3d} EPICs {bar}")
        
        # Detect column count from peaks
        peaks = []
        for i in sorted(x_bins.keys()):
            if i > 0 and i < max(x_bins.keys()):
                if x_bins[i] > x_bins.get(i-1, 0) and x_bins[i] > x_bins.get(i+1, 0):
                    if x_bins[i] > 3:  # Threshold
                        peaks.append(i)
        
        num_columns = len(peaks) if peaks else 3
        print(f"\nDetected columns: {num_columns}")
        
        # Calculate margins using percentiles
        all_word_centers.sort(key=lambda p: p[0])  # Sort by X
        x_centers = [x for x, y in all_word_centers]
        y_centers = [y for x, y in all_word_centers]
        
        x_min = x_centers[int(len(x_centers) * 0.02)]
        x_max = x_centers[int(len(x_centers) * 0.98)]
        y_min = y_centers[int(len(y_centers) * 0.05)]
        y_max = y_centers[int(len(y_centers) * 0.95)]
        
        left_margin = int(x_min)
        right_margin = max(10, page_width_px - int(x_max))
        top_margin = int(y_min)
        bottom_margin = max(10, page_height_px - int(y_max))
        
        print(f"\nDerived Margins (percentile-based):")
        print(f"  Left:   {left_margin} px")
        print(f"  Right:  {right_margin} px")
        print(f"  Top:    {top_margin} px")
        print(f"  Bottom: {bottom_margin} px")
        
        # If we have EPICs, use their positions for more precise top margin
        if epic_positions:
            first_epic_y = epic_positions[0]['y']
            
            # Assume EPICs are ~10% down from top of their row
            # Calculate what top margin would align first row with first EPIC
            if row_spacings:
                row_height = avg_row_spacing
                adjusted_top = int(first_epic_y - row_height * 0.1)
                
                print(f"\nEPIC-based adjustments:")
                print(f"  First EPIC at y={first_epic_y:.1f}")
                print(f"  Suggested top margin: {adjusted_top} px")
                
                top_margin = adjusted_top
        
        # Calculate recommended row count
        work_height = page_height_px - top_margin - bottom_margin
        row_height = work_height / 10  # Assume 10 rows standard
        
        print(f"\n=== Recommended Template Configuration ===")
        print(f"Grid: {num_columns} columns x 10 rows")
        print(f"Margins: L={left_margin}, R={right_margin}, T={top_margin}, B={bottom_margin}")
        print(f"Work height: {work_height} px")
        print(f"Row height: {row_height:.1f} px")
        
        print(f"\nAdd to api.py:")
        print(f"""
'wardwise': {{
    'left': {left_margin},
    'right': {right_margin},
    'top': {top_margin},
    'bottom': {bottom_margin},
    'rows': 10,
    'cols': {num_columns},
    'photo_excl_width': 0,
    'skip_first_pages': 0,
    'skip_last_pages': 0,
    'min_word_annotations': 20,
    'min_valid_blocks_for_page': 2
}}
""")
        
    finally:
        if os.path.exists(temp_img):
            os.remove(temp_img)
    
    pdf.close()

if __name__ == "__main__":
    analyze_wardwise_layout()
