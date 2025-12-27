"""
Quick test script for ZP Boothwise template extraction.
Tests block detection and record count without launching full UI.
"""

import os
import fitz
from backend.ocr_engine import OCREngine
from backend.parser import parse_gcv_blocks, extract_voter_from_block
from backend.api import load_template

def test_zp_boothwise():
    """Test ZP Boothwise template on sample PDF"""
    
    # Load template
    template = load_template('zp_boothwise')
    print(f"\n📐 Template: ZP Boothwise")
    print(f"   Grid: {template['cols']} cols × {template['rows']} rows")
    print(f"   Margins: L={template['left']}, R={template['right']}, T={template['top']}, B={template['bottom']}")
    
    # Find sample PDF
    sample_dir = "samples/Zp_Boothwise"
    pdf_files = [f for f in os.listdir(sample_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        print("❌ No PDF found")
        return
    
    pdf_path = os.path.join(sample_dir, pdf_files[0])
    print(f"\n📄 Testing: {pdf_files[0]}")
    
    pdf = fitz.open(pdf_path)
    total_pages = pdf.page_count
    print(f"📊 Total pages: {total_pages}")
    
    # Test first few content pages (skip page 0 if it's a cover)
    test_pages = [3, 4, 5]  # Pages 4, 5, 6 (0-indexed)
    
    ocr_engine = OCREngine()
    total_voters = 0
    
    for page_num in test_pages:
        if page_num >= total_pages:
            continue
            
        print(f"\n📄 Processing page {page_num + 1}...")
        
        # Render page at 300 DPI
        page = pdf[page_num]
        pix = page.get_pixmap(dpi=300)
        
        # Save temporarily for OCR
        temp_img = f"temp_test_page_{page_num}.png"
        pix.save(temp_img)
        
        try:
            # Run OCR
            full_text, word_annotations = ocr_engine.run_ocr(temp_img)
            print(f"   ✅ OCR extracted {len(full_text)} characters")
            
            # Check if page should be skipped (cover/index/summary)
            if len(full_text) < 500:  # Too little text
                print(f"   ⚠️  Skipping page (low text content: {len(full_text)} chars)")
                continue
            
            # Parse into grid blocks
            page_width_px = int(page.rect.width * 300 / 72)
            page_height_px = int(page.rect.height * 300 / 72)
            
            # Use full_text_annotation for block parsing
            from google.cloud import vision
            import io
            
            with io.open(temp_img, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            response = ocr_engine.client.document_text_detection(
                image=image,
                image_context={'language_hints': ['mr', 'hi', 'en']}
            )
            
            blocks = parse_gcv_blocks(
                response,
                page_width_px,
                page_height_px,
                template['rows'],
                template['cols'],
                template['left'],
                template['right'],
                template['top'],
                template['bottom']
            )
            
            print(f"   📦 Grid blocks parsed: {len(blocks)} blocks")
            
            # Extract voters from blocks
            page_voters = 0
            for i, block in enumerate(blocks):
                voter = extract_voter_from_block(
                    block_text=block['text'],
                    words=block.get('words', []),
                    page_num=page_num + 1,
                    block_index=i
                )
                
                if voter:
                    page_voters += 1
                    
                    # Show first few extractions for verification
                    if page_voters <= 3:
                        print(f"   ✅ Voter {page_voters}: EPIC={voter.get('epic_no', 'N/A')[:12]}, "
                              f"Name={voter.get('name_marathi', 'N/A')[:20]}, "
                              f"Age={voter.get('age', 'N/A')}, Gender={voter.get('gender', 'N/A')}")
            
            print(f"   📊 Extracted {page_voters} voters from page {page_num + 1}")
            total_voters += page_voters
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_img):
                os.remove(temp_img)
    
    pdf.close()
    
    print(f"\n✅ Test Complete")
    print(f"📊 Total voters extracted from {len(test_pages)} pages: {total_voters}")
    print(f"📈 Average per page: {total_voters / len(test_pages):.1f}")
    
    # Expected: ~8-12 voters per page for 2-column × 10-row layout (20 blocks, ~50% occupancy)
    expected_range = (len(test_pages) * 6, len(test_pages) * 14)
    if expected_range[0] <= total_voters <= expected_range[1]:
        print(f"✅ Extraction count looks reasonable (expected {expected_range[0]}-{expected_range[1]})")
    else:
        print(f"⚠️  Extraction count outside expected range ({expected_range[0]}-{expected_range[1]})")

if __name__ == "__main__":
    test_zp_boothwise()
