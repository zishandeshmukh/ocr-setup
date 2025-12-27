"""
Test script: Process the Boothwise sample PDF using the new calibrated template,
then save an Excel output to verify end-to-end extraction.
"""
import os
import json
from backend.api import API

SAMPLE_PDF = r"U:\\Downloads\\python-voter-ocr\\python-voter-ocr\\samples\\Boothwise\\BoothVoterList_A4_Ward_2_Booth_6.pdf"
OUTPUT_XLSX = r"U:\\Downloads\\python-voter-ocr\\python-voter-ocr\\voter_boothwise_test.xlsx"


def main():
    # Ensure credentials are set (expects environment to be configured)
    # os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'U:\\Downloads\\python-voter-ocr\\python-voter-ocr\\google-cloud-vision-key.json'

    api = API()
    api.set_template('boothwise')

    # Focus on early pages for verification (e.g., 3 to 6)
    result = api.process_pdf(SAMPLE_PDF, start_page=3, end_page=6)
    print("\n📈 Process result:")
    print(json.dumps({k: v for k, v in result.items() if k != 'voters'}, indent=2))

    if result.get('success'):
        api.update_data(result['voters'])
        exp = api.export_to_excel(OUTPUT_XLSX)
        print("\n📊 Export:")
        print(json.dumps(exp, indent=2))
    else:
        print("❌ Processing failed")


if __name__ == '__main__':
    main()
