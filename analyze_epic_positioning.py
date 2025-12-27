"""
Analyze EPIC field positioning in ZP Boothwise voter blocks
to understand why EPIC extraction is missing for valid records.
"""

import sys
import io
# Force UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
import fitz
from backend.ocr_engine import OCREngine
from backend.parser import normalize_epic_aggressive, parse_gcv_blocks, extract_voter_from_block
from backend.api import load_template
import re

def analyze_epic_positioning():
    """Analyze EPIC positioning within voter blocks"""
    
    # Load template
    template = load_template('zp_boothwise')
    print(f"\nTemplate: ZP Boothwise")
    print(f"   Grid: {template['cols']} cols x {template['rows']} rows")
    
    # Find sample PDF
    sample_dir = "samples/Zp_Boothwise"
    pdf_files = [f for f in os.listdir(sample_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        print("ERROR: No PDF found")
        return
    
    pdf_path = os.path.join(sample_dir, pdf_files[0])
    print(f"\nAnalyzing ZP Boothwise sample PDF...")
    
    pdf = fitz.open(pdf_path)
    total_pages = pdf.page_count
    
    # Test a content page (skip cover)
    test_page = 5  # Page 6 (0-indexed)
    
    if test_page >= total_pages:
        test_page = 2
    
    print(f"\nAnalyzing page {test_page + 1}...")
    
    page = pdf[test_page]
    pix = page.get_pixmap(dpi=300)
    
    # Save temporarily
    temp_img = f"temp_epic_analysis.png"
    pix.save(temp_img)
    
    ocr_engine = OCREngine()
    
    try:
        # Run OCR
        full_text, word_annotations = ocr_engine.run_ocr(temp_img)
        print(f"   OK: OCR extracted {len(full_text)} characters")
        
        # Parse into blocks
        page_width_px = int(page.rect.width * 300 / 72)
        page_height_px = int(page.rect.height * 300 / 72)
        
        from google.cloud import vision
        import io
        
        with io.open(temp_img, 'rb') as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        response = ocr_engine.client.document_text_detection(
            image=image,
            image_context={'language_hints': ['mr', 'hi', 'en']}
        )
        
        # Use word_annotations for block parsing (consistent with existing code)
        parsed = parse_gcv_blocks(
            word_annotations,
            page_width_px,
            page_height_px,
            template
        )
        
        blocks_list = parsed.get('blocks', [])
        print(f"   Parsed {len(blocks_list)} blocks")
        
        # Analyze blocks with text
        blocks_analyzed = 0
        epics_found = 0
        epics_missing = 0
        
        epic_patterns = [
            r'\b[A-Z]{3}\d{7}\b',
            r'\b[A-Z]{2}\d{8}\b',
            r'\b[A-Z]{3}[\s/-]*\d{7}\b',
            r'\b[A-Z]{3}[A-Z0-9]{1}\d{6}\b',
            r'\b[A-Z]{2,4}[0-9O]{7,8}\b'
        ]
        
        for i, block in enumerate(blocks_list):
            text = block.get('text', '')
            words = block.get('words', [])
            
            if not text.strip() or len(text) < 20:
                continue
            
            blocks_analyzed += 1
            
            # Check if block has typical voter indicators
            has_name = bool(re.search(r'(मतदाराचे|नाव|Name)', text, re.IGNORECASE))
            has_relation = bool(re.search(r'(वडिलांचे|पतीचे|Father|Husband)', text, re.IGNORECASE))
            has_age = bool(re.search(r'(वय|Age)\s*[:\s-]*\d+', text, re.IGNORECASE))
            has_gender = bool(re.search(r'(पुरुष|स्त्री|Male|Female)', text, re.IGNORECASE))
            
            is_likely_voter = (has_name or has_relation) and (has_age or has_gender)
            
            if not is_likely_voter:
                continue
            
            # Use actual extract_voter_from_block function
            voter = extract_voter_from_block(text)
            epic_val = voter.get('epic', '')
            epic_found = bool(epic_val and len(epic_val) >= 9)
            
            if epic_found:
                epics_found += 1
                if epics_found <= 3:
                    print(f"\n   [OK] Block {i}: EPIC Found: {epic_val}")
                    print(f"      Text preview: {text[:100]}")
            else:
                epics_missing += 1
                print(f"\n   [MISSING] Block {i}: EPIC MISSING (likely voter block)")
                print(f"      Text preview: {text[:150]}")
                print(f"      Signals: Name={has_name}, Relation={has_relation}, Age={has_age}, Gender={has_gender}")
                
                # Try to find EPIC-like tokens by position
                print(f"      Word count: {len(words)}")
                if words:
                    # Show first 10 words with positions
                    print(f"      First 10 words (y, x, text):")
                    for j, (y, x, word) in enumerate(words[:10]):
                        print(f"        {j}: ({y}, {x}) = '{word}'")
                    
                    # Look for alphanumeric tokens
                    alphanum_words = [(y, x, w) for y, x, w in words if re.match(r'[A-Za-z0-9]{8,}', w)]
                    if alphanum_words:
                        print(f"      Alphanumeric tokens (8+ chars):")
                        for y, x, w in alphanum_words[:5]:
                            normalized = normalize_epic_aggressive(w)
                            print(f"        ({y}, {x}) = '{w}' -> normalized: '{normalized}'")
        
        print(f"\nSummary:")
        print(f"   Voter-like blocks analyzed: {blocks_analyzed}")
        print(f"   EPICs found: {epics_found}")
        print(f"   EPICs missing: {epics_missing}")
        if blocks_analyzed > 0:
            success_rate = (epics_found / blocks_analyzed) * 100
            print(f"   Success rate: {success_rate:.1f}%")
            if success_rate < 95:
                print(f"   WARNING: Success rate below 95% - EPIC extraction needs improvement")
        
    finally:
        # Clean up
        if os.path.exists(temp_img):
            os.remove(temp_img)
    
    pdf.close()

if __name__ == "__main__":
    analyze_epic_positioning()
