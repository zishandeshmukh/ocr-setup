"""
Voter OCR Desktop Application
Main entry point for PyWebView application
"""
import webview
import os
import sys
from dotenv import load_dotenv

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller bundle"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = sys._MEIPASS
    else:
        # Running as script
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# Add project root to path
if getattr(sys, 'frozen', False):
    sys.path.insert(0, sys._MEIPASS)
else:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Google Cloud credentials BEFORE importing API
credentials_path = get_resource_path('google-cloud-vision-key.json')
if os.path.exists(credentials_path):
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
    print(f"🔑 Credentials path: {credentials_path}")
else:
    print(f"⚠️ Credentials file not found: {credentials_path}")

# Load environment variables
load_dotenv()

# Import API
from backend.api import API

def main():
    """Main application entry point"""
    print("🚀 Starting Voter OCR Desktop App...")
    
    # Initialize API backend
    api = API()
    
    # Get frontend path
    frontend_path = get_resource_path(os.path.join('frontend', 'index.html'))
    
    # Create PyWebView window
    window = webview.create_window(
        title='Voter OCR Desktop App',
        url=frontend_path,
        js_api=api,
        width=1400,
        height=900,
        resizable=True,
        background_color='#1a1a2e',
        text_select=True
    )
    
    print("✅ Window created successfully")
    print("📍 Starting application...")
    
    # Start the application with EdgeChromium backend (avoids pythonnet/WinForms dependency)
    webview.start(debug=True, gui='edgechromium')

if __name__ == '__main__':
    main()
