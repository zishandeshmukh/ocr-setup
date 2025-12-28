# Voter OCR Desktop App

Extract Marathi voter data from PDFs with automatic Excel export. Supports 6 different PDF templates.

## 🚀 Quick Start (Executable)

**No installation required!**

1. Download `VoterOCR_Final_v2.zip`
2. Unzip to any folder
3. Double-click `VoterOCR.exe`

**Requirements:** Windows 10 or 11

---

## 📦 Setup from Source Code

### Prerequisites
- Python 3.11+
- Google Cloud Vision API key

### Step 1: Clone Repository
```bash
git clone https://github.com/zishandeshmukh/ocr-setup.git
cd ocr-setup
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Add API Key
Place your `google-cloud-vision-key.json` in the project root folder.

### Step 4: Run
```bash
python main.py
```

---

## 📋 Supported Templates

| Template | Description | PDF Format |
|----------|-------------|------------|
| **Boothwise** | मतदान केंद्र based | Standard booth list |
| **Mahanagarpalika** | महानगरपालिका format | Municipal corporation |
| **Wardwise** | प्रभाग wise data | Ward-based lists |
| **ZP Boothwise** | जिल्हा परिषद format | Zilla Parishad |
| **Boothlist Division** | निवडणूक विभाग | Election division |
| **AC Wise Low Quality** | विधानसभा मतदारसंघ | Assembly constituency |

---

## 🔧 Features

- ✅ **6 PDF Templates** - Supports all major voter list formats
- ✅ **Google Cloud Vision OCR** - High accuracy Marathi text extraction
- ✅ **Automatic Header Parsing** - Extracts Corporation, Ward, Part No, Address
- ✅ **EPIC Detection** - Robust voter ID extraction (SRO, JVW, CPV, SML formats)
- ✅ **Excel Export** - Template-specific columns with proper segregation
- ✅ **Batch Processing** - Process entire folders of PDFs
- ✅ **Modern UI** - Glassmorphism design with dark mode

---

## 📁 Project Structure

```
python-voter-ocr/
├── backend/
│   ├── api.py              # Main API with template configs
│   ├── ocr_engine.py       # Google Cloud Vision integration
│   ├── parser.py           # Text extraction & EPIC patterns
│   ├── corrections.py      # Marathi OCR corrections
│   ├── excel_export.py     # Template-specific Excel export
│   └── gemini_transliterate.py  # Marathi to English
├── frontend/
│   ├── index.html          # UI markup
│   ├── styles.css          # Styling
│   └── app.js              # Frontend logic
├── main.py                 # Application entry point
├── build_exe.py            # Build standalone executable
└── requirements.txt
```

---

## 🛠️ Building Executable

```bash
python build_exe.py
```

Output: `dist/VoterOCR/VoterOCR.exe`

To create a zip for distribution:
```bash
Compress-Archive -Path "dist\VoterOCR" -DestinationPath "VoterOCR.zip"
```

---

## 📊 Excel Output Columns

### Mahanagarpalika/Wardwise
| Column | Description |
|--------|-------------|
| Corporation | महानगरपालिका name |
| Ward | प्रभाग number |
| Part No | यादी भाग क्र |
| Address | पत्ता |
| EPIC | Voter ID |
| Name (Marathi/English) | Voter name |
| Relation Type | पती/वडील |
| Relation Name | Relative name |
| House No | घर क्रमांक |
| Age | वय |
| Gender | लिंग |

### AC Wise Low Quality
| Column | Description |
|--------|-------------|
| Assembly Constituency | विधानसभा मतदारसंघ |
| Division | विभाग |
| Part No | यादी भाग क्रमांक |
| EPIC | Voter ID |
| (+ standard voter fields) | |

---

## ⚠️ Troubleshooting

### "Credentials file not found"
- Ensure `google-cloud-vision-key.json` is in the app folder

### "Export error: template_config not defined"
- Update to latest code version

### App crashes on startup (uncle's laptop)
- Requires Windows 10/11 with WebView2 (usually pre-installed)

### EPIC showing "ERROR_MISSING_EPIC"
- Template margins may need adjustment for your PDF format

---

## 📝 License

MIT

---

## 🙏 Credits

- OCR Engine: Google Cloud Vision API
- UI Framework: PyWebView
- Transliteration: Google Gemini API (optional)
