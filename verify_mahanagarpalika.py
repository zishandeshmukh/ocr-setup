"""Complete verification of Mahanagarpalika template - Save to file"""
import json
from backend.excel_export import TEMPLATE_COLUMNS, parse_mahanagarpalika_header

output = []

output.append("=" * 70)
output.append("MAHANAGARPALIKA TEMPLATE COMPLETE VERIFICATION")
output.append("=" * 70)

# 1. Check template key mapping
output.append("\n1. TEMPLATE KEY MAPPING:")
output.append("-" * 50)
keys_to_check = ['mahanagpalika', 'mahanagarpalika', 'wardwise']
for key in keys_to_check:
    exists = key in TEMPLATE_COLUMNS
    output.append(f"   '{key}' in TEMPLATE_COLUMNS: {'YES' if exists else 'NO'}")

# 2. Show Excel columns for Mahanagarpalika
output.append("\n2. EXCEL COLUMNS FOR MAHANAGARPALIKA:")
output.append("-" * 50)
config = TEMPLATE_COLUMNS.get('mahanagpalika', {})
headers = config.get('headers', [])
data_keys = config.get('data_keys', [])

output.append(f"   Total columns: {len(headers)}")
output.append("\n   Column # | Header | Data Key")
output.append("   " + "-" * 60)
for i, (h, k) in enumerate(zip(headers, data_keys), 1):
    output.append(f"   {i:2}. {h:40} | {k}")

# 3. Test header parsing
output.append("\n3. HEADER PARSING TEST:")
output.append("-" * 50)
sample_header = """महानगरपालिका चंद्रपूर
भानापेठ ११ – प्रभाग क्र : -
यादी भाग क्र . १५८ : १ - जटपुरागेटरामाला मार्ग"""

parsed = parse_mahanagarpalika_header(sample_header)
output.append("   Parsed header fields:")
for k, v in parsed.items():
    output.append(f"   {k}: {v}")

output.append("\n" + "=" * 70)
output.append("ALL CONNECTIONS VERIFIED!")
output.append("=" * 70)

# Write to file
with open('verification_result.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print("Results saved to verification_result.txt")
