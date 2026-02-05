import json
import matplotlib.pyplot as plt
import random

with open('normalized_library.json', 'r') as f:
    library = json.load(f)

def assemble_human_style(text, overlap_factor=0.2, jitter=1.5):
    current_x = 0
    assembled_strokes = []
    
    for char in text:
        if char == " ":
            current_x += 50
            continue
            
        if char in library:
            char_data = library[char]
            x_offset = current_x + random.uniform(-jitter, jitter)
            y_offset = random.uniform(-jitter, jitter)

            for stroke in char_data['strokes']:
                assembled_strokes.append([[p[0] + x_offset, p[1] + y_offset] for p in stroke])
            
            current_x += char_data['width'] * (1 - overlap_factor)
        else:
            print(f"Skipping: {char}")

    return assembled_strokes

user_text = input("Enter text for final neat version: ")
path = assemble_human_style(user_text, overlap_factor=0.22) 

plt.figure(figsize=(15, 3))
for stroke in path:
    plt.plot([p[0] for p in stroke], [p[1] for p in stroke], 'b-', linewidth=2)

plt.gca().set_aspect('equal')
plt.gca().invert_yaxis()
plt.title(f"Human-Style Preview: {user_text}")
plt.show()