"""Test EPIC extraction with user's Mahanagarpalika sample data"""
from backend.parser import extract_voter_from_block

# Sample text blocks from user's image - simulating what OCR would extract
test_blocks = [
    """211 SML9025685 71/158/577
मतदाराचे पूर्ण नाव : दुर्खिलवाणी मणिशा
पतीचोेे नाव : दुर्खिलवाणी अनिल
घर क्रमांक : ५५५
वय : २३ लिंग : स्त्री""",
    
    """212 SML9024951 71/158/578
मतदाराचे पूर्ण नाव : शिलीमकर संतोष
पतीचोेे नाव : शिलीमकर मध्देवकर
घर क्रमांक : ५५५
वय : ६० लिंग : पुरुष""",
    
    """220 SML7862568 71/158/590
मतदाराचे पूर्ण नाव : कुंभरे भारती अरविंद
पतीचोेे नाव : कुंभरे अरविंद
घर क्रमांक : २९६
वय : २६ लिंग : स्त्री""",
    
    """226 CPV1020221 71/158/602
मतदाराचे पूर्ण नाव : देवके ललीता संघृता
पतीचोेे नाव : देवके संघृता
घर क्रमांक : ५५७
वय : ५८ लिंग : स्त्री""",
]

print("=" * 60)
print("EPIC EXTRACTION TEST - Mahanagarpalika Sample")
print("=" * 60)

all_passed = True
for i, block in enumerate(test_blocks, 1):
    result = extract_voter_from_block(block)
    epic = result.get('epic', '')
    expected_epics = ['SML9025685', 'SML9024951', 'SML7862568', 'CPV1020221']
    passed = epic == expected_epics[i-1]
    status = "PASS" if passed else "FAIL"
    if not passed:
        all_passed = False
    print(f"Test {i}: EPIC = [{epic}] Expected = [{expected_epics[i-1]}] -> {status}")

print("=" * 60)
print(f"OVERALL: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
print("=" * 60)
