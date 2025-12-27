"""Verification for AC Wise Low Quality Template"""
from backend.excel_export import parse_ac_wise_header
from backend.parser import extract_voter_from_block
import json

print("=" * 60)
print("AC WISE LOW QUALITY VERIFICATION")
print("=" * 60)

# 1. Test Header Parsing
print("\n1. HEADER PARSING TEST")
print("-" * 50)
raw_header = """विधानसभा मतदारसंघ क्रमांक आणि नाव : 72-बल्लारपूर
विभाग क्रमांक आणि नाव 1-पापली भटाळी
यादी भाग क्रमांक : 2"""

parsed_header = parse_ac_wise_header(raw_header)
print(f"Raw Header:\n{raw_header}\n")
print(f"Parsed Result:")
print(f"  Assembly Constituency: '{parsed_header.get('assembly_constituency')}'")
print(f"  Division: '{parsed_header.get('division')}'")
print(f"  Part No: '{parsed_header.get('part_no')}'") # Added Check

# 2. Test Voter Parsing (EPIC & Details from Image)
print("\n2. VOTER PARSING TEST (Voter #1 from Image)")
print("-" * 50)
# Simulating OCR output for the first voter block
voter_block = """1                     SRO6400592
नाव : प्रविण मारोती आडे
वडिलांचे नाव: मारोती आडे
घर क्रमांक :
वय: 37 लिंग : पुरुष"""

extracted_voter = extract_voter_from_block(voter_block)
print(f"Raw Block:\n{voter_block}\n")
print(f"Extracted Data:")
print(f"  EPIC: '{extracted_voter.get('epic')}' (Expected: SRO6400592)")
print(f"  Name (Marathi): '{extracted_voter.get('name_marathi')}'")
print(f"  Relative Name (Marathi): '{extracted_voter.get('relation_name_marathi')}'")
print(f"  Age: '{extracted_voter.get('age')}'")
print(f"  Gender: '{extracted_voter.get('gender')}'")


print("\n" + "=" * 60)
