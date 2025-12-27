"""Test parser with user's new page format"""
import json
from backend.excel_export import parse_mahanagarpalika_header

# Two different formats from user
# Format 1 (previous page - worked)
header1 = """महानगरपालिका चंद्रपूर
भानापेठ ११ – प्रभाग क्र : -
यादी भाग क्र . १५८ : १ - जटपुरागेटरामाला मार्ग किल्ला लगत् चंद्रपुर"""

# Format 2 (new page from image)
header2 = """मुळ प्रारूप मतदार यादी
प्रभाग क्र : ११ - भानापेठ
यादी भाग क्र.५५८ : १ - जटपुरागेटरामाला मार्ग किल्ला लगत् चंद्रपूर हॉस्पिटल वार्ड क्र.३३"""

r1 = parse_mahanagarpalika_header(header1)
r2 = parse_mahanagarpalika_header(header2)

results = {
    "Format1_Previous": r1,
    "Format2_NewPage": r2
}

with open('format_test.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("Results saved to format_test.json")
