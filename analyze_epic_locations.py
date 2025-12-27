"""
Analyze EPIC Y-coordinate positions to determine correct row boundaries.
Since EPICs are at the TOP of each voter block, we can use their Y positions
to determine where row boundaries should be.
"""

import os
import fitz
from backend.ocr_engine import OCREngine
from backend.api import load_template
import re

def analyze_epic_locations():
    """Find all EPICs and their Y coordinates to determine row boundaries"""
    
    template = load_template('zp_boothwise')
    print(f"\nCurrent ZP Boothwise Template:")
    print(f"  Grid: {template['cols']} cols x {template['rows']} rows")
    print(f"  Margins: L={template['left']}, R={template['right']}, T={template['top']}, B={template['bottom']}")
    
    # Find sample PDF
    sample_dir = "samples/Zp_Boothwise"
    pdf_files = [f for f in os.listdir(sample_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        print("ERROR: No PDF found")
        return
    
    pdf_path = os.path.join(sample_dir, pdf_files[0])
    print(f"\nAnalyzing: {pdf_files[0]}")
    
    pdf = fitz.open(pdf_path)
    
    # Test page with content
    test_page = 5
    
    print(f"\nAnalyzing page {test_page + 1}...")
    
    page = pdf[test_page]
    pix = page.get_pixmap(dpi=300)
    
    # Save temporarily
    temp_img = f"temp_epic_loc.png"
    pix.save(temp_img)
    
    ocr_engine = OCREngine()
    
    try:
        # Run OCR
        full_text, word_annotations = ocr_engine.run_ocr(temp_img)
        print(f"  OCR extracted {len(word_annotations)} word annotations")
        
        # Find all EPIC-like tokens and their positions
        epic_pattern = re.compile(r'^[A-Z]{3}[0-9]{7,10}$')
        
        epic_positions = []
        
        for ann in word_annotations[1:]:  # Skip first (full text)
            word = ann.description
            
            # Clean and check if it looks like an EPIC
            clean = re.sub(r'[^A-Za-z0-9]', '', word).upper()
            if epic_pattern.match(clean):
                vertices = ann.bounding_poly.vertices
                y_coords = [v.y for v in vertices]
                x_coords = [v.x for v in vertices]
                
                y_center = sum(y_coords) / len(y_coords)
                x_center = sum(x_coords) / len(x_coords)
                
                epic_positions.append({
                    'word': word,
                    'clean': clean,
                    'x': x_center,
                    'y': y_center,
                    'y_min': min(y_coords),
                    'y_max': max(y_coords)
                })
        
        print(f"\nFound {len(epic_positions)} EPIC-like tokens")
        
        if not epic_positions:
            print("ERROR: No EPICs detected!")
            return
        
        # Sort by Y position
        epic_positions.sort(key=lambda e: e['y'])
        
        print(f"\nEPIC Y-positions (sorted):")
        for i, epic in enumerate(epic_positions):
            print(f"  {i+1:2d}. y={epic['y']:7.1f} (y_min={epic['y_min']:7.1f}, y_max={epic['y_max']:7.1f}) x={epic['x']:7.1f} | {epic['word']}")
        
        # Calculate Y differences between consecutive EPICs
        print(f"\nY-spacing between consecutive EPICs:")
        y_diffs = []
        for i in range(1, len(epic_positions)):
            diff = epic_positions[i]['y'] - epic_positions[i-1]['y']
            y_diffs.append(diff)
            print(f"  EPIC {i} -> {i+1}: {diff:.1f} px")
        
        if y_diffs:
            avg_spacing = sum(y_diffs) / len(y_diffs)
            print(f"\n  Average Y-spacing: {avg_spacing:.1f} px")
        
        # Get page dimensions
        page_width_px = int(page.rect.width * 300 / 72)
        page_height_px = int(page.rect.height * 300 / 72)
        
        print(f"\nPage dimensions: {page_width_px} x {page_height_px} px")
        
        # Calculate what the row height should be
        # If we have N EPICs and they span from first to last
        if len(epic_positions) >= 2:
            first_y = epic_positions[0]['y']
            last_y = epic_positions[-1]['y']
            y_span = last_y - first_y
            
            # If we have 20 EPICs in 10 rows, 3 columns
            # They should be distributed across rows
            print(f"\nEPIC Y-span: {first_y:.1f} to {last_y:.1f} ({y_span:.1f} px)")
            
            # Current template calculation
            current_top = template['top']
            current_bottom = template['bottom']
            current_work_h = page_height_px - current_top - current_bottom
            current_row_h = current_work_h / template['rows']
            
            print(f"\nCurrent template:")
            print(f"  Work height: {current_work_h} px")
            print(f"  Row height: {current_row_h:.1f} px")
            print(f"  First EPIC should be at y={current_top + current_row_h * 0.1:.1f}")
            print(f"  First EPIC actually at y={first_y:.1f}")
            print(f"  Difference: {first_y - (current_top + current_row_h * 0.1):.1f} px")
            
            # Recommended top margin
            # EPICs should be ~10% down from top of each row
            # So first EPIC y-position tells us where first row starts
            recommended_top = int(first_y - current_row_h * 0.1)
            
            print(f"\nRecommended adjustments:")
            print(f"  Suggested top margin: {recommended_top} px (current: {current_top} px)")
            
            # Check if row height is correct
            if len(y_diffs) > 0:
                # Group EPICs by column (3 columns, so every 3rd EPIC should have larger gap)
                print(f"\nAnalyzing row structure:")
                print(f"  If 3 columns, EPICs 1-3 in row 1, 4-6 in row 2, etc.")
                
                for i in range(0, len(epic_positions), 3):
                    row_epics = epic_positions[i:i+3]
                    if len(row_epics) >= 2:
                        row_y_avg = sum(e['y'] for e in row_epics) / len(row_epics)
                        row_y_range = max(e['y'] for e in row_epics) - min(e['y'] for e in row_epics)
                        print(f"  Row {i//3 + 1}: y_avg={row_y_avg:.1f}, y_range={row_y_range:.1f} px")
        
    finally:
        if os.path.exists(temp_img):
            os.remove(temp_img)
    
    pdf.close()

if __name__ == "__main__":
    analyze_epic_locations()
