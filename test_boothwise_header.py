#!/usr/bin/env python3
"""
Test header extraction on Boothwise (standard) template
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from backend.api import API

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-cloud-vision-key.json'

def test_boothwise_header():
    """Test header extraction with standard Boothwise template"""
    
    print("🔧 Initializing API...")
    api = API()
    print("✅ API initialized\n")
    
    # Set template to Boothwise
    template_name = 'boothwise'
    print(f"📐 Setting template: {template_name}")
    result = api.set_template(template_name)
    print(f"✅ {result}\n")
    
    # Process page 3 of Boothwise PDF
    pdf_path = 'samples/Boothwise/BoothVoterList_A4_Ward_2_Booth_6.pdf'
    print(f"📄 Testing: {pdf_path}")
    print("   Processing page 3\n")
    
    result = api.process_pdf(pdf_path, start_page=3, end_page=3)
    
    if not result.get('success'):
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
        return False
    
    voters = result.get('voters', [])
    
    print("\n" + "="*80)
    print("📊 BOOTHWISE HEADER EXTRACTION RESULTS")
    print("="*80)
    
    if not voters:
        print("❌ No voters extracted")
        return False
    
    print(f"\nTotal voters extracted: {len(voters)}\n")
    
    # Show header from first voter
    first_voter = voters[0]
    
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
    for i, voter in enumerate(voters[:3], 1):
        epic = voter.get('epic', 'N/A')
        name = voter.get('name_marathi', 'N/A')
        age = voter.get('age', 'N/A')
        gender = voter.get('gender', 'N/A')
        
        print(f"   {i}. EPIC: {epic} | Name: {name} | Age: {age} | Gender: {gender}")
    
    # Verify all voters have header fields
    voters_with_header = sum(1 for v in voters if v.get('header_raw_text'))
    coverage = voters_with_header / len(voters) * 100
    
    print(f"\n📊 Header coverage: {voters_with_header}/{len(voters)} ({coverage:.1f}%)")
    
    if coverage == 100:
        print("✅ All voters have header data!")
        print("\n" + "="*80)
        print("✅ BOOTHWISE TEMPLATE TEST PASSED!")
        print("="*80)
        return True
    else:
        print(f"⚠️ {len(voters) - voters_with_header} voters missing header")
        return False

if __name__ == '__main__':
    success = test_boothwise_header()
    
    if not success:
        sys.exit(1)
