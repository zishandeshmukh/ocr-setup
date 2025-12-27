"""Test transliteration - simple output"""
from backend.corrections import transliterate_marathi

tests = [
    'संगीता',    # Sangeeta
    'मनजीत',    # Manjeet
    'प्रसाद',   # Prasad
    'सुनील',    # Sunil  
    'राजेश',    # Rajesh
]

for t in tests:
    print(f"{t} -> {transliterate_marathi(t)}")
