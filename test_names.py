"""Test transliteration with user's names"""
from backend.corrections import transliterate_marathi

names = [
    'चंदा सतीश मौर्या',
    'राजवंती प्रसाद',
    'प्रिया सुधीर श्रीवास्तव',
    'नैना अशोक ताड्रॉ',
    'गुडिया पंकज यादव',
    'सोनम अमीरचंद प्रसाद राजभर',
    'संगीता अरुण शर्मा',
    'निर्मला चंद्रशेखर शर्मा',
]

print("=" * 60)
print("TRANSLITERATION TEST")
print("=" * 60)
for name in names:
    result = transliterate_marathi(name)
    print(f"{name}")
    print(f"  -> {result}")
    print()
