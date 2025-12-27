"""Test and save results to file"""
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

with open('transliteration_results.txt', 'w', encoding='utf-8') as f:
    for name in names:
        result = transliterate_marathi(name)
        f.write(f"{name}\n  -> {result}\n\n")
    
print("Results saved to transliteration_results.txt")
