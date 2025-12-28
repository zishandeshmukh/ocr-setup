import os
import sys
import glob

# Try to find site-packages
site_packages = next(p for p in sys.path if 'site-packages' in p)
print(f"Site packages: {site_packages}")

# Search for Python.Runtime.dll
search_pattern = os.path.join(site_packages, "**", "Python.Runtime.dll")
dlls = glob.glob(search_pattern, recursive=True)

if dlls:
    print(f"Found DLLs: {dlls}")
else:
    print("DLL not found via glob. Checking specific pythonnet location...")
    pythonnet_dir = os.path.join(site_packages, "pythonnet", "runtime")
    if os.path.exists(pythonnet_dir):
         print(f"Pythonnet runtime dir exists: {pythonnet_dir}")
         print(f"Contents: {os.listdir(pythonnet_dir)}")
