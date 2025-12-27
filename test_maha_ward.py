"""Test Mahanagarpalika and Wardwise parsers with exact user samples"""
import json
from backend.excel_export import parse_mahanagarpalika_header

# Test 1: Mahanagarpalika (user's exact sample)
raw_maha = """महानगरपालिका चंद्रपूर
भानापेठ ११ – प्रभाग क्र : -
यादी भाग क्र . १५८ : १ - जटपुरागेटरामाला मार्ग किल्ला लगत् चंद्रपुर"""

# Test 2: Wardwise (user's exact sample)
raw_ward = """महानगरपालिका चंद्रपूर
प्रभाग क्र : १ - दे . गो . तुकूम
यादी भाग क्र . ३५ : १ - गजानन मंदिर जवळ वडगाव"""

print("=" * 60)
print("1. MAHANAGARPALIKA PARSER TEST")
print("=" * 60)
r1 = parse_mahanagarpalika_header(raw_maha)
print(f"Corporation: [{r1['corporation_name']}]")
print(f"Ward: [{r1['ward']}]")
print(f"Part No: [{r1['part_no']}]")
print(f"Address: [{r1['address']}]")
success1 = bool(r1['corporation_name'] and r1['part_no'])
print(f"PASS: {success1}")

print("\n" + "=" * 60)
print("2. WARDWISE PARSER TEST (uses Mahanagarpalika parser)")
print("=" * 60)
r2 = parse_mahanagarpalika_header(raw_ward)
print(f"Corporation: [{r2['corporation_name']}]")
print(f"Ward: [{r2['ward']}]")
print(f"Part No: [{r2['part_no']}]")
print(f"Address: [{r2['address']}]")
success2 = bool(r2['corporation_name'] and r2['part_no'])
print(f"PASS: {success2}")

# Also write to JSON for visual verification
results = {
    "Mahanagarpalika": r1,
    "Wardwise": r2
}
with open('test_maha_ward.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\nResults written to test_maha_ward.json")
