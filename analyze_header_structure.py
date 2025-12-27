#!/usr/bin/env python3
"""
Analyze header structure in ZP Boothwise PDF to understand the page-level context block
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from backend.ocr_engine import OCREngine
import fitz

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-cloud-vision-key.json'

def analyze_header():
    """Analyze the top-left header block on a voter data page"""
    
    ocr_engine = OCREngine()
    
    # Load ZP Boothwise PDF
    pdf_path = 'samples/Zp_Boothwise/BoothList_Division_33_Booth_6_A4 राजोली.pdf'
    pdf = fitz.open(pdf_path)
    
    print(f"📄 PDF has {len(pdf)} pages\n")
    
    # Try page with voter data (skip cover pages)
    page_num = 5  # Page 6 (0-indexed)
    
    # Render full page
    page = pdf[page_num]
    zoom = 300 / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    
    temp_dir = 'temp'
    os.makedirs(temp_dir, exist_ok=True)
    temp_image_path = os.path.join(temp_dir, 'header_analysis_full.jpg')
    pix.save(temp_image_path, output="jpeg", jpg_quality=95)
    
    image_W, image_H = pix.width, pix.height
    print(f"Full page dimensions: {image_W} x {image_H} px")
    
    # Run OCR on full page
    print("\n🔍 Running OCR on full page...")
    _, word_annotations = ocr_engine.run_ocr(temp_image_path)
    
    if not word_annotations or len(word_annotations) <= 1:
        print("❌ No OCR results")
        return
    
    print(f"✅ Found {len(word_annotations) - 1} word annotations\n")
    
    # Analyze words in top region (first 500 pixels)
    header_region_height = 500
    print(f"📋 Words in top {header_region_height}px (potential header region):")
    print("=" * 80)
    
    header_words = []
    for annotation in word_annotations[1:]:  # Skip first (full text)
        word = annotation.description
        
        # Handle both text_annotations and full_text_annotation formats
        if hasattr(annotation, 'bounding_box'):
            vertices = annotation.bounding_box.vertices
        elif hasattr(annotation, 'bounding_poly'):
            vertices = annotation.bounding_poly.vertices
        else:
            continue
        
        y_coords = [v.y for v in vertices]
        x_coords = [v.x for v in vertices]
        y_center = sum(y_coords) / len(y_coords)
        x_center = sum(x_coords) / len(x_coords)
        
        if y_center < header_region_height:
            header_words.append({
                'word': word,
                'x': x_center,
                'y': y_center,
                'x_min': min(x_coords),
                'x_max': max(x_coords),
                'y_min': min(y_coords),
                'y_max': max(y_coords)
            })
    
    # Sort by Y then X
    header_words.sort(key=lambda w: (w['y'], w['x']))
    
    # Group by lines (words with similar Y coordinates)
    lines = []
    current_line = []
    last_y = -1
    y_threshold = 20  # pixels
    
    for word_data in header_words:
        if last_y == -1 or abs(word_data['y'] - last_y) < y_threshold:
            current_line.append(word_data)
            last_y = word_data['y']
        else:
            if current_line:
                lines.append(current_line)
            current_line = [word_data]
            last_y = word_data['y']
    
    if current_line:
        lines.append(current_line)
    
    print(f"Found {len(lines)} lines in header region:\n")
    
    for i, line in enumerate(lines, 1):
        line_text = ' '.join([w['word'] for w in line])
        y_avg = sum(w['y'] for w in line) / len(line)
        x_min = min(w['x_min'] for w in line)
        x_max = max(w['x_max'] for w in line)
        print(f"Line {i} (y≈{y_avg:.0f}px, x={x_min:.0f}-{x_max:.0f}): {line_text}")
    
    # Identify potential header block (left-aligned, top region, containing keywords)
    print("\n" + "=" * 80)
    print("🎯 Identifying header block (left-aligned, containing admin keywords):")
    print("=" * 80)
    
    keywords = ['जिल्हा', 'जिला', 'District', 'परिषद', 'Parishad', 'तालुका', 'Taluka', 
                'विभाग', 'Vibhag', 'मतदान', 'केंद्र', 'Booth', 'Ward', 'कार्यालय', 'Office']
    
    left_margin = 300  # Pixels - left-aligned threshold
    
    header_lines = []
    for i, line in enumerate(lines[:15], 1):  # Check first 15 lines
        line_text = ' '.join([w['word'] for w in line])
        x_min = min(w['x_min'] for w in line)
        x_max = max(w['x_max'] for w in line)
        y_avg = sum(w['y'] for w in line) / len(line)
        
        # Check if left-aligned
        is_left_aligned = x_min < left_margin
        
        # Check if contains keywords
        has_keyword = any(kw in line_text for kw in keywords)
        
        # Centered text usually spans most of the page width
        is_centered = (x_max - x_min) > (image_W * 0.6)
        
        marker = ""
        if is_left_aligned and not is_centered:
            marker = "✅ LEFT-ALIGNED"
            if has_keyword:
                marker += " + KEYWORD"
                header_lines.append((i, y_avg, line_text))
        elif is_centered:
            marker = "❌ CENTERED (skip)"
        
        print(f"{i:2d}. [{marker:25s}] (y≈{y_avg:.0f}, x={x_min:.0f}-{x_max:.0f}): {line_text}")
    
    print("\n" + "=" * 80)
    print("📦 Extracted Header Block:")
    print("=" * 80)
    
    if header_lines:
        for line_num, y_pos, text in header_lines:
            print(f"  {text}")
        
        print("\n" + "=" * 80)
        print("📍 Header Bounding Box:")
        print("=" * 80)
        
        # Calculate bounding box for header
        if header_lines:
            all_header_words = []
            for line in lines[:len(header_lines)]:
                for w in line:
                    x_min_w = w['x_min']
                    if x_min_w < left_margin:
                        all_header_words.append(w)
            
            if all_header_words:
                header_x_min = min(w['x_min'] for w in all_header_words)
                header_x_max = max(w['x_max'] for w in all_header_words)
                header_y_min = min(w['y_min'] for w in all_header_words)
                header_y_max = max(w['y_max'] for w in all_header_words)
                
                print(f"X: {header_x_min:.0f} - {header_x_max:.0f}px")
                print(f"Y: {header_y_min:.0f} - {header_y_max:.0f}px")
                print(f"Width: {header_x_max - header_x_min:.0f}px")
                print(f"Height: {header_y_max - header_y_min:.0f}px")
    else:
        print("⚠️ No header lines detected with keywords")
    
    print("\n✅ Analysis complete!")

if __name__ == '__main__':
    analyze_header()
