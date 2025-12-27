#!/usr/bin/env python3
"""
Debug AC Wise EPIC extraction by examining individual block contents.
Compare with ZP Boothwise methodology which achieves 100% accuracy.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from backend.api import API
from backend.parser import parse_gcv_blocks
from backend.ocr_engine import OCREngine
import fitz
import re

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-cloud-vision-key.json'

def debug_ac_wise_blocks():
    """Debug AC Wise block extraction to find missing EPICs"""
    
    # Initialize
    api = API()
    api.set_template('ac_wise_low_quality')
    ocr_engine = OCREngine()
    
    print(f"✅ Template loaded: ac_wise_low_quality")
    print(f"   Margins: L={api.template['left']}, R={api.template['right']}, "
          f"T={api.template['top']}, B={api.template['bottom']}")
    print(f"   Grid: {api.template['rows']}x{api.template['cols']}")
    
    # Load sample PDF
    pdf_path = 'samples/ACWise_LowData Quality/2024-EROLLGEN-S13-72-FinalRoll-Revision2-MAR-01.pdf'
    print(f"\n📄 Testing: {pdf_path}")
    
    pdf = fitz.open(pdf_path)
    page_num = 2  # Page 3 (0-indexed)
    
    print(f"\n🧪 Analyzing page {page_num + 1}...\n")
    
    # Render page to image
    page = pdf[page_num]
    zoom = 300 / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    
    temp_dir = 'temp'
    os.makedirs(temp_dir, exist_ok=True)
    temp_image_path = os.path.join(temp_dir, f'ac_wise_debug_page{page_num + 1}.jpg')
    pix.save(temp_image_path, output="jpeg", jpg_quality=95)
    
    image_W, image_H = pix.width, pix.height
    print(f"Page dimensions: {image_W} x {image_H} px")
    
    # Run OCR
    full_text, word_annotations = ocr_engine.run_ocr(temp_image_path)
    print(f"OCR: {len(word_annotations)} word annotations\n")
    
    # Parse into blocks using template
    parsed = parse_gcv_blocks(word_annotations, image_W, image_H, api.template)
    blocks = parsed.get('blocks', [])
    
    print(f"Parsed into {len(blocks)} blocks ({api.template['rows']}x{api.template['cols']} grid)\n")
    print("=" * 80)
    
    # Check each block for EPIC presence
    epic_pattern = re.compile(r'[A-Z]{3}[0-9]{7}', re.IGNORECASE)
    
    blocks_with_epics = 0
    blocks_without_epics = []
    
    for block in blocks:
        r, c = block['r'], block['c']
        text = block['text']
        
        # Look for EPIC in block text
        epic_match = epic_pattern.search(text)
        
        if epic_match:
            blocks_with_epics += 1
            epic_text = epic_match.group(0)
            # Show first few blocks with EPICs
            if blocks_with_epics <= 3:
                lines = text.split('\n')[:3]
                preview = ' | '.join(lines)[:60]
                print(f"✅ Block[{r},{c}]: EPIC={epic_text} | {preview}...")
        else:
            blocks_without_epics.append((r, c, text))
    
    print(f"\n{'=' * 80}")
    print(f"\n📊 Summary:")
    print(f"   Blocks with EPIC: {blocks_with_epics}/{len(blocks)}")
    print(f"   Blocks without EPIC: {len(blocks_without_epics)}/{len(blocks)}")
    
    if blocks_without_epics:
        print(f"\n❌ Blocks missing EPIC:")
        for r, c, text in blocks_without_epics[:5]:  # Show first 5
            lines = text.split('\n')
            preview = ' | '.join(lines[:3])[:80]
            word_count = len(text.split())
            print(f"\n   Block[{r},{c}] ({word_count} words):")
            print(f"      {preview}")
            if len(lines) > 3:
                print(f"      ... ({len(lines)} total lines)")
    
    # Now search for ALL EPICs in the full page OCR (not grid-based)
    print(f"\n{'=' * 80}")
    print(f"\n🔍 Full-page EPIC scan (non-grid):")
    all_epics = []
    
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
            
            all_epics.append({
                'epic': clean,
                'x': x_center,
                'y': y_center
            })
    
    all_epics.sort(key=lambda e: (e['y'], e['x']))
    
    print(f"   Found {len(all_epics)} EPICs in full-page scan")
    print(f"   Expected: 30 EPICs (for 10x3 grid)")
    print(f"   Difference: {30 - len(all_epics)} EPICs missing from OCR")
    
    if len(all_epics) < 30:
        print(f"\n⚠️ OCR itself is not detecting all EPICs!")
        print(f"   This could be due to:")
        print(f"   - Low image quality (as template name suggests)")
        print(f"   - EPICs too faint/small for OCR to recognize")
        print(f"   - EPIC text corrupted or obscured in scan")
    
    print(f"\n{'=' * 80}")
    print(f"\n💡 Recommendation:")
    if len(all_epics) >= blocks_with_epics:
        print(f"   Grid alignment issue detected!")
        print(f"   - Full-page scan found {len(all_epics)} EPICs")
        print(f"   - But only {blocks_with_epics} were assigned to blocks")
        print(f"   - Check if TOP margin is cutting off EPICs")
        print(f"   - EPICs should be at the TOP of each voter block")
    else:
        print(f"   OCR quality issue detected!")
        print(f"   - Only {len(all_epics)} EPICs detected by OCR (missing {30 - len(all_epics)})")
        print(f"   - This is inherent to the 'Low Quality Data' source")
        print(f"   - Consider image preprocessing or higher DPI")
    
    pdf.close()
    print(f"\n✅ Debug analysis complete!")

if __name__ == '__main__':
    debug_ac_wise_blocks()
