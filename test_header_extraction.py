#!/usr/bin/env python3
"""
Test page-level header extraction on ZP Boothwise sample
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from backend.api import API

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-cloud-vision-key.json'

def test_header_extraction():
    """Test header extraction with ZP Boothwise template"""
    
    print("🔧 Initializing API...")
    api = API()
    print("✅ API initialized\n")
    
    # Set template to ZP Boothwise
    template_name = 'zp_boothwise'
    print(f"📐 Setting template: {template_name}")
    result = api.set_template(template_name)
    print(f"✅ {result}\n")
    
    # Process first 3 pages of ZP Boothwise PDF
    pdf_path = 'samples/Zp_Boothwise/BoothList_Division_33_Booth_6_A4 राजोली.pdf'
    print(f"📄 Testing: {pdf_path}")
    print("   Processing pages 6-8 (voter data pages)\n")
    
    result = api.process_pdf(pdf_path, start_page=6, end_page=8)
    
    if not result.get('success'):
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
        return
    
    voters = result.get('voters', [])
    
    print("\n" + "="*80)
    print("📊 HEADER EXTRACTION RESULTS")
    print("="*80)
    
    if not voters:
        print("❌ No voters extracted")
        return
    
    print(f"\nTotal voters extracted: {len(voters)}\n")
    
    # Group by page and show header info
    pages = {}
    for voter in voters:
        page_num = voter.get('page_number', 0)
        if page_num not in pages:
            pages[page_num] = []
        pages[page_num].append(voter)
    
    for page_num in sorted(pages.keys()):
        page_voters = pages[page_num]
        print(f"\n📄 Page {page_num}: {len(page_voters)} voters")
        print("-" * 80)
        
        # Show header from first voter (all voters on same page have same header)
        first_voter = page_voters[0]
        
        print(f"📍 Page-Level Header:")
        print(f"   District:      {first_voter.get('header_district', 'N/A')}")
        print(f"   Taluka:        {first_voter.get('header_taluka', 'N/A')}")
        print(f"   Booth:         {first_voter.get('header_booth', 'N/A')}")
        print(f"   Constituency:  {first_voter.get('header_constituency', 'N/A')}")
        print(f"   Office:        {first_voter.get('header_office', 'N/A')}")
        
        if first_voter.get('header_raw_text'):
            print(f"\n📝 Raw Header Text:")
            for line in first_voter['header_raw_text'].split('\n'):
                if line.strip():
                    print(f"   {line}")
        
        print(f"\n👥 Sample voters from this page:")
        for i, voter in enumerate(page_voters[:3], 1):
            epic = voter.get('epic', 'N/A')
            name = voter.get('name_marathi', 'N/A')
            age = voter.get('age', 'N/A')
            gender = voter.get('gender', 'N/A')
            
            # Verify all voters have same header
            assert voter.get('header_district') == first_voter.get('header_district'), \
                f"Header mismatch on page {page_num}!"
            
            print(f"   {i}. EPIC: {epic} | Name: {name} | Age: {age} | Gender: {gender}")
    
    print("\n" + "="*80)
    print("✅ Header extraction test complete!")
    print("="*80)
    
    # Verify all voters have header fields
    voters_with_header = sum(1 for v in voters if v.get('header_raw_text'))
    print(f"\n📊 Voters with header data: {voters_with_header}/{len(voters)} ({voters_with_header/len(voters)*100:.1f}%)")
    
    if voters_with_header == len(voters):
        print("✅ All voters have page-level header attached!")
    else:
        print(f"⚠️ {len(voters) - voters_with_header} voters missing header data")

if __name__ == '__main__':
    test_header_extraction()
