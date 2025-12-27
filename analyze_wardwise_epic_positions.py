"""
Detailed EPIC position analysis for Wardwise to determine exact row/column structure.
"""

import os
import fitz
from backend.ocr_engine import OCREngine
import re

def analyze_wardwise_epic_positions():
    """Find all EPICs and analyze their exact positions"""
    
    sample_dir = "samples/WardWiseData"
    pdf_files = [f for f in os.listdir(sample_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        print("ERROR: No PDF found")
        return
    
    pdf_path = os.path.join(sample_dir, pdf_files[0])
    print(f"Analyzing: {pdf_files[0]}\n")
    
    pdf = fitz.open(pdf_path)
    
    # Test page 3 (0-indexed = 2)
    test_page = 2
    
    print(f"Analyzing page {test_page + 1}...\n")
    
    page = pdf[test_page]
    pix = page.get_pixmap(dpi=300)
    
    page_width_px = int(page.rect.width * 300 / 72)
    page_height_px = int(page.rect.height * 300 / 72)
    
    temp_img = "temp_wardwise_epic.png"
    pix.save(temp_img)
    
    ocr_engine = OCREngine()
    
    try:
        full_text, word_annotations = ocr_engine.run_ocr(temp_img)
        
        # Find all EPIC-like tokens
        epic_pattern = re.compile(r'^[A-Z]{3}[0-9]{7}$')
        
        epic_positions = []
        
        for ann in word_annotations[1:]:
            word = ann.description
            clean = re.sub(r'[^A-Za-z0-9]', '', word).upper()
            
            if epic_pattern.match(clean):
                vertices = ann.bounding_poly.vertices
                y_coords = [v.y for v in vertices]
                x_coords = [v.x for v in vertices]
                
                y_center = sum(y_coords) / len(y_coords)
                x_center = sum(x_coords) / len(x_coords)
                
                epic_positions.append({
                    'word': word,
                    'x': x_center,
                    'y': y_center
                })
        
        # Sort by Y then X
        epic_positions.sort(key=lambda e: (e['y'], e['x']))
        
        print(f"Total EPICs found: {len(epic_positions)}\n")
        print("All EPIC positions (y, x):")
        print("-" * 60)
        
        for i, epic in enumerate(epic_positions):
            print(f"{i+1:3d}. y={epic['y']:7.1f}  x={epic['x']:7.1f}  | {epic['word']}")
        
        # Analyze Y-spacing
        print(f"\n" + "=" * 60)
        print("Y-spacing between consecutive EPICs:")
        print("=" * 60)
        
        for i in range(1, len(epic_positions)):
            diff = epic_positions[i]['y'] - epic_positions[i-1]['y']
            marker = " <-- NEW ROW" if diff > 100 else ""
            print(f"EPIC {i} -> {i+1}: {diff:6.1f} px{marker}")
        
        # Group EPICs by row (Y proximity)
        rows = []
        current_row = [epic_positions[0]] if epic_positions else []
        
        for i in range(1, len(epic_positions)):
            y_diff = epic_positions[i]['y'] - epic_positions[i-1]['y']
            if y_diff < 50:  # Same row
                current_row.append(epic_positions[i])
            else:  # New row
                rows.append(current_row)
                current_row = [epic_positions[i]]
        
        if current_row:
            rows.append(current_row)
        
        print(f"\n" + "=" * 60)
        print(f"Row structure ({len(rows)} rows detected):")
        print("=" * 60)
        
        for i, row in enumerate(rows):
            y_avg = sum(e['y'] for e in row) / len(row)
            x_positions = sorted([e['x'] for e in row])
            print(f"Row {i+1}: {len(row)} EPICs at y≈{y_avg:.1f}, x=[{', '.join(f'{x:.0f}' for x in x_positions)}]")
        
        # Calculate average column X positions
        if rows:
            print(f"\n" + "=" * 60)
            print("Column analysis:")
            print("=" * 60)
            
            all_x_by_position = [[] for _ in range(max(len(r) for r in rows))]
            
            for row in rows:
                row_sorted = sorted(row, key=lambda e: e['x'])
                for pos, epic in enumerate(row_sorted):
                    if pos < len(all_x_by_position):
                        all_x_by_position[pos].append(epic['x'])
            
            for col_idx, x_list in enumerate(all_x_by_position):
                if x_list:
                    avg_x = sum(x_list) / len(x_list)
                    print(f"Column {col_idx + 1}: avg x={avg_x:.1f} ({len(x_list)} samples)")
        
        print(f"\n" + "=" * 60)
        print(f"Page dimensions: {page_width_px} x {page_height_px} px")
        
        if rows:
            first_row_y = rows[0][0]['y']
            last_row_y = rows[-1][0]['y']
            row_span = last_row_y - first_row_y
            
            if len(rows) > 1:
                avg_row_spacing = row_span / (len(rows) - 1)
                print(f"Row span: {first_row_y:.1f} to {last_row_y:.1f} ({row_span:.1f} px)")
                print(f"Average row spacing: {avg_row_spacing:.1f} px")
        
    finally:
        if os.path.exists(temp_img):
            os.remove(temp_img)
    
    pdf.close()

if __name__ == "__main__":
    analyze_wardwise_epic_positions()
