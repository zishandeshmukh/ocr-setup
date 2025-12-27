"""
Test Script: Verify Serial Number Extraction for ALL Templates
Run this to confirm patterns work correctly before production use.
"""
import re

# Devanagari digit mapping
devanagari_map = {'०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
                 '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'}

def extract_serial(text_block):
    """Extract serial number using all 7 patterns"""
    serial_val = ''
    
    # Pattern 1: Serial at very start followed by EPIC (boothwise)
    serial_epic_pattern = re.match(r'^\s*(\d{1,4}|[०-९]{1,4})\s+[A-Z]{2,4}', text_block)
    if serial_epic_pattern:
        serial_val = serial_epic_pattern.group(1)
        return serial_val, "Pattern 1: Serial + EPIC same line"
    
    # Pattern 2: Serial at start, then newline, then EPIC (AC Wise / Wardwise)
    if not serial_val:
        serial_newline_epic = re.match(r'^\s*(\d{1,4}|[०-९]{1,4})\s*[\n\r]+\s*[A-Z]{2,4}', text_block)
        if serial_newline_epic:
            serial_val = serial_newline_epic.group(1)
            return serial_val, "Pattern 2: Serial + newline + EPIC"
    
    # Pattern 3: Serial at start of block followed by newline
    if not serial_val:
        serial_match_start = re.match(r'^\s*\[?(\d{1,4}|[०-९]{1,4})\]?\s*[\n\r]', text_block)
        if serial_match_start:
            serial_val = serial_match_start.group(1)
            return serial_val, "Pattern 3: Boxed serial + newline"
    
    # Pattern 4: Serial at very start followed by any whitespace
    if not serial_val:
        serial_match_broad = re.match(r'^\s*(\d{1,4}|[०-९]{1,4})(?:\s|$)', text_block)
        if serial_match_broad:
            candidate = serial_match_broad.group(1)
            try:
                if int(candidate) <= 9999:
                    serial_val = candidate
                    return serial_val, "Pattern 4: Serial + whitespace"
            except:
                serial_val = candidate
                return serial_val, "Pattern 4: Serial + whitespace (Devanagari)"
    
    # Pattern 5: Label-based patterns
    if not serial_val:
        serial_label = re.search(r'(?:क्रमांक|Serial\s*No\.?|Sr\.?\s*No\.?)\s*[:\s-]*(\d+|[०-९]+)', text_block, re.IGNORECASE)
        if serial_label:
            candidate = serial_label.group(1)
            if len(candidate) <= 4:
                serial_val = candidate
                return serial_val, "Pattern 5: Label-based"
    
    # Pattern 6: ZP Boothwise format - "72/11/1"
    if not serial_val:
        zp_format = re.search(r'\d+/\d+/(\d{1,4})', text_block)
        if zp_format:
            serial_val = zp_format.group(1)
            return serial_val, "Pattern 6: ZP format (Part/Page/Serial)"
    
    # Pattern 7: Fallback - first number in first line
    if not serial_val:
        first_line = text_block.split('\n')[0] if '\n' in text_block else text_block
        first_num = re.search(r'(\d{1,4}|[०-९]{1,4})', first_line)
        if first_num:
            candidate = first_num.group(1)
            if len(candidate) <= 3:
                serial_val = candidate
                return serial_val, "Pattern 7: Fallback first number"
    
    return '', "No match"

# ============================================
# TEST CASES FOR ALL TEMPLATES
# ============================================

test_cases = [
    # Boothwise Template
    {
        "template": "Boothwise",
        "text": "1 SRO7728835 72/178/390\nमतदाराचे पूर्ण: चंदा सतीश मौर्या\nपतीचे नाव : सतीश मौर्या",
        "expected": "1"
    },
    {
        "template": "Boothwise (25)",
        "text": "25 SRO8476228 72/178/419\nमतदाराचे पूर्ण: नीतू सुनील यादव",
        "expected": "25"
    },
    
    # AC Wise Low Quality Template
    {
        "template": "AC Wise Low Quality",
        "text": "1\nJVW0954826\nनाव : आशा विकास अलोने\nपतीचे नाव: विकास अलोने",
        "expected": "1"
    },
    {
        "template": "AC Wise Low Quality (18)",
        "text": "18\nSRO6566491\nनाव : प्रमदेवन हिरामन चुनारकर",
        "expected": "18"
    },
    
    # ZP Boothwise Template
    {
        "template": "ZP Boothwise",
        "text": "1 SRO6001432 72/11/1\nमतदाराचे पूर्ण: अश्पाक शेख आरिस\nनांव",
        "expected": "1"
    },
    {
        "template": "ZP Boothwise (15)",
        "text": "15 SRO8642035 72/11/15\nमतदाराचे पूर्ण: अश्विनी तुषार सिखाम",
        "expected": "15"
    },
    
    # Mahanagarpalika Template
    {
        "template": "Mahanagarpalika",
        "text": "1 SML3117082 71/343/18\nमतदाराचे पूर्ण:आगदारी दिनेश शेखर\nनांव",
        "expected": "1"
    },
    {
        "template": "Mahanagarpalika (14)",
        "text": "14 SML8739146 71/343/762\nमतदाराचे पूर्ण:आगदारी शेखर समदुया",
        "expected": "14"
    },
    
    # Wardwise Template
    {
        "template": "Wardwise",
        "text": "3\nSRO8639247\nमतदाराचे पूर्ण:आकाश विजय कोडापे",
        "expected": "3"
    },
    
    # Boothlist Division Template
    {
        "template": "Boothlist Division",
        "text": "7 ABC1234567\nनाव : Test Name\nवय : 35",
        "expected": "7"
    },
    
    # Devanagari Serial Numbers
    {
        "template": "Devanagari Serial",
        "text": "१२ SRO1234567\nनाव : Test",
        "expected": "12"
    },
]

# Run tests
print("=" * 60)
print("SERIAL NUMBER EXTRACTION TEST - ALL TEMPLATES")
print("=" * 60)

passed = 0
failed = 0

for test in test_cases:
    serial, pattern = extract_serial(test["text"])
    
    # Convert Devanagari
    for dev, eng in devanagari_map.items():
        serial = serial.replace(dev, eng)
    
    status = "✅ PASS" if serial == test["expected"] else "❌ FAIL"
    
    if serial == test["expected"]:
        passed += 1
    else:
        failed += 1
    
    print(f"\n{status} | {test['template']}")
    print(f"   Expected: {test['expected']} | Got: {serial}")
    print(f"   Pattern: {pattern}")

print("\n" + "=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
print("=" * 60)

if failed == 0:
    print("\n🎉 ALL TEMPLATES WORKING CORRECTLY!")
else:
    print("\n⚠️ Some patterns need adjustment. Review failed cases.")
