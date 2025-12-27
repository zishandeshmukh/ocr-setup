"""
Calibration Tool - Boothwise Template
Analyzes the sample Boothwise PDF to determine optimal template coordinates
with a focus on accuracy for voter block extraction.
"""
import fitz  # PyMuPDF
import os
import json
from statistics import median

try:
    from backend.ocr_engine import OCREngine
    from backend.parser import get_word_center
except Exception:
    # Fallback imports when run from different CWD
    from backend.ocr_engine import OCREngine
    from backend.parser import get_word_center

SAMPLE_PDF = r"U:\\Downloads\\python-voter-ocr\\python-voter-ocr\\samples\\Boothwise\\BoothVoterList_A4_Ward_2_Booth_6.pdf"
PREVIEW_IMG = r"U:\\Downloads\\python-voter-ocr\\python-voter-ocr\\samples\\Boothwise\\preview_boothwise.jpg"
TEMP_IMG = r"U:\\Downloads\\python-voter-ocr\\python-voter-ocr\\temp\\boothwise_page_1.jpg"


def percentile(values, pct):
    if not values:
        return 0
    values = sorted(values)
    k = (len(values) - 1) * pct
    f = int(k)
    c = min(f + 1, len(values) - 1)
    if f == c:
        return values[f]
    d0 = values[f] * (c - k)
    d1 = values[c] * (k - f)
    return d0 + d1


def calibrate_boothwise_template():
    if not os.path.exists(SAMPLE_PDF):
        print(f"❌ PDF not found: {SAMPLE_PDF}")
        return None

    print("📄 Opening Boothwise PDF for calibration…")
    pdf_doc = fitz.open(SAMPLE_PDF)
    page = pdf_doc[0]

    # Render first page at 300 DPI
    zoom = 300 / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    image_W, image_H = pix.width, pix.height

    # Save preview and temp image
    os.makedirs(os.path.dirname(PREVIEW_IMG), exist_ok=True)
    os.makedirs(os.path.dirname(TEMP_IMG), exist_ok=True)
    pix.save(PREVIEW_IMG, output='jpeg', jpg_quality=92)
    pix.save(TEMP_IMG, output='jpeg', jpg_quality=92)
    print(f"✅ Preview saved: {PREVIEW_IMG}")

    # Try OCR to locate internal labels for accurate content bounds
    ocr = None
    try:
        ocr = OCREngine()
    except Exception as e:
        print(f"⚠️ OCR init failed, using layout heuristics only: {e}")

    label_centers = []
    all_centers = []
    if ocr:
        full_text, word_annotations = ocr.run_ocr(TEMP_IMG)
        if word_annotations:
            # Skip first annotation (full text)
            for ann in word_annotations[1:]:
                word = (ann.description or '').strip()
                cx, cy = get_word_center(ann)
                all_centers.append((cx, cy, word))
                # Typical in-box labels that help bound content
                if any([
                    # Marathi labels
                    'वय' in word,
                    'लिंग' in word,
                    'घर' in word,
                    'नाव' in word or 'नांव' in word,
                    # English labels
                    'Age' in word,
                    'Gender' in word,
                    'House' in word,
                    "Elector's" in word,
                ]):
                    label_centers.append((cx, cy, word))
        else:
            print("⚠️ No word annotations returned; falling back to heuristics.")

    # Establish bounds
    left = right = top = bottom = None
    if all_centers:
        # Use all word centers in mid-band (exclude clear header/footer)
        usable = [(cx, cy) for cx, cy, w in all_centers if (image_H * 0.08) < cy < (image_H * 0.95)]
        if usable:
            xs = [cx for cx, cy in usable]
            ys = [cy for cx, cy in usable]
            min_x = int(percentile(xs, 0.02))
            max_x = int(percentile(xs, 0.98))
            min_y = int(percentile(ys, 0.05))
            max_y = int(percentile(ys, 0.98))
            pad_x = int(image_W * 0.015)
            pad_y = int(image_H * 0.015)
            left = max(min_x - pad_x, 0)
            right = max(image_W - (max_x + pad_x), 0)
            top = max(min_y - pad_y, 0)
            bottom = max(image_H - (max_y + pad_y), 0)
            print(f"📐 Bounds from words -> L:{left} R:{right} T:{top} B:{bottom}")
    
    if left is None:
        # Fallback margins if OCR/bounds failed
        left = int(image_W * 0.03)
        right = int(image_W * 0.03)
        top = int(image_H * 0.10)
        bottom = int(image_H * 0.06)
        print(f"📐 Heuristic bounds -> L:{left} R:{right} T:{top} B:{bottom}")

    # Grid estimation: Boothwise is typically 3 columns x 10 rows
    cols = 3
    rows = 10

    work_w = image_W - left - right
    work_h = image_H - top - bottom
    cell_w = work_w / cols
    cell_h = work_h / rows
    print(f"📊 Grid -> cols:{cols} rows:{rows} cell_w:{cell_w:.0f} cell_h:{cell_h:.0f}")

    template = {
        'name': 'Boothwise (Calibrated)',
        'left': left,
        'right': right,
        'top': top,
        'bottom': bottom,
        'rows': rows,
        'cols': cols,
        'photo_excl_width': 0,
        'skip_first_pages': 0,
        'skip_last_pages': 0,
        'min_word_annotations': 20,
        'min_valid_blocks_for_page': 2
    }

    print("\n✨ Recommended Boothwise Template:")
    print(json.dumps(template, indent=2))

    pdf_doc.close()
    # Cleanup temp image
    try:
        if os.path.exists(TEMP_IMG):
            os.remove(TEMP_IMG)
    except Exception:
        pass

    return template


if __name__ == '__main__':
    calibrate_boothwise_template()
