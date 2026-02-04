import json
import os

LIBRARY_DIR = 'stroke_library'
OUTPUT_FILE = 'normalized_library.json'
TARGET_HEIGHT = 100.0 

def normalize_letter(letter_data, name):
    strokes = letter_data[name]
    all_pts = [pt for stroke in strokes for pt in stroke]
    if not all_pts: return None

    min_x, max_x = min(p[0] for p in all_pts), max(p[0] for p in all_pts)
    min_y, max_y = min(p[1] for p in all_pts), max(p[1] for p in all_pts)
    
    height = max_y - min_y
    scale = TARGET_HEIGHT / max(height, 1)
    
    norm_strokes = []
    for stroke in strokes:
        norm_strokes.append([[round((p[0]-min_x)*scale, 2), 
                              round((p[1]-min_y)*scale, 2)] for p in stroke[::2]])
        
    return {"strokes": norm_strokes, "width": round((max_x-min_x)*scale, 2)}

full_lib = {}
for filename in os.listdir(LIBRARY_DIR):
    if filename.endswith('_strokes.json'):
        raw_name = filename.split('_')[0]
        
        # Mapping logic: 'a1' -> 'A', 'a' -> 'a'
        if len(raw_name) == 2 and raw_name.endswith('1'):
            char_key = raw_name[0].upper()
        else:
            char_key = raw_name
            
        with open(os.path.join(LIBRARY_DIR, filename), 'r') as f:
            try:
                data = json.load(f)
                full_lib[char_key] = normalize_letter(data, raw_name)
                print(f"Mapped {raw_name} -> {char_key}")
            except Exception as e:
                print(f"Error mapping {raw_name}: {e}")

with open(OUTPUT_FILE, 'w') as f:
    json.dump(full_lib, f, indent=2)
print("\nNormalization complete! Master library created.")