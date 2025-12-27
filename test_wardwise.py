#!/usr/bin/env python3
"""Test Wardwise template on sample PDF."""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from backend.api import API
import fitz

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-cloud-vision-key.json'

def test_wardwise():
    """Test Wardwise template on sample PDF"""
    
    # Initialize API with wardwise template
    api = API()
    api.set_template('wardwise')
    
    print(f"✅ Loaded template: wardwise")
    print(f"   Template config: L={api.template['left']}, R={api.template['right']}, "
          f"T={api.template['top']}, B={api.template['bottom']}, "
          f"Rows={api.template['rows']}, Cols={api.template['cols']}")
    
    # Find sample PDF
    sample_dir = 'samples/WardWiseData'
    pdf_files = [f for f in os.listdir(sample_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        print("❌ No PDF found")
        return
    
    pdf_path = os.path.join(sample_dir, pdf_files[0])
    print(f"\n📄 Testing: {pdf_files[0]}")
    
    pdf = fitz.open(pdf_path)
    total_pages = pdf.page_count
    pdf.close()
    
    print(f"   Total pages: {total_pages}")
    
    # Test on page 3 which we analyzed (has 5 rows of data = 13 EPICs)
    print(f"\n🧪 Testing page 3 (5 rows of voter data)...")
    result = api.process_pdf(pdf_path, start_page=3, end_page=3)
    
    # Check results
    voters_found = len(result.get('voters', []))
    print(f"\n📊 Results for page 3:")
    print(f"   Total voters extracted: {voters_found}")
    
    # Count EPICs
    epics_found = sum(1 for v in result.get('voters', []) if v.get('epic'))
    print(f"   EPICs found: {epics_found}")
    print(f"   Expected: 13 EPICs (based on calibration analysis)")
    
    if epics_found >= 12:  # Allow 1 miss for 92% accuracy
        print(f"   ✅ EPIC extraction: {epics_found}/13 = {epics_found/13*100:.1f}%")
    else:
        print(f"   ⚠️ EPIC extraction below target: {epics_found}/13 = {epics_found/13*100:.1f}%")
    
    # Show sample voters
    print(f"\n📝 Sample voters from page 3:")
    for i, voter in enumerate(result.get('voters', [])[:5], 1):
        epic = voter.get('epic', 'N/A')
        name = voter.get('name', 'N/A')[:30]
        print(f"   {i}. EPIC: {epic} | Name: {name}")
    
    # Test on a fuller page (try multiple pages to find one with full grid)
    print(f"\n🧪 Testing pages 10-15 to find full voter grid...")
    for page_num in range(10, 16):
        result_p = api.process_pdf(pdf_path, start_page=page_num, end_page=page_num)
        voters_p = len(result_p.get('voters', []))
        epics_p = sum(1 for v in result_p.get('voters', []) if v.get('epic'))
        if voters_p > 0:
            print(f"   Page {page_num}: {voters_p} voters, {epics_p} EPICs")
            if epics_p >= 25:  # Found a nearly full page
                print(f"      ✅ Page {page_num} has nearly full grid!")
                break
    
    print(f"\n✅ Wardwise template test complete!")

if __name__ == '__main__':
    test_wardwise()
