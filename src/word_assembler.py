import json
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import gaussian_filter1d

# Load your master font data
with open('normalized_library.json', 'r') as f:
    library = json.load(f)

def apply_human_smoothing(stroke, sigma=0.8):
    if len(stroke) < 3: return stroke
    points = np.array(stroke)
    smooth_x = gaussian_filter1d(points[:, 0], sigma)
    smooth_y = gaussian_filter1d(points[:, 1], sigma)
    return np.column_stack((smooth_x, smooth_y)).tolist()

def assemble_human_hierarchy_text(text, line_height=12, char_padding=0.5):
    # BASE_SCALE is for Capital letters (~8.5mm)
    BASE_SCALE = 0.085 
    # LOWER_RATIO makes lowercase letters 75% the size of capitals
    LOWER_RATIO = 0.75
    
    PAGE_WIDTH_MM = 190
    current_x, current_y = 10, 20
    all_strokes = []
    
    words = text.split(' ')
    for word in words:
        word_width = 0
        for char in word:
            if char in library:
                is_cap = char.isupper()
                scale = BASE_SCALE if is_cap else (BASE_SCALE * LOWER_RATIO)
                word_width += (library[char]['width'] * scale) + char_padding
        
        if current_x + word_width > PAGE_WIDTH_MM:
            current_x = 10
            current_y += line_height
            
        for char in word:
            if char in library:
                char_data = library[char]
                is_cap = char.isupper()
                scale = BASE_SCALE if is_cap else (BASE_SCALE * LOWER_RATIO)
                
                # Align small letters to the bottom baseline
                y_shift = (BASE_SCALE * 100) * (1 - LOWER_RATIO) if not is_cap else 0

                for stroke in char_data['strokes']:
                    smoothed = apply_human_smoothing(stroke)
                    all_strokes.append([[p[0] * scale + current_x, 
                                          p[1] * scale + current_y + y_shift] for p in smoothed])
                
                current_x += (char_data['width'] * scale) + char_padding
        current_x += 4 
    return all_strokes

# --- THE TRIGGER BLOCK (Fixed) ---
if __name__ == "__main__":
    user_input = input("Enter text (Hierarchy & Smoothing Active): ")
    final_path = assemble_human_hierarchy_text(user_input)

    plt.figure(figsize=(8.27, 11.69)) 
    for stroke in final_path:
        plt.plot([p[0] for p in stroke], [p[1] for p in stroke], 
                 color='blue', linewidth=1, solid_capstyle='round')

    plt.gca().set_aspect('equal')
    plt.xlim(0, 210) 
    plt.ylim(297, 0) 
    plt.title("A4 Hierarchy Preview (1unit = 1mm)")
    plt.show()