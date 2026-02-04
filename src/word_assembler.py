import json
import matplotlib.pyplot as plt

with open('normalized_library.json', 'r') as f:
    library = json.load(f)

def assemble_text(text, spacing=25):
    current_x = 0
    assembled_strokes = []
    for char in text: 
        if char == " ":
            current_x += 60
            continue
        if char in library:
            for stroke in library[char]['strokes']:
                assembled_strokes.append([[p[0]+current_x, p[1]] for p in stroke])
            current_x += library[char]['width'] + spacing
        else:
            print(f"Warning: Character '{char}' not in library.")
    return assembled_strokes

if __name__ == "__main__":
    text_to_show = input("Enter text (Case Sensitive): ")
    path = assemble_text(text_to_show)

    plt.figure(figsize=(12, 3))
    for stroke in path:
        plt.plot([p[0] for p in stroke], [p[1] for p in stroke], 'b-', linewidth=1.5)

    plt.gca().set_aspect('equal')
    plt.gca().invert_yaxis() 
    plt.show()