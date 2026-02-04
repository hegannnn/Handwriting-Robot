#!/usr/bin/env python3
"""
🤖 MITS Handwriting Robot - FIXED VERSION
Works with your stroke_library/a_strokes.json (16KB)
"""
import json
import os

BLOCK_WORDS = ['signature', 'sign', 'sincerely']

def ethics_check(text):
    for word in BLOCK_WORDS:
        if word in text.lower():
            print(f"🚫 BLOCKED: '{word}' detected!")
            return False
    return True

def load_strokes(letter):
    path = f"stroke_library/{letter}_strokes.json"
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                strokes = data.get('strokes', [])
                if strokes and len(strokes) > 0:
                    print(f"✅ LOADED {letter}: {path}")
                    return strokes[0]  # Return first stroke
                else:
                    print(f"❌ Empty strokes in {path}")
        except Exception as e:
            print(f"❌ Error reading {path}: {e}")
    else:
        print(f"❌ File not found: {path}")
    return []

def generate_text_strokes(text):
    all_strokes = []
    x_offset = 0
    
    print(f"Processing text: '{text}'")
    for i, char in enumerate(text.lower()):
        print(f"  Looking for '{char}'...")
        stroke = load_strokes(char)
        if stroke:
            # Offset each letter 30mm apart
            offset_stroke = [(x + x_offset*30, y) for x, y in stroke]
            all_strokes.append(offset_stroke)
            x_offset += 1
            print(f"  ✅ Added '{char}' stroke")
        else:
            print(f"  ❌ No stroke for '{char}'")
    
    return all_strokes

def strokes_to_gcode(strokes, filename="handwriting"):
    if not strokes:
        print("❌ No strokes to convert!")
        return []
    
    gcode = ["G21", "G90", "G1 F1000"]  # mm units, absolute, speed
    
    for i, stroke in enumerate(strokes):
        if len(stroke) < 2:
            continue
        # Pen up, move to start
        gcode.append("M5")
        x0, y0 = stroke[0]
        gcode.append(f"G0 X{x0:.1f} Y{y0:.1f}")
        # Pen down, draw
        gcode.append("M3 S500")
        for x, y in stroke:
            gcode.append(f"G1 X{x:.1f} Y{y:.1f}")
        gcode.append("M5")  # Pen up
    
    gcode.extend(["G0 X0 Y0", "M2"])  # Home, end
    
    os.makedirs("output_gcode", exist_ok=True)
    filepath = f'output_gcode/{filename}.gcode'
    with open(filepath, 'w') as f:
        f.write('\n'.join(gcode))
    
    print(f"\n🚀 G-CODE SAVED: {filepath}")
    print(f"📏 {len(strokes)} strokes → Ready for UGS!")
    return gcode

if __name__ == "__main__":
    print("🤖 MITS Handwriting Robot v1.0")
    print("✅ Using stroke_library/a_strokes.json (16KB)")
    
    text = input("\n✍️ Enter text (try 'aaa'): ")
    
    if ethics_check(text):
        strokes = generate_text_strokes(text)
        strokes_to_gcode(strokes, "my_text")
    else:
        print("🚫 Blocked!")
