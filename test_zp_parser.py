"""Quick test for ZP Boothwise parser"""
from backend.excel_export import parse_zp_boothwise_header

raw = """परिषद जिल्हा चंद्रपुर
मारोडा - निवार्चन निवडणूक विभाग : राजोली - गण ३३
कोळसा : १ - भाग क्र . ६ यादी
कोळसा नविन : १ मतदान केंद्र कोळसा , जि.प.प्रा.शाळा पत्ता :"""

result = parse_zp_boothwise_header(raw)

print("=" * 50)
print("ZP BOOTHWISE PARSER TEST")
print("=" * 50)
print(f"District Council: {result['district_council']}")
print(f"Election Division: {result['election_division']}")
print(f"Gan: {result['gan']}")
print(f"Part No: {result['part_no']}")
print(f"Polling Station: {result['polling_station']}")
print(f"Address: {result['address']}")
print("=" * 50)
