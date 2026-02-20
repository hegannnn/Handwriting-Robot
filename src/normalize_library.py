import json
import os

LIBRARY_DIR = 'stroke_library'
OUTPUT_FILE = 'normalized_library.json'
TARGET_HEIGHT = 100.0

# ── Maximum allowed aspect ratio (width / height) per category ──
# In natural handwriting, most letters are roughly 0.5–0.9 wide.
# Characters wider than this limit will have their X compressed.
MAX_ASPECT_LOWER   = 1.00   # lowercase
MAX_ASPECT_UPPER   = 1.05   # uppercase (M, W can be wide)
MAX_ASPECT_SYMBOL  = 1.20   # symbols / digits
MAX_ASPECT_SPECIAL = {'m': 1.30, 'w': 1.20, 'M': 1.30, 'W': 1.20,
                      '-': 1.50, '%': 1.00, '&': 0.80}

# ── Ideal width table (as fraction of height=100) ──
# Used to gently guide severely distorted characters toward
# natural proportions.  Characters already within ±40 % of the
# target are left alone; only extreme outliers are rescaled.
IDEAL_WIDTH = {
    # lowercase
    'a': 65, 'b': 60, 'c': 55, 'd': 60, 'e': 55, 'f': 40,
    'g': 55, 'h': 60, 'i': 30, 'j': 35, 'k': 55, 'l': 30,
    'm': 90, 'n': 60, 'o': 55, 'p': 60, 'q': 60, 'r': 45,
    's': 50, 't': 40, 'u': 60, 'v': 55, 'w': 80, 'x': 55,
    'y': 50, 'z': 55,
    # uppercase
    'A': 75, 'B': 65, 'C': 65, 'D': 70, 'E': 60, 'F': 55,
    'G': 65, 'H': 75, 'I': 40, 'J': 45, 'K': 65, 'L': 60,
    'M': 90, 'N': 75, 'O': 70, 'P': 60, 'Q': 70, 'R': 65,
    'S': 55, 'T': 65, 'U': 70, 'V': 70, 'W': 90, 'X': 65,
    'Y': 60, 'Z': 60,
}


def _get_max_aspect(char_key):
    """Return the maximum allowed aspect ratio for a character."""
    if char_key in MAX_ASPECT_SPECIAL:
        return MAX_ASPECT_SPECIAL[char_key]
    if char_key.islower():
        return MAX_ASPECT_LOWER
    if char_key.isupper():
        return MAX_ASPECT_UPPER
    return MAX_ASPECT_SYMBOL


def normalize_letter(letter_data, name, char_key=None):
    """Normalize a character: scale height to TARGET_HEIGHT, cap width."""
    if char_key is None:
        char_key = name

    strokes = letter_data[name]
    all_pts = [pt for stroke in strokes for pt in stroke]
    if not all_pts:
        return None

    min_x = min(p[0] for p in all_pts)
    max_x = max(p[0] for p in all_pts)
    min_y = min(p[1] for p in all_pts)
    max_y = max(p[1] for p in all_pts)

    height = max_y - min_y
    width  = max_x - min_x
    scale_y = TARGET_HEIGHT / max(height, 1)

    # Start with uniform scale (preserving aspect ratio)
    scale_x = scale_y

    # ── Width capping ─────────────────────────────────────────
    raw_width = width * scale_x
    max_asp   = _get_max_aspect(char_key)
    max_width = TARGET_HEIGHT * max_asp

    # If an IDEAL_WIDTH exists and the raw width is way off (>50% error),
    # blend toward the ideal.
    ideal = IDEAL_WIDTH.get(char_key)
    if ideal is not None:
        if raw_width > ideal * 1.50:
            # Severely too wide → compress X to ideal + 15 % tolerance
            target_w = ideal * 1.15
            scale_x = target_w / max(width, 1)
        elif raw_width < ideal * 0.50:
            # Severely too narrow → stretch X to ideal - 15 %
            target_w = ideal * 0.85
            scale_x = target_w / max(width, 1)

    # Hard cap: never exceed max_aspect regardless
    final_width = width * scale_x
    if final_width > max_width:
        scale_x = max_width / max(width, 1)

    # ── Build normalised strokes ───────────────────────────────
    norm_strokes = []
    for stroke in strokes:
        norm_strokes.append([
            [round((p[0] - min_x) * scale_x, 2),
             round((p[1] - min_y) * scale_y, 2)]
            for p in stroke
        ])

    final_w = round(width * scale_x, 2)
    return {"strokes": norm_strokes, "width": final_w}


full_lib = {}
for filename in os.listdir(LIBRARY_DIR):
    if filename.endswith('_strokes.json'):
        raw_name = filename.split('_')[0]
        if len(raw_name) == 2 and raw_name.endswith('1'):
            char_key = raw_name[0].upper()
        else:
            char_key = raw_name

        with open(os.path.join(LIBRARY_DIR, filename), 'r') as f:
            try:
                data = json.load(f)
                full_lib[char_key] = normalize_letter(data, raw_name,
                                                       char_key=char_key)
                print(f"Mapped {raw_name} -> {char_key}")
            except Exception as e:
                print(f"Error mapping {raw_name}: {e}")

with open(OUTPUT_FILE, 'w') as f:
    json.dump(full_lib, f, indent=2)
print("\nNormalization complete! Master library created.")