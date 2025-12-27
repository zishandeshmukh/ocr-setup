import os
import fitz
import sys
import json
import re
from dotenv import load_dotenv
from ocr_engine import OCREngine
from parser import parse_gcv_annotations, extract_voter_from_block, extract_header_info
from corrections import apply_marathi_corrections, transliterate_marathi

# Load env (parent dir)
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

def load_template(template_name='Assembly_Standard'):
    """Load OCR template from config"""
    templates = {
        'Assembly_Standard': {
            'left': 61,
            'right': 85,
            'top': 390,
            'bottom': 168,
            'rows': 10,
            'cols': 3,
            'photo_excl_width': 0
        }
    }
    return templates.get(template_name, templates['Assembly_Standard'])

# Config
SAMPLES_DIR = r"d:\voter-details (5)\all_samples"
OUTPUT_REPORT = "verification_report.json"
PAGES_TO_TEST = 2 # Number of pages to test per file
SKIP_PAGES = 3    # Skip first N pages (headers, index)

def verify_samples():
    print(f"🚀 Starting Verification on: {SAMPLES_DIR}")
    
    # Get all PDF files and sort by size
    files = [f for f in os.listdir(SAMPLES_DIR) if f.lower().endswith('.pdf')]
    files_with_size = [(f, os.path.getsize(os.path.join(SAMPLES_DIR, f))) for f in files]
    files_with_size.sort(key=lambda x: x[1]) # Sort by size ascending
    
    # Check if we have files
    if not files:
        print("❌ No PDF files found in samples directory!")
        return

    print(f"found {len(files)} files.")

    ocr_engine = OCREngine()
    template = load_template()
    
    report = {}
    
    total_files = len(files)
    
    # Limit to first 3 files for quick verification if running interactively
    # check_limit = 3 
    # Use full list for now, user can interrupt
    
    for idx, (filename, size) in enumerate(files_with_size, 1):
        file_path = os.path.join(SAMPLES_DIR, filename)
        print(f"\n[{idx}/{total_files}] Checking: {filename} ({size/1024/1024:.2f} MB)")
        
        try:
            doc = fitz.open(file_path)
            total_pages = doc.page_count
            
            # Determine pages to check
            start_page = min(SKIP_PAGES, total_pages - 1) 
            end_page = min(start_page + PAGES_TO_TEST, total_pages)
            
            # If PDF is too short, just take page 0 or 1
            if start_page >= total_pages:
                start_page = 0
                end_page = min(PAGES_TO_TEST, total_pages)

            pages_checked = range(start_page, end_page)
            print(f"   Using pages: {list(pages_checked)} (Total: {total_pages})")
            
            file_results = {
                'total_pages': total_pages,
                'pages_checked': [],
                'status': 'PASS' 
            }
            
            for page_num in pages_checked:
                print(f"   -> Processing Page {page_num+1}...")
                
                # Render
                page = doc[page_num]
                zoom = 300 / 72
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                
                temp_img = f"temp_verify_{idx}_{page_num}.jpg"
                pix.save(temp_img, output="jpeg", jpg_quality=95)
                
                try:
                    # OCR
                    full_text, word_annotations = ocr_engine.run_ocr(temp_img)
                    
                    if not word_annotations:
                        print("      ⚠️ No text found")
                        continue
                        
                    # Parse
                    structured_text = parse_gcv_annotations(
                        word_annotations, 
                        pix.width, 
                        pix.height, 
                        template
                    )
                    
                    # Extract Header
                    header_info = {}
                    header_match = re.search(r'--- PAGE HEADING START ---\n(.*?)\n--- PAGE HEADING END ---', structured_text, re.DOTALL)
                    if header_match:
                         header_info = extract_header_info(header_match.group(1))
                    
                    # Extract Voters
                    blocks = structured_text.split('---')
                    voters = []
                    for block in blocks:
                        if 'PAGE HEADING' in block or len(block.strip()) < 20: continue
                        v = extract_voter_from_block(block)
                        if v['name_marathi'] or v['epic']:
                            voters.append(v)
                            
                    print(f"      ✅ Found {len(voters)} voters. Header Part No: {header_info.get('part_no', 'N/A')}")
                    
                    page_status = {
                        'page': page_num + 1,
                        'voter_count': len(voters),
                        'header_part': header_info.get('part_no'),
                        'success': len(voters) > 10 # Modified to >10 to be safer
                    }
                    file_results['pages_checked'].append(page_status)
                    
                    if len(voters) < 5:
                        print(f"      ⚠️ Low extraction count! ({len(voters)})")
                        file_results['status'] = 'WARN_LOW_COUNT'
                        
                finally:
                    if os.path.exists(temp_img):
                        os.remove(temp_img)
                        
            report[filename] = file_results
            
            # Flush stdout
            sys.stdout.flush()
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            report[filename] = {'status': 'ERROR', 'error': str(e)}
            
    # Summary
    print("\n" + "="*50)
    print("VERIFICATION SUMMARY")
    print("="*50)
    for fname, res in report.items():
        status = res.get('status', 'UNKNOWN')
        pages = res.get('pages_checked', [])
        counts = [p['voter_count'] for p in pages]
        print(f"{fname[:30]}... : {status} (Counts: {counts})")

if __name__ == "__main__":
    verify_samples()
