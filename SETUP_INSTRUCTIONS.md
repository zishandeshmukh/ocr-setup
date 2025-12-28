# Voter OCR - Setup Instructions

Follow these steps to set up and run the application on a new laptop (Uncle's Laptop).

## 1. Install Python
1. Download **Python 3.11** from [python.org/downloads](https://www.python.org/downloads/).
2. Run the installer.
3. **IMPORTANT:** Check the box **"Add Python to PATH"** before clicking Install.

## 2. Setup the Code Information
1. Download the code (Zip or Git Clone) to a folder, e.g., `Documents\VoterOCR`.
2. Open that folder.

## 3. Copy the Secret Key
1. Copy the file `google-cloud-vision-key.json` from your laptop.
2. Paste it directly into the `VoterOCR` folder (where `main.py` is located).
   > **Note:** The app will NOT work without this file.

## 4. Install Dependencies
1. Open the folder in File Explorer.
2. Type `cmd` in the address bar and press Enter to open Command Prompt.
3. Run the following command to install required libraries:
   ```bash
   pip install -r requirements.txt
   ```
   *If that finishes successfully, you are ready.*

## 5. Run the Application
In the same Command Prompt window, run:
```bash
python main.py
```

The application window should open.

---

## Troubleshooting
- **"python is not recognized"**: You didn't check "Add Python to PATH" during installation. Reinstall Python and check that box.
- **"ModuleNotFoundError"**: You skipped Step 4 (`pip install...`).
- **"Credentials file not found"**: You missed Step 3. The `google-cloud-vision-key.json` file must be in the same folder as `main.py`.
