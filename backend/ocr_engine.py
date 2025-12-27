"""
OCR Engine - Google Cloud Vision Integration
Based on OCR_Samruddhi's gcv_ocr.py
"""
from google.cloud import vision
import io
import os

class OCREngine:
    def __init__(self):
        """Initialize Google Cloud Vision client"""
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize GCV client with credentials"""
        try:
            # Credentials should be set via GOOGLE_APPLICATION_CREDENTIALS env var
            self.client = vision.ImageAnnotatorClient()
            print("✅ Google Cloud Vision client initialized")
        except Exception as e:
            print(f"⚠️ Error initializing GCV client: {e}")
            raise
    
    def run_ocr(self, image_path, max_retries=3):
        """
        Run Google Cloud Vision DOCUMENT_TEXT_DETECTION on image
        with retry logic for rate limiting errors.
        
        Args:
            image_path: Path to image file
            max_retries: Number of retry attempts for rate limit errors
            
        Returns:
            tuple: (full_text, word_annotations)
        """
        for attempt in range(max_retries):
            try:
                # Read image file
                with io.open(image_path, 'rb') as image_file:
                    content = image_file.read()
                
                image = vision.Image(content=content)
                
                # Call DOCUMENT_TEXT_DETECTION with language hints
                response = self.client.document_text_detection(
                    image=image,
                    image_context={
                        'language_hints': ['mr', 'hi', 'en']  # Marathi, Hindi, English
                    }
                )
                
                # Check for API error in response
                if response.error.message:
                    raise Exception(response.error.message)
                
                # Extract results
                full_text = response.text_annotations[0].description if response.text_annotations else ""
                word_annotations = response.text_annotations
                
                return full_text, word_annotations
                
            except Exception as e:
                error_str = str(e)
                # Check for rate limiting / server errors that are retryable
                is_retryable = any(code in error_str for code in ['503', '502', '429', 'UNAVAILABLE', 'rate limit'])
                
                if is_retryable and attempt < max_retries - 1:
                    import time
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    print(f"⏳ OCR rate limited, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                
                print(f"❌ OCR Error: {e}")
                return f"Error: {e}", None

    def run_ocr_block(self, image_path):
        """
        Run Google Cloud Vision TEXT_DETECTION on smaller cropped images (blocks)
        Returns (full_text, word_annotations)
        """
        try:
            with io.open(image_path, 'rb') as image_file:
                content = image_file.read()

            image = vision.Image(content=content)

            response = self.client.text_detection(image=image, image_context={'language_hints': ['mr', 'hi', 'en']})
            full_text = response.text_annotations[0].description if response.text_annotations else ""
            word_annotations = response.text_annotations
            return full_text, word_annotations
        except Exception as e:
            print(f"❌ OCR Block Error: {e}")
            return f"Error: {e}", None
