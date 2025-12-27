"""
API - PyWebView JavaScript API
Connects frontend to backend processing
"""
import webview
import os
import fitz  # PyMuPDF
import re
from PIL import Image as PILImage
from .ocr_engine import OCREngine
from .parser import parse_gcv_annotations, parse_gcv_blocks, extract_voter_from_block, extract_header_info, extract_page_header
from .corrections import apply_marathi_corrections, transliterate_marathi
from .gemini_transliterate import batch_transliterate_gemini
from .excel_export import export_to_excel
import json

# Load template
def load_template(template_name='boothlist_division'):
    """Load OCR template from config"""
    # Base template from OCR_Samruddhi template_300dpi.json (A4 @ 300 DPI)
    # Page size: 2480 x 3509
    boothlist_base = {
        'left': 61,
        'right': 85,
        'top': 390,
        'bottom': 168,
        'rows': 10,
        'cols': 3,
        'photo_excl_width': 0,
        'skip_first_pages': 0,
        'skip_last_pages': 0,
        'min_word_annotations': 20,
        'min_valid_blocks_for_page': 2
    }
    
    ac_wise_calibrated = {
        'left': 50,      # Reduced from 65 to capture left side
        'right': 50,     # Reduced from 85 to capture EPIC at right edge
        'top': 80,       # Reduced from 117 to capture EPIC at top of blocks
        'bottom': 60,    # Adjusted for better block sizing
        'rows': 10,
        'cols': 3,
        'photo_excl_width': 0,
        'name': 'AC Wise Low Quality',
        'skip_first_pages': 0,
        'skip_last_pages': 0,
        'min_word_annotations': 15,  # Reduced from 20 to accept more pages
        'min_valid_blocks_for_page': 1
    }
    
    templates = {
        'boothlist_division': boothlist_base,
        'Assembly_Standard': boothlist_base,  # backward compatibility
        'assembly_standard': boothlist_base,
        'ac_wise_low_quality': ac_wise_calibrated,  # ✅ Calibrated
        # ✅ Boothwise - Calibrated from empirical analysis (5 sample pages)
        'boothwise': {
            'left': 65,
            'right': 306,
            'top': 313,
            'bottom': 254,
            'rows': 10,
            'cols': 3,
            'photo_excl_width': 0,
            'skip_first_pages': 0,
            'skip_last_pages': 0,
            'min_word_annotations': 20,
            'min_valid_blocks_for_page': 2
        },
        # ✅ ZP Boothwise - Recalibrated using EPIC Y-position analysis
        # EPICs are at top of blocks. Analysis shows:
        # - 30 EPICs detected (10 rows x 3 cols)
        # - Row Y-positions: 422, 717, 1013, 1306, 1601, 1897, 2190, 2485, 2781, 3076
        # - Average row spacing: ~294 px
        # - Adjusted top margin to align first row, bottom to fit 10 rows
        'zp_boothwise': {
            'left': 65,
            'right': 366,
            'top': 390,      # Adjusted from 380 to align with first EPIC at y=421
            'bottom': 138,   # Adjusted to give 10 rows × 294px spacing
            'rows': 10,
            'cols': 3,
            'photo_excl_width': 0,
            'skip_first_pages': 0,
            'skip_last_pages': 0,
            'min_word_annotations': 20,
            'min_valid_blocks_for_page': 2
        },
        # ✅ Wardwise - Calibrated using EPIC position analysis from page 3
        # Analysis shows:
        # - 5 rows detected on sample page (partial data)
        # - Row Y-positions: 364.5, 658.5, 952.0, 1246.8, 1543.0
        # - Average row spacing: 294.4 px (same as ZP Boothwise)
        # - Column X-positions: 442, 1218, 1996
        # - Same page dimensions as ZP Boothwise (2480 x 3509 px)
        # - Margins calculated for 10-row grid with 294px spacing
        'wardwise': {
            'left': 65,
            'right': 275,
            'top': 334,      # First EPIC at y=364.5, ~30px buffer above
            'bottom': 231,   # Calculated for 10 rows × 294px = 2944px usable height
            'rows': 10,
            'cols': 3,
            'photo_excl_width': 0,
            'skip_first_pages': 0,
            'skip_last_pages': 0,
            'min_word_annotations': 20,
            'min_valid_blocks_for_page': 1
        }
    }
    # Add alias for wardwise
    templates['ward_wise_data'] = templates['wardwise']
    
    # ✅ Mahanagarpalika - Calibrated using EPIC position analysis
    # Analysis shows (page 3 of DraftList_Ward_11.pdf):
    # - 10 rows detected with 26 EPICs (some rows have 2 EPICs)
    # - Row Y-positions: 364.5, 658.2, 953.0, 1246.8, 1541.8, 1837.2, 2132.0, 2427.0, 2720.8, 3017.2
    # - Average row spacing: 294.8 px (consistent with other templates)
    # - Column X-positions: 444, 1222, 1998
    # - Layout nearly identical to Wardwise template
    templates['mahanagpalika'] = {
        'left': 65,
        'right': 274,
        'top': 333,      # First EPIC at y=363.5, ~30px buffer above
        'bottom': 228,   # Calculated for 10 rows × 294.8px spacing
        'rows': 10,
        'cols': 3,
        'photo_excl_width': 0,
        'skip_first_pages': 0,
        'skip_last_pages': 0,
        'min_word_annotations': 20,
        'min_valid_blocks_for_page': 1,
        'name': 'Mahanagarpalika'
    }
    
    return templates.get(template_name, boothlist_base)

class API:
    """PyWebView API - Exposed to JavaScript frontend"""
    
    def __init__(self):
        """Initialize API with OCR engine"""
        print("🔧 Initializing API...")
        self.ocr_engine = OCREngine()
        self.current_data = []
        self.template = load_template()
        self.current_template_key = 'boothlist_division'
        # Progress tracking for frontend
        self.progress_messages = []
        self.processing_status = {
            'is_processing': False,
            'current_page': 0,
            'total_pages': 0,
            'current_file': '',
            'voters_found': 0
        }
        print("✅ API initialized")
    
    def add_progress(self, message, page=None, total=None, voters=None):
        """Add a progress message for frontend"""
        self.progress_messages.append(message)
        if page is not None:
            self.processing_status['current_page'] = page
        if total is not None:
            self.processing_status['total_pages'] = total
        if voters is not None:
            self.processing_status['voters_found'] = voters
        # Keep only last 50 messages
        if len(self.progress_messages) > 50:
            self.progress_messages = self.progress_messages[-50:]
    
    def get_progress(self):
        """Get current progress for frontend polling"""
        return {
            'messages': self.progress_messages[-20:],  # Last 20 messages
            'status': self.processing_status
        }
    
    def clear_progress(self):
        """Clear progress messages"""
        self.progress_messages = []
        self.processing_status = {
            'is_processing': False,
            'current_page': 0,
            'total_pages': 0,
            'current_file': '',
            'voters_found': 0
        }

    def set_template(self, template_key):
        """Set OCR template from frontend dropdown"""
        try:
            self.template = load_template(template_key)
            self.current_template_key = template_key
            print(f"📐 Template set: {template_key}")
            return {'success': True, 'template': template_key}
        except Exception as e:
            print(f"❌ Failed to set template: {e}")
            return {'success': False, 'error': str(e)}
    
    def select_pdf(self):
        """Open file dialog to select PDF"""
        try:
            result = webview.windows[0].create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=False,
                file_types=('PDF Files (*.pdf)',)
            )
            return result[0] if result else None
        except Exception as e:
            print(f"❌ Error selecting file: {e}")
            return None

    def select_folder(self):
        """Open folder dialog"""
        try:
            result = webview.windows[0].create_file_dialog(
                webview.FOLDER_DIALOG,
                allow_multiple=False
            )
            return result[0] if result else None
        except Exception as e:
            print(f"❌ Error selecting folder: {e}")
            return None

    def process_batch(self, folder_path):
        """Process all PDFs in a folder - creates individual Excel files for each PDF"""
        try:
            print(f"📂 Batch processing folder: {folder_path}")
            pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
            
            total_files = len(pdf_files)
            print(f"Found {total_files} PDF files")
            
            if total_files == 0:
                return {'success': False, 'error': 'No PDF files found in folder'}
            
            all_voters = []
            processed_files = []
            failed_files = []
            
            for i, filename in enumerate(pdf_files, 1):
                pdf_path = os.path.join(folder_path, filename)
                print(f"[{i}/{total_files}] Processing {filename}...")
                
                # Reuse process_pdf logic but internal call
                result = self._process_single_pdf(pdf_path)
                
                if result['success'] and result['voters']:
                    voters = result['voters']
                    all_voters.extend(voters)
                    
                    # Create individual Excel file for this PDF
                    excel_filename = os.path.splitext(filename)[0] + '.xlsx'
                    excel_path = os.path.join(folder_path, excel_filename)
                    
                    try:
                        export_to_excel(voters, excel_path, template=self.current_template_key)
                        print(f"   ✅ Exported {len(voters)} voters to {excel_filename}")
                        processed_files.append({
                            'pdf': filename,
                            'excel': excel_filename,
                            'voters': len(voters)
                        })
                    except Exception as export_err:
                        print(f"   ❌ Export failed for {filename}: {export_err}")
                        failed_files.append({'file': filename, 'error': str(export_err)})
                else:
                    error_msg = result.get('error', 'No voters found')
                    print(f"   ⚠️ Skipped {filename}: {error_msg}")
                    failed_files.append({'file': filename, 'error': error_msg})
            
            self.current_data = all_voters
            
            # Summary
            print(f"\n{'='*50}")
            print(f"📊 Batch Processing Summary:")
            print(f"   Total PDFs: {total_files}")
            print(f"   Successful: {len(processed_files)}")
            print(f"   Failed: {len(failed_files)}")
            print(f"   Total voters: {len(all_voters)}")
            print(f"{'='*50}")
            
            return {
                'success': True,
                'total_voters': len(all_voters),
                'total_files': total_files,
                'processed_files': len(processed_files),
                'failed_files': len(failed_files),
                'files_detail': processed_files,
                'voters': all_voters
            }
        except Exception as e:
            print(f"❌ Batch error: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}

    def process_pdf(self, pdf_path, start_page=None, end_page=None):
        """Public wrapper for single PDF processing with optional page range"""
        return self._process_single_pdf(pdf_path, start_page=start_page, end_page=end_page)

    def _process_single_pdf(self, pdf_path, start_page=None, end_page=None):
        """Internal PDF processing logic with Header Extraction"""
        try:
            filename = os.path.basename(pdf_path)
            print(f"📄 Processing PDF: {pdf_path}")
            self.add_progress(f"📄 Processing: {filename}")
            
            # Open PDF with PyMuPDF
            print("🖼️ Opening PDF...")
            pdf_document = fitz.open(pdf_path)
            page_count = pdf_document.page_count
            print(f"✅ PDF has {page_count} pages")
            self.add_progress(f"✅ PDF has {page_count} pages", total=page_count)
            self.processing_status['is_processing'] = True
            self.processing_status['current_file'] = filename
            
            all_voters = []
            temp_dir = 'temp'
            os.makedirs(temp_dir, exist_ok=True)
            
            # Global extraction order counter - ensures deterministic ordering
            extraction_order = 0
            
            # Process each page
            min_words = self.template.get('min_word_annotations', 0)

            # Determine page range
            sp = max(0, (start_page - 1)) if isinstance(start_page, int) and start_page >= 1 else 0
            ep = min(page_count, end_page) if isinstance(end_page, int) and end_page and end_page >= 1 else page_count
            for page_num in range(sp, ep):
                print(f"📃 Processing page {page_num + 1}/{page_count}...")
                self.add_progress(f"📃 Processing page {page_num + 1}/{page_count}...", page=page_num + 1)
                
                # Get page
                page = pdf_document[page_num]
                
                # Render page to image at 300 DPI
                zoom = 300 / 72
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                
                # Save image temporarily
                temp_image_path = os.path.join(temp_dir, f'page_{page_num + 1}.jpg')
                pix.save(temp_image_path, output="jpeg", jpg_quality=95)
                
                # Get image dimensions
                image_W, image_H = pix.width, pix.height
                
                try:
                    # Run OCR
                    full_text, word_annotations = self.ocr_engine.run_ocr(temp_image_path)
                    
                    # Small delay to prevent rate limiting on large PDFs
                    import time
                    time.sleep(0.3)  # 300ms delay between pages
                    
                    if not word_annotations or len(word_annotations) < min_words:
                        msg = f"⏭️ Skipping page {page_num + 1} - low/empty text"
                        print(msg)
                        self.add_progress(msg)
                        continue
                    
                    # Parse into explicit blocks for stricter presence checks
                    parsed = parse_gcv_blocks(
                        word_annotations,
                        image_W,
                        image_H,
                        self.template
                    )
                    
                    # Extract page-level header (administrative context for all voters on this page)
                    page_header = extract_page_header(
                        word_annotations,
                        image_W,
                        image_H,
                        self.template
                    )
                    
                    header_info = {}
                    is_cover_by_keywords = False
                    if parsed.get('heading_text'):
                        header_text = parsed['heading_text']
                        header_info = extract_header_info(header_text)
                        cover_keywords = [
                            'Alphabetical Index', 'Index', 'Summary', 'Certificate', 'Instructions',
                            'अक्षरानुक्रम', 'अनुक्रमणिका', 'सूची', 'प्रमाणपत्र', 'सूचना'
                        ]
                        is_cover_by_keywords = any(kw.lower() in header_text.lower() for kw in cover_keywords)
                        print(f"   🏛️ Header Info: {header_info.get('part_no', 'N/A')} | cover_kw={is_cover_by_keywords}")

                    blocks_list = parsed.get('blocks', [])
                    if not blocks_list:
                        print(f"⏭️ Skipping page {page_num + 1} - no voter blocks detected")
                        continue

                    valid_voters_on_page = []
                    total_blocks_on_page = len(blocks_list)
                    min_valid_blocks_for_page = self.template.get('min_valid_blocks_for_page', 2)

                    # Evaluate each block using label hits and presence signals (data-driven)
                    for block_idx, block in enumerate(blocks_list):
                        text = block.get('text', '')
                        if not text.strip():
                            continue
                        voter = extract_voter_from_block(text)
                        
                        # Merge existing header info (part_no, etc.)
                        voter.update(header_info)
                        
                        # Attach page-level header to this voter record
                        voter['header_district'] = page_header.get('district', '')
                        voter['header_taluka'] = page_header.get('taluka', '')
                        voter['header_booth'] = page_header.get('booth', '')
                        voter['header_constituency'] = page_header.get('constituency', '')
                        voter['header_office'] = page_header.get('office', '')
                        voter['header_raw_text'] = page_header.get('raw_header_text', '')

                        # Apply corrections to Marathi names
                        voter['name_marathi'] = apply_marathi_corrections(voter['name_marathi'])
                        voter['relation_name_marathi'] = apply_marathi_corrections(voter['relation_name_marathi'])

                        # Transliteration will be done in batch after collecting all voters on page

                        # Add page number
                        voter['page_number'] = page_num + 1

                        # Validity signals
                        has_id_signal = bool(voter.get('epic')) or bool(voter.get('serial_no'))
                        has_demo_signal = bool(voter.get('age')) and bool(voter.get('gender'))
                        has_person_signal = bool(voter.get('name_marathi')) or bool(voter.get('relation_name_marathi'))

                        # Label hits inside block to reduce header false positives
                        label_hits = 0
                        age_label = bool(re.search(r'वय|Age', text))
                        gender_label = bool(re.search(r'लिंग|Gender', text))
                        house_label = bool(re.search(r'घर\s*क्रमांक|House\s*No', text))
                        name_label = bool(re.search(r'नाव|Elector\'s\s*Name', text))
                        photo_label = bool(re.search(r'Photo|Available', text))
                        label_hits += 1 if age_label else 0
                        label_hits += 1 if gender_label else 0
                        label_hits += 1 if house_label else 0
                        label_hits += 1 if name_label else 0
                        # Count lines/words to avoid accepting empty boxes
                        text_lines = [ln for ln in text.split('\n') if ln.strip()]
                        words_count = len(re.findall(r"\w+", text))

                        # Accept if block contains at least two labels OR strong signals
                        # AND EPIC must be present (voter lists always have EPIC)
                        has_epic = bool(voter.get('epic')) and str(voter.get('epic')).strip() != ''
                        
                        if label_hits >= 2 or (has_id_signal and has_demo_signal) or (has_person_signal and has_demo_signal):
                            # Only accept if EPIC is present OR mark as error for review
                            if not has_epic:
                                # If strong person/demo signals exist but no EPIC, mark for review
                                if (has_person_signal and has_demo_signal) or label_hits >= 3:
                                    voter['epic'] = 'ERROR_MISSING_EPIC'
                                    voter['confidence'] = 0
                                    voter['extraction_order'] = extraction_order
                                    extraction_order += 1
                                    valid_voters_on_page.append(voter)
                                # Otherwise reject the block (likely OCR noise)
                            else:
                                # Normal case: EPIC present
                                voter['extraction_order'] = extraction_order
                                extraction_order += 1
                                valid_voters_on_page.append(voter)

                    # Page-level cover detection and acceptance rules
                    is_cover_page = bool(parsed.get('heading_text')) and is_cover_by_keywords
                    is_first_page = (page_num == 0)

                    if is_cover_page:
                        print(f"⏭️ Skipping page {page_num + 1} - cover page detected | candidate={total_blocks_on_page}")
                        continue

                    is_first_page = (page_num == 0)

                    if not valid_voters_on_page:
                        print(f"⏭️ Skipping page {page_num + 1} - no valid voters detected | candidate={total_blocks_on_page}")
                        continue

                    # Apply stricter minimum only for the first page
                    if is_first_page and len(valid_voters_on_page) < min_valid_blocks_for_page:
                        print(f"⏭️ Skipping page {page_num + 1} - first-page minimum valid blocks not met (valid={len(valid_voters_on_page)} < min={min_valid_blocks_for_page})")
                        continue

                    # Batch transliterate all names on this page using Gemini (FAST)
                    if valid_voters_on_page:
                        all_names = [v.get('name_marathi', '') for v in valid_voters_on_page]
                        all_relations = [v.get('relation_name_marathi', '') for v in valid_voters_on_page]
                        
                        # Batch translate - one API call for all names on page
                        try:
                            translated_names = batch_transliterate_gemini(all_names)
                            translated_relations = batch_transliterate_gemini(all_relations)
                            
                            for i, voter in enumerate(valid_voters_on_page):
                                voter['name_english'] = translated_names[i] if i < len(translated_names) else ''
                                voter['relation_name_english'] = translated_relations[i] if i < len(translated_relations) else ''
                        except Exception as e:
                            print(f"⚠️ Batch translation failed: {e}, using fallback")
                            for voter in valid_voters_on_page:
                                voter['name_english'] = transliterate_marathi(voter.get('name_marathi', ''))
                                voter['relation_name_english'] = transliterate_marathi(voter.get('relation_name_marathi', ''))
                    
                    all_voters.extend(valid_voters_on_page)
                    msg = f"✅ Page {page_num + 1}: {len(valid_voters_on_page)} voters found"
                    print(msg)
                    self.add_progress(msg, voters=len(all_voters))
                    
                finally:
                    # Clean up temp image
                    if os.path.exists(temp_image_path):
                        os.remove(temp_image_path)
            
            # Close PDF
            pdf_document.close()
            
            # Store current data
            self.current_data = all_voters
            
            # Integrity check: ensure data consistency
            if len(all_voters) == 0:
                print("⚠️ Warning: No voters extracted from PDF")
            
            print(f"🎉 Processing complete! Total voters: {len(all_voters)}")
            self.add_progress(f"🎉 Complete! Total: {len(all_voters)} voters", voters=len(all_voters))
            self.processing_status['is_processing'] = False
            
            return {
                'success': True,
                'total_voters': len(all_voters),
                'total_pages': page_count,
                'voters': all_voters
            }
            
        except Exception as e:
            print(f"❌ Error processing PDF: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def export_to_excel(self, output_path):
        """
        Export current data to Excel
        
        Args:
            output_path: Path to save Excel file
            
        Returns:
            dict: Export result
        """
        try:
            if not self.current_data:
                return {
                    'success': False,
                    'error': 'No data to export'
                }
            
            print(f"📊 Exporting {len(self.current_data)} voters to Excel (template: {self.current_template_key})...")
            export_to_excel(self.current_data, output_path, template=self.current_template_key)
            print(f"✅ Excel exported: {output_path}")
            
            return {
                'success': True,
                'path': output_path,
                'count': len(self.current_data)
            }
            
        except Exception as e:
            print(f"❌ Export error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_current_data(self):
        """Get currently loaded voter data"""
        return self.current_data

    def update_data(self, new_data):
        """Update current data from frontend (e.g. after edits)"""
        print(f"🔄 Updating backend data: {len(new_data)} records")
        self.current_data = new_data
        return {'success': True}
