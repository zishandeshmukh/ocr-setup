"""Quick test for transliteration fix"""
from backend.corrections import transliterate_marathi

# User's test cases
tests = [
    ('संगीता', 'Sangeeta'),
    ('मनजीत', 'Manjeet'),
    ('प्रसाद', 'Prasad'),
    ('सुनील', 'Sunil'),
    ('राजेश', 'Rajesh'),
]

print("Testing transliteration...")
for marathi, expected in tests:
    result = transliterate_marathi(marathi)
    status = "✅" if expected.lower() in result.lower() else "❌"
    print(f"{status} {marathi} -> {result} (expected: {expected})")
