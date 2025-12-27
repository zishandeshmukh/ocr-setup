"""Simple test with JSON output"""
import json
from backend.excel_export import (
    parse_boothwise_header,
    parse_mahanagarpalika_header,
    parse_zp_boothwise_header,
    parse_ac_wise_header
)

results = {}

# 1. Boothwise
raw1 = """मतदान केंद्र : १ पेपर मिल मंगल कार्यालय उत्तरेकडील भाग खोली
परिषद नगर बल्लारपूर
प्रभाग क्र : १ - प्रभाग क्र . १
यादी भाग क्र . १६२ : ४ - बिहारी किराणा जवळील परिसर गोकुल"""
r1 = parse_boothwise_header(raw1)
results['1_Boothwise'] = {
    'council_name': r1['council_name'],
    'ward_no': r1['ward_no'],
    'polling_station': r1['polling_station'],
    'part_no': r1['part_no'],
    'polling_address': r1['polling_address'],
    'PASS': bool(r1['council_name'] and r1['ward_no'] and r1['part_no'] and r1['polling_station'])
}

# 2. Mahanagarpalika
raw2 = """महानगरपालिका चंद्रपूर
भانापेठ ११ – प्रभाग क्र : -
यादी भाग क्र . १५८ : १ - जटपुरागेटरामाला मार्ग किल्ला लगत् चंद्रपुर"""
r2 = parse_mahanagarpalika_header(raw2)
results['2_Mahanagarpalika'] = {
    'corporation_name': r2['corporation_name'],
    'ward': r2['ward'],
    'part_no': r2['part_no'],
    'address': r2['address'],
    'PASS': bool(r2['corporation_name'] and r2['part_no'])
}

# 3. Wardwise (uses same parser as Mahanagarpalika)
raw3 = """महानगरपालिका चंद्रपूर
प्रभाग क्र : १ - दे . गो . तुकूम
यादी भाग क्र . ३७ : २ - राष्ट्रवादी नगर"""
r3 = parse_mahanagarpalika_header(raw3)
results['3_Wardwise'] = {
    'corporation_name': r3['corporation_name'],
    'ward': r3['ward'],
    'part_no': r3['part_no'],
    'address': r3['address'],
    'PASS': bool(r3['corporation_name'] and r3['part_no'])
}

# 4. ZP Boothwise
raw4 = """परिषद जिल्हा चंद्रपुर
मारोडा - निवार्चन निवडणूक विभाग : राजोली - गण ३३
कोळसा : १ - भाग क्र . ६ यादी
कोळसा नविन : १ मतदान केंद्र कोळसा , जि.प.प्रा.शाळा पत्ता :"""
r4 = parse_zp_boothwise_header(raw4)
results['4_ZP_Boothwise'] = {
    'district_council': r4['district_council'],
    'election_division': r4['election_division'],
    'gan': r4['gan'],
    'part_no': r4['part_no'],
    'polling_station': r4['polling_station'],
    'address': r4['address'],
    'PASS': bool(r4['district_council'] and r4['gan'] and r4['part_no'])
}

# 5. AC Wise Low Quality
raw5 = """विधानसभा मतदारसंघ क्रमांक आणि नाव : 72-बल्लारपूर
विभाग क्रमांक आणि नाव 1-पायली भटाळी"""
r5 = parse_ac_wise_header(raw5)
results['5_AC_Wise'] = {
    'assembly_constituency': r5['assembly_constituency'],
    'division': r5['division'],
    'PASS': bool(r5['assembly_constituency'] and r5['division'])
}

# 6. Boothlist Division (uses ZP parser)
raw6 = """चंद्रपुर जिल्हा परिषद
निवडणूक विभाग : २८ - दुर्गापुर , निवार्चन गण : ५६
यादी भाग क्र. ५६ : १ - पंचशिल वार्ड दुर्गापुर
मतदान केंद्र : ९६ St. Mery Highschool (Durgapur) Room No ९ , पत्ता : St. Mery Highschool"""
r6 = parse_zp_boothwise_header(raw6)
results['6_Boothlist_Division'] = {
    'district_council': r6['district_council'],
    'election_division': r6['election_division'],
    'gan': r6['gan'],
    'part_no': r6['part_no'],
    'polling_station': r6['polling_station'],
    'address': r6['address'],
    'PASS': bool(r6['gan'] and r6['part_no'])
}

# Write results
with open('test_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# Summary
passed = sum(1 for k, v in results.items() if v.get('PASS'))
print(f"RESULTS: {passed}/6 PASSED")
for k, v in results.items():
    print(f"  {k}: {'PASS' if v.get('PASS') else 'FAIL'}")
