"""
Test serial extraction patterns against boothwise template format
Based on the page image provided by user
"""
import re

# Simulated OCR text blocks from boothwise template
# Format: serial is in top-left box, EPIC on same line or separate
test_blocks = [
    # Block format 1: Serial and EPIC on same line
    ("10 SRO8732299 72/160/1\nमतदाराचे पूर्ण: मंजू सतीश राजभर\nपतीचे नाव : सतीश राजभर", 10),
    
    # Block format 2: Serial on separate line
    ("10\nSRO8732299 72/160/1\nमतदाराचे पूर्ण: मंजू सतीश राजभर", 10),
    
    # Block format 3: EPIC first, serial after
    ("SRO8732299 72/160/1\n10\nमतदाराचे पूर्ण: मंजू सतीश राजभर", 10),
    
    # Various serials from the page
    ("11 SRO6584056 72/160/4\nमतदाराचे पूर्ण: चिंत्या ताराबाई आंबी", 11),
    ("25 SRO7303506 72/160/22\nमतदाराचे पूर्ण: शुभांगी कैलास भोंडेकार", 25),
    ("39 SRO3144532 72/160/43\nमतदाराचे पूर्ण: अनंता दशरथ गेडाम", 39),
    
    # Edge cases
    ("1 SRO123456 72/1/1\nनाव: Test Name", 1),
    ("99 SRO999999 72/99/99\nनाव: Test", 99),
]

# Import the actual extraction function
from backend.parser import extract_voter_from_block

print("=" * 60)
print("SERIAL EXTRACTION TEST - BOOTHWISE TEMPLATE")
print("=" * 60)

passed = 0
failed = 0

for text_block, expected_serial in test_blocks:
    # Extract voter data
    voter = extract_voter_from_block(text_block)
    extracted_serial = voter.get('serial_no', '')
    
    # Convert to int for comparison
    try:
        extracted_int = int(extracted_serial) if extracted_serial else 0
    except:
        extracted_int = 0
    
    status = "✅" if extracted_int == expected_serial else "❌"
    
    if extracted_int == expected_serial:
        passed += 1
    else:
        failed += 1
    
    # Show first line of block for context
    first_line = text_block.split('\n')[0][:50]
    print(f"\n{status} Block: '{first_line}...'")
    print(f"   Expected: {expected_serial}, Got: {extracted_serial}")

print("\n" + "=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_blocks)} tests")
print("=" * 60)

if failed == 0:
    print("\n🎉 ALL SERIAL EXTRACTIONS WORKING CORRECTLY!")
else:
    print("\n⚠️ Some patterns need adjustment.")
