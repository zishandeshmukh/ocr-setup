"""
Gemini-based Fast Transliteration
Uses batch processing for speed - transliterates all names in one API call
"""
import os
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Cache for transliterations to avoid repeated API calls
_transliteration_cache = {}

def get_gemini_api_key():
    """Get Gemini API key from environment"""
    return os.getenv('VITE_API_KEY', '')

def batch_transliterate_gemini(marathi_names):
    """
    Batch transliterate multiple Marathi names to English using Gemini API.
    This is FAST because it sends all names in one API call.
    
    Args:
        marathi_names: List of Marathi name strings
        
    Returns:
        List of English transliterations in same order
    """
    if not marathi_names:
        return []
    
    api_key = get_gemini_api_key()
    if not api_key:
        print("⚠️ Gemini API key not found, using fallback")
        from .corrections import transliterate_marathi
        return [transliterate_marathi(name) for name in marathi_names]
    
    # Check cache first
    uncached_names = []
    uncached_indices = []
    results = [None] * len(marathi_names)
    
    for i, name in enumerate(marathi_names):
        if name in _transliteration_cache:
            results[i] = _transliteration_cache[name]
        else:
            uncached_names.append(name)
            uncached_indices.append(i)
    
    # If all cached, return immediately
    if not uncached_names:
        return results
    
    try:
        import requests
        
        # Direct HTTP request to Gemini API (more compatible)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        # Create prompt for batch transliteration
        names_text = '\n'.join([f"{i+1}. {name}" for i, name in enumerate(uncached_names)])
        
        prompt = f"""Transliterate these Marathi names to English. 
Rules:
- Use common English spellings for Indian names
- चं → Chan (not Can)
- Keep the order and numbering
- Output ONLY the transliterated names, one per line with the same numbering

Names:
{names_text}

Output format:
1. [English name]
2. [English name]
..."""

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 1000
            }
        }
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            response_text = data['candidates'][0]['content']['parts'][0]['text'].strip()
            
            # Parse response
            lines = response_text.split('\n')
            
            transliterated = []
            for line in lines:
                # Extract name from "1. Name" format
                match = re.match(r'^\d+\.\s*(.+)$', line.strip())
                if match:
                    transliterated.append(match.group(1).strip())
            
            # Fill in results and cache
            for i, idx in enumerate(uncached_indices):
                if i < len(transliterated):
                    results[idx] = transliterated[i]
                    _transliteration_cache[uncached_names[i]] = transliterated[i]
                else:
                    # Fallback if parsing failed
                    from .corrections import transliterate_marathi
                    results[idx] = transliterate_marathi(uncached_names[i])
            
            return results
        else:
            print(f"⚠️ Gemini API error {response.status_code}: {response.text[:100]}")
            raise Exception(f"API error {response.status_code}")
        
    except Exception as e:
        print(f"⚠️ Gemini API error: {e}, using fallback")
        from .corrections import transliterate_marathi
        for i, idx in enumerate(uncached_indices):
            results[idx] = transliterate_marathi(uncached_names[i])
        return results


def transliterate_single_gemini(marathi_text):
    """
    Transliterate a single Marathi name using Gemini.
    Uses cache for fast repeated lookups.
    """
    if not marathi_text:
        return ''
    
    # Check cache
    if marathi_text in _transliteration_cache:
        return _transliteration_cache[marathi_text]
    
    # Use batch function with single name
    results = batch_transliterate_gemini([marathi_text])
    return results[0] if results else ''


def clear_cache():
    """Clear the transliteration cache"""
    global _transliteration_cache
    _transliteration_cache = {}
