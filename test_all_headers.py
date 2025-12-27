#!/usr/bin/env python3
"""
Test header extraction across multiple templates
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from backend.api import API

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-cloud-vision-key.json'

def test_template(api, template_name, pdf_path, page_num):
    """Test header extraction for a specific template"""
    
    print(f"\n{'='*80}")
    print(f"📋 Testing template: {template_name}")
    print(f"📄 PDF: {pdf_path}")
    print(f"📃 Page: {page_num}")
    print('='*80)
    
    # Set template
    api.set_template(template_name)
    
    # Process single page
    result = api.process_pdf(pdf_path, start_page=page_num, end_page=page_num)
    
    if not result.get('success'):
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
        return False
    
    voters = result.get('voters', [])
    
    if not voters:
        print("⚠️ No voters extracted")
        return False
    
    print(f"\n✅ Extracted {len(voters)} voters")
    
    # Show header from first voter
    first_voter = voters[0]
    
    print(f"\n📍 Page-Level Header:")
    print(f"   District:      {first_voter.get('header_district', 'N/A')}")
    print(f"   Taluka:        {first_voter.get('header_taluka', 'N/A')}")
    print(f"   Booth:         {first_voter.get('header_booth', 'N/A')}")
    print(f"   Constituency:  {first_voter.get('header_constituency', 'N/A')}")
    print(f"   Office:        {first_voter.get('header_office', 'N/A')}")
    
    if first_voter.get('header_raw_text'):
        print(f"\n📝 Raw Header Text:")
        lines = first_voter['header_raw_text'].split('\n')
        for line in lines[:5]:  # Show first 5 lines
            if line.strip():
                print(f"   {line}")
        if len(lines) > 5:
            print(f"   ... ({len(lines) - 5} more lines)")
    
    print(f"\n👥 Sample voter:")
    epic = first_voter.get('epic', 'N/A')
    name = first_voter.get('name_marathi', 'N/A')
    age = first_voter.get('age', 'N/A')
    gender = first_voter.get('gender', 'N/A')
    print(f"   EPIC: {epic} | Name: {name} | Age: {age} | Gender: {gender}")
    
    # Check if all voters have header
    voters_with_header = sum(1 for v in voters if v.get('header_raw_text'))
    coverage = voters_with_header / len(voters) * 100
    print(f"\n📊 Header coverage: {voters_with_header}/{len(voters)} ({coverage:.1f}%)")
    
    if coverage == 100:
        print("✅ All voters have header data!")
        return True
    else:
        print(f"⚠️ {len(voters) - voters_with_header} voters missing header")
        return False

def main():
    """Test header extraction across all templates"""
    
    print("🔧 Initializing API...")
    api = API()
    print("✅ API initialized\n")
    
    # Test cases for different templates
    test_cases = [
        {
            'template': 'zp_boothwise',
            'pdf': 'samples/Zp_Boothwise/BoothList_Division_33_Booth_6_A4 राजोली.pdf',
            'page': 6
        },
        {
            'template': 'boothwise',
            'pdf': 'samples/Boothwise/BoothVoterList_A4_Ward_2_Booth_6.pdf',
            'page': 3
        },
        {
            'template': 'wardwise',
            'pdf': 'samples/WardWiseData/FinalList_Ward_3.pdf',
            'page': 3
        },
        {
            'template': 'mahanagarpalika',
            'pdf': 'samples/Mahanagarpalika/DraftList_Ward_11.pdf',
            'page': 3
        },
        {
            'template': 'ac_wise_low_quality',
            'pdf': 'samples/ACWise_LowData Quality/2024-EROLLGEN-S13-72-FinalRoll-Revision2-MAR-01.pdf',
            'page': 3
        }
    ]
    
    results = {}
    
    for test_case in test_cases:
        template = test_case['template']
        pdf = test_case['pdf']
        page = test_case['page']
        
        # Check if PDF exists
        if not os.path.exists(pdf):
            print(f"\n⚠️ Skipping {template} - PDF not found: {pdf}")
            results[template] = False
            continue
        
        try:
            success = test_template(api, template, pdf, page)
            results[template] = success
        except Exception as e:
            print(f"\n❌ Error testing {template}: {e}")
            results[template] = False
    
    # Summary
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    
    for template, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {template}: {'PASS' if success else 'FAIL'}")
    
    total = len(results)
    passed = sum(1 for s in results.values() if s)
    
    print(f"\n📈 Overall: {passed}/{total} templates passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 All templates successfully extract page-level headers!")
    else:
        print(f"\n⚠️ {total - passed} template(s) need attention")

if __name__ == '__main__':
    main()
