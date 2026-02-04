import cv2
import numpy as np
import json
import os

print("🚀 Handwriting Robot - Stroke Extractor READY!")
print("📁 Working: C:\\Users\\hp\\Desktop\\MITS\\Projects\\Handwriting Robot")

# Auto-create folders
os.makedirs("Stage1_scans", exist_ok=True)
os.makedirs("stroke_library", exist_ok=True)
os.makedirs("output_gcode", exist_ok=True)

print("✅ Folders: Stage1_scans/, stroke_library/, output_gcode/")
print("-" * 50)

def extract_strokes(image_path):
    """Photo → Robot strokes (OpenCV MAGIC!)"""
    print(f"🖊️ Processing: {image_path}")
    
    # Check file exists
    if not os.path.exists(image_path):
        print("❌ ERROR: No photo! Put 'a.jpg' in Stage1_scans/")
        return []
    
    # OpenCV: Photo → Black strokes on white
    img = cv2.imread(image_path, 0)  # Grayscale
    _, binary = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY_INV)
    
    # Find pen strokes (VECTOR PATHS!)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    strokes = []
    for contour in contours:
        path = contour.reshape(-1, 2).tolist()  # (x,y) points
        if len(path) > 10:  # Real stroke (not noise)
            strokes.append(path)
    
    # SAVE YOUR HANDWRITING!
    filename = image_path.split('/')[-1].split('.')[0]  # "a.jpg" → "a"
    stroke_data = {filename: strokes}
    
    with open(f'stroke_library/{filename}_strokes.json', 'w') as f:
        json.dump(stroke_data, f, indent=2)
    
    print(f"🎉 SUCCESS! Saved {len(strokes)} strokes for '{filename}'")
    print(f"📄 Created: stroke_library/{filename}_strokes.json")
    return strokes

# AUTO-TEST YOUR 'a'
print("\n🔍 Looking for Stage1_scans/a.jpg...")
if os.path.exists("Stage1_scans/a.jpg"):
    print("✅ Found a.jpg! Extracting strokes...")
    extract_strokes("Stage1_scans/a.jpg")
else:
    print("\n🚀 YOUR 60-SECOND MISSION:")
    print("1. WHITE paper + BLACK pen → Write HUGE 'a'")
    print("2. Clear photo → Drag to Stage1_scans/ → Rename 'a.jpg'")
    print("3. Ctrl+S this file → Right-click → Run → MAGIC!")

print("\n🎯 Ready when you are! Run again after adding a.jpg")
