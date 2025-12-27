"""
Parser - Template-based coordinate parsing
Based on OCR_Samruddhi's gcv_xy_parser.py
"""
from PIL import Image as PILImage
import re

def normalize_epic_aggressive(text):
    """
    Aggressive EPIC normalization to handle OCR errors.
    EPIC format: Exactly 3 letters + 7 digits (10 characters total).
    Example: ABC1234567
    
    Handles common OCR errors in low-quality scans:
    - O/0, I/1/l, S/5, Z/2, B/8, G/6 confusion
    - Extra spaces, dashes, slashes
    - Mixed case
    """
    if not text:
        return ''
    # Remove all non-alphanumeric
    clean = re.sub(r'[^A-Za-z0-9]', '', text).upper()
    if len(clean) < 10:
        return ''
    
    # Extract exactly 3 letters + 7 digits
    # Try to find 3 consecutive letters at start
    alpha_match = re.match(r'^([A-Z]{3})', clean)
    if alpha_match:
        prefix = alpha_match.group(1)
        suffix = clean[3:]
        # Apply OCR fixes ONLY to suffix (digits), not prefix (letters)
        # More aggressive fixes for low-quality scans
        suffix = suffix.replace('O', '0').replace('o', '0')
        suffix = suffix.replace('I', '1').replace('l', '1').replace('i', '1')
        suffix = suffix.replace('L', '1')
        suffix = suffix.replace('S', '5').replace('s', '5')
        suffix = suffix.replace('Z', '2').replace('z', '2')
        suffix = suffix.replace('B', '8').replace('b', '8')
        suffix = suffix.replace('G', '6').replace('g', '6')
        # Remove any remaining letters from suffix
        suffix = re.sub(r'[A-Za-z]', '', suffix)
        # Take exactly 7 digits
        if len(suffix) >= 7:
            return prefix + suffix[:7]
    
    # Fallback: try to extract 3 letters + 7 digits from anywhere in the string
    # Apply fixes before pattern matching
    fixed = clean.replace('O', '0').replace('I', '1').replace('L', '1')
    fixed = fixed.replace('S', '5').replace('Z', '2').replace('B', '8').replace('G', '6')
    pattern_match = re.search(r'([A-Z]{3})([0-9]{7})', fixed)
    if pattern_match:
        return pattern_match.group(1) + pattern_match.group(2)
    
    return ''

def get_word_center(word_annotation):
    """Calculate the center (x, y) of a word's bounding box"""
    vertices = word_annotation.bounding_poly.vertices
    x_min = min(v.x for v in vertices)
    x_max = max(v.x for v in vertices)
    y_min = min(v.y for v in vertices)
    y_max = max(v.y for v in vertices)
    center_x = (x_min + x_max) // 2
    center_y = (y_min + y_max) // 2
    return center_x, center_y

def structure_block_by_line(words_data, line_tolerance=10):
    """Group words into lines based on Y-coordinate and sort by X-coordinate"""
    if not words_data:
        return ""
    
    lines = []
    words_data.sort(key=lambda x: x[0])  # Sort by Y
    
    current_line_y = None
    current_line_words = []
    
    for y, x, word in words_data:
        if current_line_y is None:
            current_line_y = y
            current_line_words.append((x, word))
        elif abs(y - current_line_y) <= line_tolerance:
            current_line_words.append((x, word))
        else:
            # Finish current line
            current_line_words.sort(key=lambda item: item[0])
            lines.append(" ".join([w for x, w in current_line_words]))
            
            # Start new line
            current_line_y = y
            current_line_words = [(x, word)]
    
    # Add last line
    if current_line_words:
        current_line_words.sort(key=lambda item: item[0])
        lines.append(" ".join([w for x, w in current_line_words]))
    
    return "\n".join(lines)

def parse_gcv_annotations(word_annotations, image_W, image_H, template):
    """
    Parse GCV word annotations using template-based coordinate system
    
    Args:
        word_annotations: List of GCV text annotations
        image_W: Image width
        image_H: Image height
        template: Template dict with left, right, top, bottom, rows, cols
        
    Returns:
        str: Structured text blocks separated by '---'
    """
    if not word_annotations or len(word_annotations) <= 1:
        return "Error: No word annotations provided"
    
    # Extract template parameters
    L = template.get("left", 0)
    R = template.get("right", 0)
    T = template.get("top", 0)
    B = template.get("bottom", 0)
    ROWS = template.get("rows", 1)
    COLS = template.get("cols", 1)
    
    work_w = image_W - L - R
    work_h = image_H - T - B
    
    if work_w <= 0 or work_h <= 0 or ROWS == 0 or COLS == 0:
        return "Error: Invalid template parameters"
    
    box_w = work_w // COLS
    box_h = work_h // ROWS
    
    heading_words_data = []
    blocks_data = {}
    
    # Skip first annotation (full text)
    for annotation in word_annotations[1:]:
        word = annotation.description
        center_x, center_y = get_word_center(annotation)
        word_data_tuple = (center_y, center_x, word)
        
        # Check if word is in page heading (above template area)
        if center_y < T:
            heading_words_data.append(word_data_tuple)
            continue
        
        # Calculate row and column index
        rel_x = center_x - L
        rel_y = center_y - T
        c = rel_x // box_w
        r = rel_y // box_h
        
        # Add to block if within bounds
        if 0 <= r < ROWS and 0 <= c < COLS:
            if (r, c) not in blocks_data:
                blocks_data[(r, c)] = []
            blocks_data[(r, c)].append(word_data_tuple)
    
    # Structure output
    structured_blocks = []
    
    # Add page heading if exists
    if heading_words_data:
        structured_blocks.append("--- PAGE HEADING START ---")
        structured_blocks.append(structure_block_by_line(heading_words_data))
        structured_blocks.append("--- PAGE HEADING END ---")
    
    # Add voter blocks (row by row, column by column)
    for r in range(ROWS):
        for c in range(COLS):
            words_in_block = blocks_data.get((r, c), [])
            
            if words_in_block:
                block_text = structure_block_by_line(words_in_block)
                if block_text.strip():
                    structured_blocks.append(block_text)
    
    return "\n---\n".join(structured_blocks)

def extract_page_header(word_annotations, image_W, image_H, template):
    """
    Extract page-level administrative header from top-left of the page.
    
    This header contains district, taluka, booth, ward, and other contextual info
    that applies to all voter records on this page.
    
    Args:
        word_annotations: List of GCV text annotations
        image_W: Image width
        image_H: Image height
        template: Template dict (uses top margin as boundary)
    
    Returns:
        dict: {
            'raw_header_text': str,  # Full concatenated header text
            'district': str,         # Extracted district name
            'taluka': str,           # Extracted taluka/vibhag name
            'booth': str,            # Extracted booth/ward info
            'constituency': str,     # Extracted constituency info
            'office': str            # Extracted office/karyalay info
        }
    """
    if not word_annotations or len(word_annotations) <= 1:
        return {
            'raw_header_text': '',
            'district': '',
            'taluka': '',
            'booth': '',
            'constituency': '',
            'office': ''
        }
    
    # Get template margins
    T = template.get("top", 0)
    
    # Header keywords for detection (Marathi, Hindi, English)
    district_keywords = ['जिल्हा', 'जिला', 'District', 'परिषद', 'Parishad', 'जि.प']
    taluka_keywords = ['तालुका', 'Taluka', 'विभाग', 'Vibhag']
    booth_keywords = ['मतदान', 'केंद्र', 'Booth', 'Ward', 'वार्ड', 'गण']
    office_keywords = ['कार्यालय', 'Office', 'पत्ता', 'Address']
    constituency_keywords = ['निवडणूक', 'निवार्चन', 'Constituency', 'विधानसभा', 'Assembly']
    
    # Collect words in header region (top-left area before grid starts)
    # Header is typically in top 300px and left-aligned (x < 40% of page width)
    header_region_height = min(T, 400)  # Use top margin or max 400px
    header_region_width = image_W * 0.4  # Left 40% of page
    
    header_words = []
    for annotation in word_annotations[1:]:
        word = annotation.description
        center_x, center_y = get_word_center(annotation)
        
        # Check if in header region (top-left area)
        if center_y < header_region_height and center_x < header_region_width:
            header_words.append({
                'word': word,
                'x': center_x,
                'y': center_y
            })
    
    # Sort by Y then X
    header_words.sort(key=lambda w: (w['y'], w['x']))
    
    # Group into lines
    lines = []
    current_line = []
    last_y = -1
    y_threshold = 20
    
    for word_data in header_words:
        if last_y == -1 or abs(word_data['y'] - last_y) < y_threshold:
            current_line.append(word_data['word'])
            last_y = word_data['y']
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word_data['word']]
            last_y = word_data['y']
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Create raw header text
    raw_header_text = '\n'.join(lines)
    
    # Extract structured fields using keywords
    district = ''
    taluka = ''
    booth = ''
    constituency = ''
    office = ''
    
    for line in lines:
        # District extraction
        if not district and any(kw in line for kw in district_keywords):
            district = line.strip()
        
        # Taluka extraction
        if not taluka and any(kw in line for kw in taluka_keywords):
            taluka = line.strip()
        
        # Booth extraction
        if not booth and any(kw in line for kw in booth_keywords):
            booth = line.strip()
        
        # Constituency extraction
        if not constituency and any(kw in line for kw in constituency_keywords):
            constituency = line.strip()
        
        # Office extraction
        if not office and any(kw in line for kw in office_keywords):
            office = line.strip()
    
    return {
        'raw_header_text': raw_header_text,
        'district': district,
        'taluka': taluka,
        'booth': booth,
        'constituency': constituency,
        'office': office
    }

def parse_gcv_blocks(word_annotations, image_W, image_H, template):
    """
    Parse GCV word annotations and return explicit grid blocks.

    Args:
        word_annotations: List of GCV text annotations
        image_W: Image width
        image_H: Image height
        template: Template dict with left, right, top, bottom, rows, cols

    Returns:
        dict: {
          'heading_text': str,  # structured heading text (optional)
          'blocks': [
             {'r': int, 'c': int, 'text': str, 'words': [(y,x,word), ...]}
          ]
        }
    """
    if not word_annotations or len(word_annotations) <= 1:
        return {'heading_text': '', 'blocks': []}

    L = template.get("left", 0)
    R = template.get("right", 0)
    T = template.get("top", 0)
    B = template.get("bottom", 0)
    ROWS = template.get("rows", 1)
    COLS = template.get("cols", 1)

    work_w = image_W - L - R
    work_h = image_H - T - B

    if work_w <= 0 or work_h <= 0 or ROWS == 0 or COLS == 0:
        return {'heading_text': '', 'blocks': []}

    box_w = work_w // COLS
    box_h = work_h // ROWS

    heading_words_data = []
    blocks_data = {}

    centers = []
    for annotation in word_annotations[1:]:
        word = annotation.description
        center_x, center_y = get_word_center(annotation)
        tup = (center_y, center_x, word)
        centers.append((center_x, center_y, word))

        if center_y < T:
            heading_words_data.append(tup)
            continue

        rel_x = center_x - L
        rel_y = center_y - T
        c = rel_x // box_w
        r = rel_y // box_h

        if 0 <= r < ROWS and 0 <= c < COLS:
            blocks_data.setdefault((r, c), []).append(tup)

    # Helper: build blocks list from blocks_data
    def build_blocks_from(blocks_map):
        blocks_out = []
        for rr in range(ROWS):
            for cc in range(COLS):
                words = blocks_map.get((rr, cc), [])
                text = structure_block_by_line(words) if words else ''
                blocks_out.append({'r': rr, 'c': cc, 'text': text, 'words': words})
        return blocks_out

    # Build blocks list
    blocks = []
    for r in range(ROWS):
        for c in range(COLS):
            words = blocks_data.get((r, c), [])
            text = structure_block_by_line(words) if words else ''
            blocks.append({'r': r, 'c': c, 'text': text, 'words': words})

    heading_text = structure_block_by_line(heading_words_data) if heading_words_data else ''

    return {'heading_text': heading_text, 'blocks': blocks}

def extract_header_info(header_text):
    """
    Extract key details from page header text
    Supports both Assembly forms and Zilla Parishad forms
    """
    info = {
        'assembly_name': '',  # Or Election Dept
        'part_no': '',
        'polling_station': '',
        'polling_address': '',
        'revenue_village': '',
    }
    
    # 1. Extract Part Number (Priority)
    # Patters: "भाग क्रमांक : 45", "यादी भाग क्र. ६", "Part No. : 45"
    part_match = re.search(r'(?:भाग\s*क्रमांक|यादी\s*भाग\s*क्र\.?|Part\s*No\.?)\s*[:\s-]*([\d०-९]+)', header_text, re.IGNORECASE)
    if part_match:
        val = part_match.group(1).strip()
        info['part_no'] = val
        
    # 2. Extract Assembly / Election Division
    # Patterns: "विधानसभा मतदारसंघ : ...", "Assembly Constituency : ...", "निवडणूक विभाग : ..."
    region_match = re.search(r'(?:विधानसभा\s*मतदारसंघाचे\s*(?:क्रमांक)?|विधानसभा\s*मतदारसंघ|निवडणूक\s*विभाग|Assembly\s*Constituency)\s*[:\s-]*([^\n]+)', header_text, re.IGNORECASE)
    if region_match:
        raw_val = region_match.group(1).strip()
        if 'निर्वाचन' in raw_val:
            raw_val = raw_val.split('निर्वाचन')[0].strip()
        info['assembly_name'] = raw_val

    # 3. Extract Polling Station Name
    # Pattern: "मतदान केंद्र : ...", "Polling Station : ..."
    ps_match = re.search(r'(?:मतदान\s*केंद्र(?:निहाय)?|Polling\s*Station)\s*[:\s-]*([^\n]+)', header_text, re.IGNORECASE)
    if ps_match:
        raw_val = ps_match.group(1).strip()
        if 'पत्ता' in raw_val:
            raw_val = raw_val.split('पत्ता')[0].strip()
        if 'Address' in raw_val:
             raw_val = raw_val.split('Address')[0].strip()
        info['polling_station'] = raw_val
        
    # 4. Extract Polling Station Address
    addr_match = re.search(r'(?:पत्ता|Address)\s*[:\s-]*([^\n]+)', header_text, re.IGNORECASE)
    if addr_match:
        info['polling_address'] = addr_match.group(1).strip()

    return info

def extract_voter_from_block(text_block):
    """
    Extract voter information from a structured text block
    Uses robust label-to-label extraction to handle multi-line fields
    """
    voter = {
        'epic': '',
        'serial_no': '',
        'name_marathi': '',
        'name_english': '',
        'relation_type': 'Father',
        'relation_name_marathi': '',
        'relation_name_english': '',
        'house_no': '',
        'age': '',
        'gender': 'Male',
        'confidence': 85
    }
    
    # 1. Extract EPIC (Pattern: Exactly 3 letters + 7 digits = 10 characters)
    # Standard Indian EPIC format: ABC1234567
    # Common formats in PDFs: SRO7795768, JVW0954826, etc.
    epic_patterns = [
        r'\b[A-Z]{3}\d{7}\b',  # Standard: 3 letters + 7 digits (SRO7795768)
        r'\b[A-Z]{3}[\s/-]?\d{7}\b',  # With optional separator
        r'\b[A-Z]{3}[0-9O]{7}\b',  # Allow O that will be normalized to 0
        r'[A-Z]{2,4}\d{6,8}',  # Relaxed: 2-4 letters + 6-8 digits
        r'SML\d{7}',  # Specific: SML format (SML9025685, SML8112641)
        r'SR[O0]\d{7}',  # Specific: SRO format commonly used (SRO7795768)
        r'JVW\d{7}',  # Specific: JVW format
        r'CPV\d{7}',  # Specific: CPV format (CPV1020007, CPV1756956)
        r'[JLMN]VW\d{7}',  # Variations: JVW, LVW, MVW, NVW
        r'[A-Z]{2}[0-9]{8}',  # 2 letters + 8 digits (alternative format)
        r'[A-Z][A-Z0-9]{2}\d{7}',  # Mixed first 3 characters + 7 digits
    ]
    epic_val = ''
    for pat in epic_patterns:
        m = re.search(pat, text_block, re.IGNORECASE)
        if m:
            epic_val = normalize_epic_aggressive(m.group(0))
            if epic_val and len(epic_val) == 10:  # Must be exactly 10 chars
                break
    # Fallback: scan all alphanumeric tokens for 10-character EPICs
    if not epic_val:
        tokens = re.findall(r'[A-Za-z0-9]{8,15}', text_block)
        for t in tokens:
            nt = normalize_epic_aggressive(t)
            # Accept only if exactly 10 characters: 3 letters + 7 digits
            if nt and len(nt) == 10 and re.match(r'^[A-Z]{3}[0-9]{7}$', nt):
                epic_val = nt
                break
    # Additional fallback: Look for EPIC-like patterns with OCR errors
    if not epic_val:
        # Sometimes OCR reads "SR07795768" instead of "SRO7795768"
        partial_matches = re.findall(r'[A-Za-z0-9]{9,12}', text_block)
        for pm in partial_matches:
            nt = normalize_epic_aggressive(pm)
            if nt and len(nt) == 10 and re.match(r'^[A-Z]{3}[0-9]{7}$', nt):
                epic_val = nt
                break
    voter['epic'] = epic_val
    
    # 2. Extract Serial Number - Universal patterns for ALL templates
    # Templates:
    # - Boothwise: "1 SRO7728835" (serial + EPIC on same line)
    # - AC Wise: "1\nJVW0954826" (serial in box at top-left, EPIC at top-right)
    # - Wardwise: Similar to AC Wise
    # - Mahanagpalika: Similar to Wardwise
    
    serial_val = ''
    devanagari_map = {'०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
                     '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'}
    
    # Pattern 0 (HIGHEST PRIORITY): Standalone number on its own at very start
    # e.g., "10\n" or "10 \n" - the boxed serial number read separately
    serial_standalone = re.match(r'^(\d{1,3}|[०-९]{1,3})\s*$', text_block.split('\n')[0].strip() if '\n' in text_block else '')
    if serial_standalone:
        serial_val = serial_standalone.group(1)
    
    # Pattern 1: Serial at very start followed by EPIC (boothwise)
    # e.g., "1 SRO7728835" or "25 SRO8476228"
    if not serial_val:
        serial_epic_pattern = re.match(r'^\s*(\d{1,4}|[०-९]{1,4})\s+[A-Z]{2,4}', text_block)
        if serial_epic_pattern:
            serial_val = serial_epic_pattern.group(1)
    
    # Pattern 2: Serial at start, then newline, then EPIC (AC Wise / Wardwise)
    # e.g., "1\nJVW0954826" or "18\nSRO6566491"
    if not serial_val:
        serial_newline_epic = re.match(r'^\s*(\d{1,4}|[०-९]{1,4})\s*[\n\r]+\s*[A-Z]{2,4}', text_block)
        if serial_newline_epic:
            serial_val = serial_newline_epic.group(1)
    
    # Pattern 3: Serial at start of block followed by newline (standalone number in box)
    if not serial_val:
        serial_match_start = re.match(r'^\s*\[?(\d{1,4}|[०-९]{1,4})\]?\s*[\n\r]', text_block)
        if serial_match_start:
            serial_val = serial_match_start.group(1)
    
    # Pattern 4: Serial at very start followed by any whitespace
    if not serial_val:
        serial_match_broad = re.match(r'^\s*(\d{1,4}|[०-९]{1,4})(?:\s|$)', text_block)
        if serial_match_broad:
            candidate = serial_match_broad.group(1)
            # Only accept if it's a reasonable serial (1-9999)
            try:
                if int(candidate) <= 9999:
                    serial_val = candidate
            except:
                serial_val = candidate  # Devanagari digits will be converted later
    
    # Pattern 5: Look for a line that contains ONLY a 1-3 digit number
    # This catches boxes where serial is on its own line anywhere in first 3 lines
    if not serial_val:
        lines = text_block.split('\n')[:3]  # Check first 3 lines
        for line in lines:
            line_stripped = line.strip()
            if re.match(r'^(\d{1,3}|[०-९]{1,3})$', line_stripped):
                serial_val = line_stripped
                break
    
    # Pattern 6: Label-based patterns (e.g., "क्रमांक : 1", "Sr. No. 25")
    if not serial_val:
        serial_label = re.search(r'(?:क्रमांक|Serial\s*No\.?|Sr\.?\s*No\.?)\s*[:\s-]*(\d+|[०-९]+)', text_block, re.IGNORECASE)
        if serial_label:
            candidate = serial_label.group(1)
            if len(candidate) <= 4:  # Serial numbers are typically 1-4 digits
                serial_val = candidate
    
    # Pattern 7: Fallback - first number in first line if <=3 digits and not part of EPIC
    if not serial_val:
        first_line = text_block.split('\n')[0] if '\n' in text_block else text_block
        # Find first number that's NOT preceded by letters (to avoid 72 from SRO72...)
        first_num = re.search(r'(?<![A-Z])(\d{1,3}|[०-९]{1,3})(?![0-9])', first_line)
        if first_num:
            serial_val = first_num.group(1)
    
    # Convert Devanagari digits to English
    if serial_val:
        for dev, eng in devanagari_map.items():
            serial_val = serial_val.replace(dev, eng)
        voter['serial_no'] = serial_val
    
    # Helper to extract text between two markers
    def get_text_between(text, start_patterns, end_patterns):
        start_idx = -1
        end_idx = len(text)
        
        # Find start
        for pattern in start_patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                start_idx = m.end()
                break
        
        if start_idx == -1:
            return ""
            
        # Find nearest end after start
        substring = text[start_idx:]
        best_end_pos = len(substring)
        
        for pattern in end_patterns:
            m = re.search(pattern, substring, re.IGNORECASE)
            if m and m.start() < best_end_pos:
                best_end_pos = m.start()
                
        return substring[:best_end_pos].strip().replace('\n', ' ')

    # 3. Extract Name (Marathi)
    # Start: "Name", "Matdarache Nav", "Matdarache Purn :"
    name_start = [
        r'मतदाराचे\s*(?:पूर्ण)?\s*(?:नाव|नांव)?\s*[:\s-]',
        r'मतदाराचे\s+पूर्ण\s*[:\s-]',
        r'नाव\s*[:\s-]',
        r'Elector\'s\s*Name\s*[:\s-]'
    ]
    name_end = [
        r'(?:वडिलांचे|पतीचे|आईचे|वडीलांचे)\s*नाव', 
        r'Husband\'s\s*Name',
        r'Father\'s\s*Name',
        r'घर\s*क्रमांक',
        r'House\s*No',
        r'वय', 
        r'लिंग',
        r'Photo',
        r'Available'
    ]
    
    raw_name = get_text_between(text_block, name_start, name_end)
    
    # FALLBACK: If name not found by label, look for text BEFORE the relation label
    if not raw_name:
        # Find where relation starts
        rel_markers = [r'(?:वडिलांचे|पतीचे|आईचे|वडीलांचे)\s*नाव', r'Husband\'s', r'Father\'s', r'Mother\'s']
        for marker in rel_markers:
            m = re.search(marker, text_block)
            if m:
                # Take the text line(s) before this marker
                pre_text = text_block[:m.start()].strip()
                # Split by newlines and take the last non-empty line(s) that aren't serial/EPIC
                lines = [l.strip() for l in pre_text.split('\n') if l.strip()]
                # Usually name is the last significant chunk before relation
                # Filter out EPIC identifiers
                relevant_lines = [l for l in lines if not re.match(r'^[A-Z]{2,4}[/\d]', l)]
                if relevant_lines:
                     raw_name = relevant_lines[-1] # Take last line
                break

    if raw_name:
        # Remove colon/hyphen if leaked
        raw_name = re.sub(r'^[:\s-]+', '', raw_name)
        # Remove floating "नाव/नांव" labels at ends and anywhere as standalone tokens
        raw_name = re.sub(r'\s+(?:नाव|नांव)$', '', raw_name)
        raw_name = re.sub(r'^(?:नाव|नांव)\s+', '', raw_name)
        raw_name = re.sub(r'(?i)(?:^|\s)(?:नाव|नांव|नव|nav|nanv)(?:\s|$)', ' ', raw_name)
        # Strip separators like pipes/colons that leak from OCR layout
        raw_name = re.sub(r'[\|:]+', ' ', raw_name)
        # Remove * or ** (often used for deleted/duplicate)
        raw_name = re.sub(r'\*+', '', raw_name)
        # Collapse whitespace and trim
        raw_name = re.sub(r'\s+', ' ', raw_name).strip()
        voter['name_marathi'] = raw_name

    # 4. Extract Relation Name (Marathi) & Type
    # Determine type first
    rel_type_map = {
        r'पतीचे': 'Husband',
        r'Husband\'s': 'Husband',
        r'आईचे': 'Mother',
        r'Mother\'s': 'Mother',
        r'वडिलांचे': 'Father',
        r'वडीलांचे': 'Father',
        r'Father\'s': 'Father'
    }
    
    rel_marker = r'(?:वडिलांचे|वडीलांचे)\s*नाव'
    voter['relation_type'] = 'Father'
    
    for pattern, rtype in rel_type_map.items():
        if re.search(pattern, text_block, re.IGNORECASE):
             voter['relation_type'] = rtype
             rel_marker = pattern + r'\s*(?:नाव|Name)?'
             break

    rel_start = [rel_marker]
    rel_end = [r'घर', r'House', r'वय', r'Age', r'लिंग', r'Gender', r'Photo', r'Available']
    
    raw_rel = get_text_between(text_block, rel_start, rel_end)
    if raw_rel:
        raw_rel = re.sub(r'^[:\s-]+', '', raw_rel)
        raw_rel = re.sub(r'\*+', '', raw_rel).strip()
        voter['relation_name_marathi'] = raw_rel
        
    # 5. Extract House Number
    house_start = [r'घर\s*क्रमांक']
    house_end = [r'वय', r'लिंग', r'Photo']
    
    raw_house = get_text_between(text_block, house_start, house_end)
    if raw_house:
         # Remove colon/hyphen
        raw_house = re.sub(r'^[:\s-]+', '', raw_house)
        # Check for Ward No
        if 'Ward' in raw_house or 'No' in raw_house:
             # Keep it, it's valid address data
             pass
        voter['house_no'] = raw_house

    # 6. Extract Age
    age_match = re.search(r'वय\s*[:\s-]+\s*(\d+|[०-९]+)', text_block)
    if age_match:
        age_str = age_match.group(1)
        # Convert Devanagari digits to English
        devanagari_map = {'०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
                         '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'}
        for dev, eng in devanagari_map.items():
            age_str = age_str.replace(dev, eng)
        voter['age'] = age_str
    
    # 7. Extract Gender
    sex_match = re.search(r'लिंग\s*[:\s-]+\s*(स्त्री|पु|महिला|पुरुष)', text_block)
    if sex_match:
        sex_text = sex_match.group(1)
        voter['gender'] = 'Female' if ('स्त्री' in sex_text or 'महिला' in sex_text) else 'Male'
    
    return voter
