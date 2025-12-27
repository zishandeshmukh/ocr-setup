"""
Calibration Tool - AC Wise Low Quality Template
Analyzes PDF layout to determine optimal template coordinates
"""
import fitz  # PyMuPDF
import os
from PIL import Image as PILImage
import json

def calibrate_ac_wise_template():
    """Analyze AC Wise PDF to measure template coordinates"""
    
    pdf_path = r'U:\Downloads\python-voter-ocr\python-voter-ocr\samples\ACWise_LowData Quality\2024-EROLLGEN-S13-72-FinalRoll-Revision2-MAR-01.pdf'
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    print("📄 Opening AC Wise PDF for calibration...")
    pdf_doc = fitz.open(pdf_path)
    
    # Get first page
    page = pdf_doc[0]
    page_rect = page.rect
    page_width = page_rect.width
    page_height = page_rect.height
    
    print(f"\n📐 Page Dimensions (72 DPI):")
    print(f"   Width: {page_width}")
    print(f"   Height: {page_height}")
    
    # Render at 300 DPI for analysis
    zoom = 300 / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    
    img_width = pix.width
    img_height = pix.height
    
    print(f"\n🖼️  Image Dimensions (300 DPI):")
    print(f"   Width: {img_width}")
    print(f"   Height: {img_height}")
    
    # Save preview image
    preview_path = r'U:\Downloads\python-voter-ocr\python-voter-ocr\samples\ACWise_LowData Quality\preview.jpg'
    pix.save(preview_path, output='jpeg', jpg_quality=90)
    print(f"\n✅ Preview saved: {preview_path}")
    
    # Based on visual inspection from screenshot:
    # Layout: 3 columns x ~6 rows per page
    # Each voter box contains: number, name (Marathi), age, relation, photo
    
    # Estimate margins (pixels at 300 DPI)
    # Looking at the screenshot, margins appear to be roughly:
    left_margin = int(img_width * 0.02)      # ~2% from left
    right_margin = int(img_width * 0.02)     # ~2% from right
    top_margin = int(img_height * 0.08)      # ~8% from top (header space)
    bottom_margin = int(img_height * 0.05)   # ~5% from bottom
    
    # Content area
    content_width = img_width - left_margin - right_margin
    content_height = img_height - top_margin - bottom_margin
    
    cols = 3
    rows = 6  # Estimate based on screenshot
    
    cell_width = content_width / cols
    cell_height = content_height / rows
    
    print(f"\n📊 Layout Analysis:")
    print(f"   Columns: {cols}")
    print(f"   Rows: {rows}")
    print(f"   Cell Width: {cell_width:.0f}")
    print(f"   Cell Height: {cell_height:.0f}")
    
    # Convert to percentage coordinates (for template config)
    # Since parser uses percentage-based coordinates
    left_pct = int((left_margin / img_width) * 100)
    right_pct = int((right_margin / img_width) * 100)
    top_pct = int((top_margin / img_height) * 100)
    bottom_pct = int((bottom_margin / img_height) * 100)
    
    template = {
        'name': 'AC Wise Low Quality',
        'left': left_pct,
        'right': right_pct,
        'top': top_pct,
        'bottom': bottom_pct,
        'rows': rows,
        'cols': cols,
        'photo_excl_width': 0,
        'notes': 'Calibrated from AC Wise PDF at 300 DPI'
    }
    
    print(f"\n✨ Recommended Template:")
    print(json.dumps(template, indent=2))
    
    pdf_doc.close()
    return template

if __name__ == '__main__':
    calibrate_ac_wise_template()
