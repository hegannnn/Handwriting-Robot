# AI Handwriting Robot

**Photo → Your Handwriting → Robot Drawing** (3-stage pipeline)

## Features
- OpenCV stroke extraction from photos
- JSON handwriting library (per-user)
- GRBL G-code generation (EasyDraw V2)
- Ethics safeguards (blocks "signature")
- PDF OCR bonus (Tesseract)

## Quick Demo (30 seconds)
```bash
pip install -r requirements.txt
python src/gcode_generator.py
# Type "aaa" → my_handwriting.gcode → UGS → Robot!
```
