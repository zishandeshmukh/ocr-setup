#!/usr/bin/env python3
"""
Build script for Voter OCR Desktop App
Creates standalone executable using PyInstaller
"""

import subprocess
import sys
import os

def build():
    """Build the executable"""
    print("🔨 Building Voter OCR Desktop App...")
    
    # PyInstaller command
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name=VoterOCR',
        '--onedir',
        '--console',  # Show console for debugging
        '--add-data=frontend;frontend',
        '--add-data=google-cloud-vision-key.json;.',
        '--hidden-import=webview',
        '--hidden-import=webview.platforms.winforms',
        '--hidden-import=clr',
        '--hidden-import=clr_loader',
        '--hidden-import=pythonnet',
        '--hidden-import=google.cloud.vision',
        '--hidden-import=google.cloud.vision_v1',
        '--hidden-import=google.api_core',
        '--hidden-import=google.auth',
        '--hidden-import=google.auth.transport.requests',
        '--hidden-import=google.oauth2',
        '--hidden-import=grpc',
        '--hidden-import=PIL',
        '--hidden-import=PIL.Image',
        '--hidden-import=openpyxl',
        '--hidden-import=fitz',
        '--clean',
        '--noconfirm',
        'main.py'
    ]
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    
    if result.returncode == 0:
        print("\n✅ Build complete!")
        print("📁 Executable is in: dist/VoterOCR/")
        print("🚀 Run: dist/VoterOCR/VoterOCR.exe")
    else:
        print(f"\n❌ Build failed with code: {result.returncode}")
    
    return result.returncode

if __name__ == '__main__':
    sys.exit(build())
