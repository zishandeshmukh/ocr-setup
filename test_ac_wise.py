#!/usr/bin/env python3
"""Test AC Wise Low Quality template EPIC extraction."""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from backend.api import API
import fitz

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-cloud-vision-key.json'

def test_ac_wise():
    """Test AC Wise Low Quality template on sample PDF"""
    
    # Initialize API with ac_wise_low_quality template
    api = API()
    api.set_template('ac_wise_low_quality')
    
    print(f"✅ Loaded template: ac_wise_low_quality")
    print(f"   Template config: L={api.template['left']}, R={api.template['right']}, "
          f"T={api.template['top']}, B={api.template['bottom']}, "
          f"Rows={api.template['rows']}, Cols={api.template['cols']}")
    
    # Find sample PDF
    sample_dir = 'samples/ACWise_LowData Quality'
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
    
    # Test on page 3 (skip potential cover pages)
    print(f"\n🧪 Testing page 3...")
    result = api.process_pdf(pdf_path, start_page=3, end_page=3)
    
    # Check results
    voters_found = len(result.get('voters', []))
    print(f"\n📊 Results for page 3:")
    print(f"   Total voters extracted: {voters_found}")
    print(f"   Expected: 30 voters (10 rows × 3 cols)")
    
    # Count EPICs
    epics_found = sum(1 for v in result.get('voters', []) if v.get('epic') and v.get('epic') != 'ERROR_MISSING_EPIC')
    error_epics = sum(1 for v in result.get('voters', []) if v.get('epic') == 'ERROR_MISSING_EPIC')
    missing_epic = voters_found - epics_found - error_epics
    
    print(f"   EPICs found: {epics_found}/{voters_found}")
    print(f"   Error placeholders: {error_epics}")
    print(f"   Missing EPICs: {missing_epic}")
    
    if epics_found >= 28:  # 93%+ accuracy
        print(f"   ✅ EPIC extraction: {epics_found}/{voters_found} = {epics_found/voters_found*100:.1f}%")
    elif epics_found + error_epics >= 28:
        print(f"   ⚠️ EPIC extraction with errors: {epics_found} valid + {error_epics} errors = {(epics_found + error_epics)/voters_found*100:.1f}%")
    else:
        print(f"   ⚠️ EPIC extraction below target: {epics_found}/{voters_found} = {epics_found/voters_found*100:.1f}%")
    
    # Show sample voters with and without EPICs
    print(f"\n📝 Sample voters from page 3:")
    voters_with_epic = [v for v in result.get('voters', []) if v.get('epic') and v.get('epic') != 'ERROR_MISSING_EPIC']
    voters_error_epic = [v for v in result.get('voters', []) if v.get('epic') == 'ERROR_MISSING_EPIC']
    voters_without_epic = [v for v in result.get('voters', []) if not v.get('epic')]
    
    print(f"\n✅ With valid EPIC ({len(voters_with_epic)}):")
    for i, voter in enumerate(voters_with_epic[:3], 1):
        epic = voter.get('epic', 'N/A')
        name = voter.get('name_marathi', voter.get('name_english', 'N/A'))[:30]
        print(f"   {i}. EPIC: {epic} | Name: {name}")
    
    if voters_error_epic:
        print(f"\n⚠️ With ERROR_MISSING_EPIC placeholder ({len(voters_error_epic)}):")
        for i, voter in enumerate(voters_error_epic[:5], 1):
            name = voter.get('name_marathi', voter.get('name_english', 'N/A'))[:30]
            serial = voter.get('serial_no', 'N/A')
            print(f"   {i}. Serial: {serial} | Name: {name}")
    
    if voters_without_epic:
        print(f"\n❌ Completely missing EPIC ({len(voters_without_epic)}):")
        for i, voter in enumerate(voters_without_epic[:3], 1):
            name = voter.get('name_marathi', voter.get('name_english', 'N/A'))[:30]
            serial = voter.get('serial_no', 'N/A')
            print(f"   {i}. Serial: {serial} | Name: {name}")
    
    # Test more pages
    print(f"\n🧪 Testing pages 5, 7, 10 for consistency...")
    for page_num in [5, 7, 10]:
        result_p = api.process_pdf(pdf_path, start_page=page_num, end_page=page_num)
        voters_p = len(result_p.get('voters', []))
        epics_p = sum(1 for v in result_p.get('voters', []) if v.get('epic') and v.get('epic') != 'ERROR_MISSING_EPIC')
        error_p = sum(1 for v in result_p.get('voters', []) if v.get('epic') == 'ERROR_MISSING_EPIC')
        if voters_p > 0:
            success_rate = (epics_p / voters_p * 100) if voters_p > 0 else 0
            if error_p > 0:
                print(f"   Page {page_num}: {voters_p} voters, {epics_p} EPICs, {error_p} errors ({success_rate:.1f}%)")
            else:
                print(f"   Page {page_num}: {voters_p} voters, {epics_p} EPICs ({success_rate:.1f}%)")
    
    print(f"\n✅ AC Wise Low Quality template test complete!")

if __name__ == '__main__':
    test_ac_wise()
