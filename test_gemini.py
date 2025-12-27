"""Test Gemini transliteration"""
import sys
sys.path.insert(0, '.')
from backend.gemini_transliterate import batch_transliterate_gemini

names = [
    'चंदा सतीश मौर्या',
    'राजवंती प्रसाद',
    'प्रिया सुधीर श्रीवास्तव',
    'संगीता अरुण शर्मा',
    'निर्मला चंद्रशेखर शर्मा',
]

print("Testing Gemini batch transliteration...")
print("="*50)

results = batch_transliterate_gemini(names)

for i, (mar, eng) in enumerate(zip(names, results)):
    print(f"{i+1}. {mar}")
    print(f"   -> {eng}")
    print()
