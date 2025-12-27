"""Test with user's exact sample data"""
import json
from backend.excel_export import parse_mahanagarpalika_header

# User's exact sample from header_raw_text
raw = """यादी मतदार प्रारूप मुळ
महानगरपालिका चंद्रपूर
भानापेठ ११ – प्रभाग क्र : -
यादी भाग क्र . १५८ : १ - जटपुरागेटरामाला मार्ग किल्ला लगत् चंद्रपुर हॉस्पिटल वार्ड क्र .३३"""

result = parse_mahanagarpalika_header(raw)

print("=" * 60)
print("MAHANAGARPALIKA PARSER TEST - User's Exact Sample")
print("=" * 60)
print(f"Corporation: [{result['corporation_name']}]")
print(f"Ward: [{result['ward']}]")
print(f"Part No: [{result['part_no']}]")
print(f"Address: [{result['address']}]")
print("=" * 60)

# Save to JSON
with open('test_user_sample.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print("Results saved to test_user_sample.json")
