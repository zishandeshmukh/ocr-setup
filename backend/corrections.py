"""
Marathi OCR Corrections
Fixes common OCR character confusions
"""
import re

# Common OCR error corrections for Marathi
MARATHI_CORRECTIONS = {
    'आजम': 'आत्राम',
    'अजम': 'आत्राम',
    'आञाम': 'आत्राम',
    'अञाम': 'आत्राम',
    'प्रवन': 'प्रविन',
    'प्रवीन': 'प्रविन',
    'गोपल': 'गोपाल',
    'सुनल': 'सुनिल',
    'सुनला': 'सुनील',
    'रमश': 'रमेश',
    'महश': 'महेश',
    'राजश': 'राजेश',
    'दनश': 'दिनेश',
}

def apply_marathi_corrections(text):
    """
    Apply OCR corrections to Marathi text
    
    Args:
        text: Marathi text string
        
    Returns:
        str: Corrected text
    """
    if not text:
        return text
    
    corrected = text
    for wrong, correct in MARATHI_CORRECTIONS.items():
        corrected = corrected.replace(wrong, correct)
    
    return corrected

def transliterate_marathi(marathi_text):
    """
    Marathi to English transliteration using indic-transliteration library
    
    Args:
        marathi_text: Marathi text in Devanagari
        
    Returns:
        str: Transliterated English text
    """
    if not marathi_text:
        return ''
    
    # Remove "नाव" (name label) from marathi text before transliteration
    marathi_text = marathi_text.replace('नाव', '').replace('नांव', '').replace('नव', '').strip()
    # Remove stray separators
    marathi_text = re.sub(r'[\|:]+', ' ', marathi_text)
    marathi_text = re.sub(r'\s+', ' ', marathi_text).strip()
    
    if not marathi_text:
        return ''
    
    # Try using indic-transliteration library (proper transliteration)
    try:
        from indic_transliteration import sanscript
        from indic_transliteration.sanscript import transliterate
        
        # Use HK (Harvard-Kyoto) scheme which preserves inherent 'a' vowel
        result = transliterate(marathi_text, sanscript.DEVANAGARI, sanscript.HK)
        
        # Fix anusvara (M) based on following consonant
        # Before velars (k, g) -> n (ng sound)
        # Before palatals (c, j) -> n  
        # Before labials (p, b) -> m
        # Default -> n (most common in names)
        import re as regex
        result = regex.sub(r'M([kg])', r'n\1', result)  # Mg, Mk -> ng, nk
        result = regex.sub(r'M([cj])', r'n\1', result)  # Mc, Mj -> nc, nj
        result = regex.sub(r'M([pb])', r'm\1', result)  # Mp, Mb -> mp, mb
        result = result.replace('M', 'n')  # Default: M -> n
        
        # Convert HK notation to readable English
        hk_to_english = {
            'A': 'a',     # long a -> a (simplified)
            'I': 'ee',    # long i -> ee
            'U': 'oo',    # long u -> oo  
            'R': 'ri',    # vocalic r
            'G': 'n',     # velar nasal (ङ) -> n
            'J': 'n',     # palatal nasal (ञ) -> n
            'T': 't',     # retroflex t
            'D': 'd',     # retroflex d
            'N': 'n',     # retroflex n
            'z': 'sh',    # palatal sibilant (ś)
            'S': 'sh',    # retroflex sibilant (ṣ)
            'H': '',      # remove visarga at end of names
            '|': '',      # remove dandas
            "'": '',      # remove avagraha
        }
        
        for hk, eng in hk_to_english.items():
            result = result.replace(hk, eng)
        
        # Clean up double vowels that look awkward
        result = result.replace('aa', 'a')  # Simplify long a
        result = result.replace('ii', 'i')  # Don't use ii
        
        # Smart trailing 'a' removal:
        # - Keep 'a' if original Marathi ends with ा (aa matra) - these are intentional
        # - Remove 'a' if it's just schwa from consonant (like श -> sha -> sh)
        # Check if original text ends with aa-matra (ा)
        ends_with_aa_matra = marathi_text.endswith('ा') or marathi_text.endswith('ी') or marathi_text.endswith('ू') or marathi_text.endswith('े') or marathi_text.endswith('ो') or marathi_text.endswith('ौ') or marathi_text.endswith('ै')
        
        words = result.split()
        cleaned_words = []
        for i, word in enumerate(words):
            # Only process the last word for trailing vowel check
            if i == len(words) - 1 and not ends_with_aa_matra:
                # Remove trailing 'a' only if original doesn't end with vowel matra
                if len(word) > 3 and word.endswith('a'):
                    word = word[:-1]
            cleaned_words.append(word.capitalize())
        
        return ' '.join(cleaned_words)
        
    except ImportError:
        # Fallback to simple character mapping if library not available
        pass
    except Exception as e:
        # If any error, fall back to simple method
        print(f"Transliteration error: {e}")
    
    # Fallback: Simple character mapping
    char_map = {
        'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ee', 'उ': 'u', 'ऊ': 'oo',
        'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
        'क': 'ka', 'ख': 'kha', 'ग': 'ga', 'घ': 'gha', 'ङ': 'nga',
        'च': 'cha', 'छ': 'chha', 'ज': 'ja', 'झ': 'jha', 'ञ': 'nya',
        'ट': 'ta', 'ठ': 'tha', 'ड': 'da', 'ढ': 'dha', 'ण': 'na',
        'त': 'ta', 'थ': 'tha', 'द': 'da', 'ध': 'dha', 'न': 'na',
        'प': 'pa', 'फ': 'pha', 'ब': 'ba', 'भ': 'bha', 'म': 'ma',
        'य': 'ya', 'र': 'ra', 'ल': 'la', 'व': 'va', 'ळ': 'la',
        'श': 'sha', 'ष': 'sha', 'स': 'sa', 'ह': 'ha',
        'ा': 'a', 'ि': 'i', 'ी': 'ee', 'ु': 'u', 'ू': 'oo',
        'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au',
        'ं': 'n', 'ः': 'h', '्': '',
        'ृ': 'ri', 'ॅ': 'e', 'ॉ': 'o',
    }
    
    result = ''
    for char in marathi_text:
        result += char_map.get(char, char)
    
    # Clean up
    result = re.sub(r'\s+', ' ', result).strip()
    
    # Title case
    return ' '.join(word.capitalize() for word in result.split())

