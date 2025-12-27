"""
Empirical calibration script for ZP Boothwise template.
Analyzes sample PDF pages to derive optimal grid margins.
"""

import fitz
import os
from backend.ocr_engine import OCREngine
from collections import defaultdict
import io

def analyze_zp_boothwise_layout():
    """
    Analyze ZP Boothwise sample PDF to determine:
    1. Grid dimensions (rows × columns)
    2. Optimal margins (left, right, top, bottom) at 300 DPI
    """
    
    # Find the sample PDF
    sample_dir = "samples/Zp_Boothwise"
    pdf_files = [f for f in os.listdir(sample_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        print("❌ No PDF found in samples/Zp_Boothwise/")
        return
    
    pdf_path = os.path.join(sample_dir, pdf_files[0])
    print(f"📄 Analyzing: {pdf_files[0]}")
    
    pdf = fitz.open(pdf_path)
    total_pages = pdf.page_count
    print(f"📊 Total pages: {total_pages}")
    
    # Select representative pages (skip first page which is often a cover)
    # Analyze middle pages with typical voter blocks
    pages_to_analyze = []
    if total_pages > 10:
        pages_to_analyze = [3, 5, 7, 9, 11]  # Sample various middle pages
    elif total_pages > 5:
        pages_to_analyze = [2, 3, 4, 5]
    else:
        pages_to_analyze = list(range(1, total_pages))
    
    pages_to_analyze = [p for p in pages_to_analyze if p < total_pages]
    
    print(f"🔍 Analyzing pages: {pages_to_analyze}")
    
    all_x_centers = []
    all_y_centers = []
    all_word_data = []
    
    ocr_engine = OCREngine()
    
    for page_num in pages_to_analyze:
        print(f"\n📄 Processing page {page_num + 1}...")
        
        page = pdf[page_num]
        pix = page.get_pixmap(dpi=300)
        img_bytes = pix.tobytes("png")
        
        # Save temporarily for OCR
        temp_img = f"temp_page_{page_num}.png"
        pix.save(temp_img)
        
        # Perform OCR using document_text_detection for full layout
        try:
            with io.open(temp_img, 'rb') as image_file:
                content = image_file.read()
            
            from google.cloud import vision
            image = vision.Image(content=content)
            
            # Call DOCUMENT_TEXT_DETECTION
            response = ocr_engine.client.document_text_detection(
                image=image,
                image_context={'language_hints': ['mr', 'hi', 'en']}
            )
        finally:
            # Clean up temp file
            if os.path.exists(temp_img):
                os.remove(temp_img)
        
        if not response.full_text_annotation:
            print(f"  ⚠️  No OCR results for page {page_num + 1}")
            continue
        
        page_text = response.full_text_annotation.text
        print(f"  ✅ OCR extracted {len(page_text)} characters")
        
        # Collect word center positions
        for page_block in response.full_text_annotation.pages:
            for block in page_block.blocks:
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        # Get bounding box
                        vertices = word.bounding_box.vertices
                        if len(vertices) < 4:
                            continue
                        
                        x_coords = [v.x for v in vertices]
                        y_coords = [v.y for v in vertices]
                        
                        x_center = sum(x_coords) / len(x_coords)
                        y_center = sum(y_coords) / len(y_coords)
                        
                        word_text = ''.join([symbol.text for symbol in word.symbols])
                        
                        all_x_centers.append(x_center)
                        all_y_centers.append(y_center)
                        all_word_data.append({
                            'text': word_text,
                            'x': x_center,
                            'y': y_center,
                            'page': page_num
                        })
    
    pdf.close()
    
    if not all_x_centers:
        print("\n❌ No word data collected")
        return
    
    print(f"\n📊 Collected {len(all_x_centers)} words from {len(pages_to_analyze)} pages")
    
    # Compute percentile-based margins
    all_x_centers.sort()
    all_y_centers.sort()
    
    # Use 2nd and 98th percentiles for X (left/right margins)
    # Use 5th and 95th percentiles for Y (top/bottom margins) - adjusted for more conservative bottom
    x_min = all_x_centers[int(len(all_x_centers) * 0.02)]
    x_max = all_x_centers[int(len(all_x_centers) * 0.98)]
    y_min = all_y_centers[int(len(all_y_centers) * 0.05)]
    y_max = all_y_centers[int(len(all_y_centers) * 0.95)]  # 95th instead of 98th
    
    # Get page dimensions at 300 DPI
    page = fitz.open(pdf_path)[0]
    page_width_pts = page.rect.width
    page_height_pts = page.rect.height
    
    # Convert points to pixels at 300 DPI (1 point = 300/72 pixels)
    page_width_px = int(page_width_pts * 300 / 72)
    page_height_px = int(page_height_pts * 300 / 72)
    
    print(f"\n📐 Page dimensions at 300 DPI: {page_width_px} × {page_height_px} px")
    
    # Calculate margins (ensure non-negative)
    left_margin = int(x_min)
    right_margin = max(10, page_width_px - int(x_max))  # Minimum 10px
    top_margin = int(y_min)
    bottom_margin = max(10, page_height_px - int(y_max))  # Minimum 10px
    
    print(f"\n🎯 Derived Margins:")
    print(f"   Left:   {left_margin} px")
    print(f"   Right:  {right_margin} px")
    print(f"   Top:    {top_margin} px")
    print(f"   Bottom: {bottom_margin} px")
    
    # Analyze column distribution to determine grid columns
    content_width = page_width_px - left_margin - right_margin
    
    # Bin words into potential columns
    bins = defaultdict(int)
    bin_width = content_width / 10  # Try 10 bins
    
    for x in all_x_centers:
        if x >= x_min and x <= x_max:
            bin_idx = int((x - x_min) / bin_width)
            bins[bin_idx] += 1
    
    print(f"\n📊 Horizontal word distribution (bins):")
    for i in sorted(bins.keys()):
        bar = '█' * (bins[i] // 10)
        print(f"   Bin {i:2d}: {bins[i]:4d} words {bar}")
    
    # Detect columns by finding peaks
    peak_bins = []
    for i in sorted(bins.keys()):
        if i > 0 and i < max(bins.keys()):
            if bins[i] > bins.get(i-1, 0) and bins[i] > bins.get(i+1, 0):
                if bins[i] > 50:  # Threshold for significant peak
                    peak_bins.append(i)
    
    num_columns = len(peak_bins) if peak_bins else 3  # Default to 3
    
    print(f"\n🔢 Detected {num_columns} columns")
    
    # Estimate rows (assume 10 rows as standard for voter lists)
    num_rows = 10
    
    print(f"\n✅ Suggested Template Configuration:")
    print(f"   Grid: {num_columns} columns × {num_rows} rows")
    print(f"   Margins: L={left_margin}, R={right_margin}, T={top_margin}, B={bottom_margin}")
    print(f"\n📝 Add to api.py load_template():")
    print(f"""
    elif template_name == 'zp_boothwise':
        return {{
            'name': 'zp_boothwise',
            'rows': {num_rows},
            'cols': {num_columns},
            'margin_left': {left_margin},
            'margin_right': {right_margin},
            'margin_top': {top_margin},
            'margin_bottom': {bottom_margin},
            'dpi': 300
        }}
    """)
    
    return {
        'left_margin': left_margin,
        'right_margin': right_margin,
        'top_margin': top_margin,
        'bottom_margin': bottom_margin,
        'num_columns': num_columns,
        'num_rows': num_rows,
        'page_width': page_width_px,
        'page_height': page_height_px
    }

if __name__ == "__main__":
    result = analyze_zp_boothwise_layout()
