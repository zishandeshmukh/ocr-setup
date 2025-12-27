"""Test the improved transliteration"""
from backend.corrections import transliterate_marathi

test_names = [
    ('प्रसाद', 'Prasad'),
    ('सुनील', 'Sunil'),
    ('राजेश', 'Rajesh'),
    ('महेश', 'Mahesh'),
    ('दिनेश', 'Dinesh'),
    ('विजय', 'Vijay'),
    ('चंदा', 'Chanda'),
    ('आशा', 'Asha'),
    ('सतीश', 'Satish'),
    ('गोपाल', 'Gopal'),
]

print("=" * 50)
print("TRANSLITERATION TEST")
print("=" * 50)

for marathi, expected in test_names:
    result = transliterate_marathi(marathi)
    status = "✅" if result.lower() == expected.lower() else "⚠️"
    print(f"{status} {marathi} -> {result} (expected: {expected})")

print("=" * 50)
