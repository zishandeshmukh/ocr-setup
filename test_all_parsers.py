"""Comprehensive test for ALL template parsers"""
from backend.excel_export import (
    parse_boothwise_header,
    parse_mahanagarpalika_header,
    parse_zp_boothwise_header,
    parse_ac_wise_header
)

def test_boothwise():
    """Test Boothwise parser"""
    raw = """मतदान केंद्र : १ पेपर मिल मंगल कार्यालय उत्तरेकडील भाग खोली
परिषद नगर बल्लारपूर
प्रभाग क्र : १ - प्रभाग क्र . १
यादी भाग क्र . १६२ : ४ - बिहारी किराणा जवळील परिसर गोकुल"""
    
    result = parse_boothwise_header(raw)
    print("=" * 60)
    print("1. BOOTHWISE PARSER TEST")
    print("=" * 60)
    print(f"Council Name: {result['council_name']}")
    print(f"Ward No: {result['ward_no']}")
    print(f"Polling Station: {result['polling_station']}")
    print(f"Part No: {result['part_no']}")
    print(f"Polling Address: {result['polling_address']}")
    
    # Verify
    ok = all([
        'बल्लारपूर' in result['council_name'],
        '१' in result['ward_no'],
        result['part_no'] in ['१६२', '162'],
    ])
    print(f"Status: {'✅ PASS' if ok else '❌ FAIL'}")
    return ok

def test_mahanagarpalika():
    """Test Mahanagarpalika parser"""
    raw = """महानगरपालिका चंद्रपूर
भानापेठ ११ – प्रभाग क्र : -
यादी भाग क्र . १५८ : १ - जटपुरागेटरामाला मार्ग किल्ला लगत् चंद्रपुर"""
    
    result = parse_mahanagarpalika_header(raw)
    print("\n" + "=" * 60)
    print("2. MAHANAGARPALIKA PARSER TEST")
    print("=" * 60)
    print(f"Corporation: {result['corporation_name']}")
    print(f"Ward: {result['ward']}")
    print(f"Part No: {result['part_no']}")
    print(f"Address: {result['address']}")
    
    # Verify
    ok = all([
        'चंद्रपूर' in result['corporation_name'],
        'प्रभाग' in result['ward'],
        result['part_no'] in ['१५८', '158'],
    ])
    print(f"Status: {'✅ PASS' if ok else '❌ FAIL'}")
    return ok

def test_wardwise():
    """Test Wardwise parser (uses Mahanagarpalika parser)"""
    raw = """महानगरपालिका चंद्रपूर
प्रभाग क्र : १ - दे . गो . तुकूम
यादी भाग क्र . ३७ : २ - राष्ट्रवादी नगर"""
    
    result = parse_mahanagarpalika_header(raw)
    print("\n" + "=" * 60)
    print("3. WARDWISE PARSER TEST (uses Mahanagarpalika parser)")
    print("=" * 60)
    print(f"Corporation: {result['corporation_name']}")
    print(f"Ward: {result['ward']}")
    print(f"Part No: {result['part_no']}")
    print(f"Address: {result['address']}")
    
    # Verify
    ok = all([
        'चंद्रपूर' in result['corporation_name'],
        'प्रभाग' in result['ward'] or 'तुकूम' in result['ward'],
        result['part_no'] in ['३७', '37'],
    ])
    print(f"Status: {'✅ PASS' if ok else '❌ FAIL'}")
    return ok

def test_zp_boothwise():
    """Test ZP Boothwise parser"""
    raw = """परिषद जिल्हा चंद्रपुर
मारोडा - निवार्चन निवडणूक विभाग : राजोली - गण ३३
कोळसा : १ - भाग क्र . ६ यादी
कोळसा नविन : १ मतदान केंद्र कोळसा , जि.प.प्रा.शाळा पत्ता :"""
    
    result = parse_zp_boothwise_header(raw)
    print("\n" + "=" * 60)
    print("4. ZP BOOTHWISE PARSER TEST")
    print("=" * 60)
    print(f"District Council: {result['district_council']}")
    print(f"Election Division: {result['election_division']}")
    print(f"Gan: {result['gan']}")
    print(f"Part No: {result['part_no']}")
    print(f"Polling Station: {result['polling_station']}")
    print(f"Address: {result['address']}")
    
    # Verify
    ok = all([
        'चंद्रपुर' in result['district_council'],
        'राजोली' in result['election_division'],
        result['gan'] in ['३३', '33'],
        result['part_no'] in ['६', '6'],
        'कोळसा' in result['polling_station'],
        'शाळा' in result['address'],
    ])
    print(f"Status: {'✅ PASS' if ok else '❌ FAIL'}")
    return ok

def test_ac_wise():
    """Test AC Wise Low Quality parser"""
    raw = """विधानसभा मतदारसंघ क्रमांक आणि नाव : 72-बल्लारपूर
विभाग क्रमांक आणि नाव 1-पायली भटाळी"""
    
    result = parse_ac_wise_header(raw)
    print("\n" + "=" * 60)
    print("5. AC WISE LOW QUALITY PARSER TEST")
    print("=" * 60)
    print(f"Assembly Constituency: {result['assembly_constituency']}")
    print(f"Division: {result['division']}")
    
    # Verify
    ok = all([
        'बल्लारपूर' in result['assembly_constituency'],
        'भटाळी' in result['division'],
    ])
    print(f"Status: {'✅ PASS' if ok else '❌ FAIL'}")
    return ok

def test_boothlist_division():
    """Test Boothlist Division parser (uses ZP Boothwise parser)"""
    raw = """चंद्रपुर जिल्हा परिषद
निवडणूक विभाग : २८ - दुर्गापुर , निवार्चन गण : ५६
यादी भाग क्र. ५६ : १ - पंचशिल वार्ड दुर्गापुर
मतदान केंद्र : ९६ St. Mery Highschool (Durgapur) Room No ९ , पत्ता : St. Mery Highschool"""
    
    result = parse_zp_boothwise_header(raw)
    print("\n" + "=" * 60)
    print("6. BOOTHLIST DIVISION PARSER TEST (uses ZP Boothwise parser)")
    print("=" * 60)
    print(f"District Council: {result['district_council']}")
    print(f"Election Division: {result['election_division']}")
    print(f"Gan: {result['gan']}")
    print(f"Part No: {result['part_no']}")
    print(f"Polling Station: {result['polling_station']}")
    print(f"Address: {result['address']}")
    
    # Verify
    ok = all([
        'जिल्हा' in result['district_council'] or 'परिषद' in result['district_council'],
        result['gan'] in ['५६', '56'],
        result['part_no'] in ['५६', '56'],
    ])
    print(f"Status: {'✅ PASS' if ok else '❌ FAIL'}")
    return ok

if __name__ == "__main__":
    print("\n" + "🔍 TESTING ALL TEMPLATE PARSERS" + "\n")
    
    results = [
        ("Boothwise", test_boothwise()),
        ("Mahanagarpalika", test_mahanagarpalika()),
        ("Wardwise", test_wardwise()),
        ("ZP Boothwise", test_zp_boothwise()),
        ("AC Wise Low Quality", test_ac_wise()),
        ("Boothlist Division", test_boothlist_division()),
    ]
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, ok in results if ok)
    failed = len(results) - passed
    
    for name, ok in results:
        print(f"  {name}: {'✅ PASS' if ok else '❌ FAIL'}")
    
    print(f"\nTotal: {passed} passed, {failed} failed out of {len(results)} tests")
    print("=" * 60)
