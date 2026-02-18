import cv2
import numpy as np
import json
import os
from skimage.morphology import skeletonize

INPUT_DIR = 'Stage1_scans'
OUTPUT_DIR = 'stroke_library'

def sort_points(points):
    """Sorts points so the pen follows a logical path (Nearest Neighbor)."""
    if not points: return []
    sorted_points = [points.pop(0)]
    while points:
        last_pt = sorted_points[-1]
        dists = np.sum((np.array(points) - last_pt)**2, axis=1)
        closest_idx = np.argmin(dists)
        if dists[closest_idx] > 50: 
             break 
        sorted_points.append(points.pop(closest_idx))
    return sorted_points, points

def extract_letter_data(image_path, letter_name):
    img = cv2.imread(image_path, 0)
    if img is None: 
        print(f"Skipping {image_path}: Could not read image.")
        return None
    
    _, binary = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)
    
    h, w = binary.shape
    margin = 10 
    if h > 2*margin and w > 2*margin:
        binary = binary[margin:h-margin, margin:w-margin]
    
    skeleton = skeletonize(binary / 255).astype(np.uint8)
    
    y_indices, x_indices = np.where(skeleton > 0)
    points = [[int(x), int(y)] for x, y in zip(x_indices, y_indices)]
    all_strokes = []
    remaining_points = points
    while len(remaining_points) > 15: 
        stroke, remaining_points = sort_points(remaining_points)
        if len(stroke) > 10: 
            all_strokes.append(stroke)
    
    return {letter_name: all_strokes}

if not os.path.exists(OUTPUT_DIR): 
    os.makedirs(OUTPUT_DIR)

for file in os.listdir(INPUT_DIR):
    if file.endswith(('.jpg', '.png', '.jpeg')):
        name = file.split('.')[0]
        print(f"Processing letter: {name}...")
        
        result = extract_letter_data(os.path.join(INPUT_DIR, file), name)
        
        if result and result[name]:
            output_path = os.path.join(OUTPUT_DIR, f"{name}_strokes.json")
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)

print("\nAll done! Now run normalize_library.py to fix the sizes.")