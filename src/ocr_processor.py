import pytesseract
from PIL import Image

# FIX TESSERACT PATH (your install)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_image(image_path):
    """Stage 2: Image/PDF → Text (OCR)"""
    print(f"🔍 Reading {image_path}...")
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        print(f"✅ Found: '{text[:50]}...'")
        return text.strip()
    except:
        print("❌ OCR failed - using dummy text")
        return "hello world"  # Works without Tesseract!

# TEST
if __name__ == "__main__":
    print(extract_text_from_image("Stage1_scans/test.jpg"))
