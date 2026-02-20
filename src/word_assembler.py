import json
import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d

# Import stroke smoother (works from repo root or src/ directory)
try:
    from src.stroke_smoother import smooth_stroke
except ImportError:
    from stroke_smoother import smooth_stroke

# Load master font data (support running from repo root or src/)
_HERE = os.path.dirname(os.path.abspath(__file__))
_LIB_PATH = os.path.join(_HERE, '..', 'normalized_library.json')
with open(_LIB_PATH, 'r') as f:
    library = json.load(f)

# ──────────────────────────────────────────────────────────────
# HUMAN-LIKE PROCESSING  HELPERS
# ──────────────────────────────────────────────────────────────

def add_micro_jitter(stroke, jitter=0.10):
    """
    Simulate natural hand tremor.
    Noise is tapered to zero at stroke endpoints (pen placement is
    more deliberate at the start/end of each stroke).
    """
    if len(stroke) < 3:
        return stroke
    points = np.array(stroke, dtype=float)
    n = len(points)
    # Taper: 0 at both ends, 1 in the middle
    taper = np.sin(np.linspace(0, np.pi, n))
    points[:, 0] += np.random.normal(0, jitter, n) * taper
    points[:, 1] += np.random.normal(0, jitter * 0.5, n) * taper
    return points.tolist()


def apply_forward_slant(stroke, shear=0.10):
    """
    Apply a forward cursive lean via horizontal shear.
    Shear is relative to each stroke's own y-centre so capital
    letters and small letters slant consistently.
    """
    if len(stroke) < 1:
        return stroke
    points = np.array(stroke, dtype=float)
    cy = float(np.mean(points[:, 1]))
    points[:, 0] += (points[:, 1] - cy) * shear
    return points.tolist()


def add_baseline_wobble(stroke, wobble=0.03):
    """
    Add a tiny random vertical shift per character stroke
    (ink line rides slightly above/below the baseline).
    """
    if len(stroke) < 1:
        return stroke
    points = np.array(stroke, dtype=float)
    points[:, 1] += np.random.uniform(-wobble, wobble)
    return points.tolist()


# ──────────────────────────────────────────────────────────────
# CHARACTER-CATEGORY SIZING  (natural handwriting proportions)
# ──────────────────────────────────────────────────────────────

# Descender letters: tails hang BELOW the baseline
DESCENDERS = set('fgjpqyz')

# Ascender letters: tall strokes reaching UP toward cap-height
# Note: 'f' is both an ascender AND a descender in many handwriting styles
ASCENDERS  = set('bdfhklt')

# Typical handwriting character-width table (fraction of cap_height).
# Used ONLY for cursor advancement (spacing), NOT for scaling the glyph.
# This ensures even spacing regardless of raw glyph proportions.
CHAR_WIDTH_TABLE = {
    'a': 0.55, 'b': 0.55, 'c': 0.50, 'd': 0.55, 'e': 0.50,
    'f': 0.40, 'g': 0.55, 'h': 0.55, 'i': 0.25, 'j': 0.30,
    'k': 0.50, 'l': 0.25, 'm': 0.80, 'n': 0.55, 'o': 0.55,
    'p': 0.55, 'q': 0.55, 'r': 0.40, 's': 0.45, 't': 0.35,
    'u': 0.55, 'v': 0.50, 'w': 0.75, 'x': 0.50, 'y': 0.50,
    'z': 0.50,
    'A': 0.70, 'B': 0.60, 'C': 0.65, 'D': 0.65, 'E': 0.55,
    'F': 0.55, 'G': 0.65, 'H': 0.70, 'I': 0.35, 'J': 0.40,
    'K': 0.60, 'L': 0.55, 'M': 0.85, 'N': 0.70, 'O': 0.70,
    'P': 0.55, 'Q': 0.70, 'R': 0.60, 'S': 0.55, 'T': 0.60,
    'U': 0.65, 'V': 0.65, 'W': 0.85, 'X': 0.60, 'Y': 0.55,
    'Z': 0.55,
    '0': 0.55, '1': 0.35, '2': 0.50, '3': 0.50, '4': 0.50,
    '5': 0.50, '6': 0.50, '7': 0.50, '8': 0.50, '9': 0.50,
    ',': 0.15, ';': 0.18, '!': 0.12, '-': 0.50,
    '(': 0.20, ')': 0.20, '[': 0.22, ']': 0.22,
    '{': 0.28, '}': 0.28, '&': 0.60, '%': 0.60,
}


# ──────────────────────────────────────────────────────────────
# MAIN ASSEMBLER
# ──────────────────────────────────────────────────────────────

def assemble_human_hierarchy_text(text, line_height=13, char_padding=0.3):
    """
    Convert a string into a list of positioned, human-naturalised
    stroke paths (each path is a list of [x, y] points in mm).

    Alignment strategy
    ──────────────────
    Every character is normalised to height = 100 in the library.
    At render time we scale that to real mm:
      • Capitals  → scale = BASE_SCALE           → 7.0 mm
      • Lowercase → scale = BASE_SCALE × 0.70    → 4.9 mm ≈ x-height

    The *baseline* is at  current_y + CAP_HEIGHT .
    Capital glyphs span  [current_y … current_y + CAP_HEIGHT].
    Lowercase glyphs span [baseline - x_height … baseline].
    Descenders extend below baseline.
    Ascenders are taller lowercase (scaled to ~90 % of cap height).

    Smoothing pipeline (per stroke):
      1. resample  → uniform arc-length spacing
      2. Chaikin   → geometric corner cutting (×3 iterations)
      3. cubic spline → C² continuous curves
      4. Gaussian  → final soft pass (σ = 1.6)
    """
    BASE_SCALE    = 0.07       # capital letters ≈ 7 mm
    LOWER_RATIO   = 0.70       # x-height / cap-height
    ASCENDER_RATIO = 0.90      # ascenders reach 90 % of cap height
    CAP_HEIGHT    = BASE_SCALE * 100          # 7.0 mm

    X_HEIGHT       = CAP_HEIGHT * LOWER_RATIO  # 4.9 mm
    ASCENDER_HT    = CAP_HEIGHT * ASCENDER_RATIO  # 6.3 mm
    DESCENDER_DROP = CAP_HEIGHT * 0.28         # ~2.0 mm below baseline

    PAGE_WIDTH_MM  = 190
    LEFT_MARGIN    = 10.0
    current_x      = LEFT_MARGIN
    current_y      = 25.0          # top of FIRST cap-height zone
    all_strokes    = []

    line_drift = 0.0

    words = text.split(' ')
    for word in words:
        # ── Estimate word width for line-wrapping ─────────────
        word_width = 0.0
        for char in word:
            cw = CHAR_WIDTH_TABLE.get(char, 0.55)
            word_width += cw * CAP_HEIGHT + char_padding

        if current_x + word_width > PAGE_WIDTH_MM:
            current_x  = LEFT_MARGIN
            current_y += line_height
            line_drift = np.random.uniform(-0.10, 0.10)

        for char in word:
            if char not in library or library[char] is None:
                continue

            char_data = library[char]
            is_cap    = char.isupper()
            ch_lower  = char.lower()

            # ── Determine scale & vertical anchor ─────────────
            # The glyph in the library occupies  y ∈ [0, 100].
            # We scale it so its rendered height matches the
            # appropriate zone, then shift it so its BOTTOM
            # sits on the baseline  (current_y + CAP_HEIGHT).
            #
            # DESCENDER LOGIC (g, j, p, q, y, f, z):
            #   The normalised glyph has body + tail in [0, 100].
            #   We scale the FULL glyph to  (X_HEIGHT + DESCENDER_DROP)
            #   and position it so the body top aligns with x-height
            #   top, letting the tail extend below the baseline.
            #   This mimics how humans write: the body sits at the
            #   same height as other lowercase, but the tail dips.

            # Per-character size micro-variation  (±1.5 %)
            size_var = 1.0 + np.random.uniform(-0.015, 0.015)

            baseline = current_y + CAP_HEIGHT

            is_descender = ch_lower in DESCENDERS
            is_ascender  = ch_lower in ASCENDERS

            if is_cap:
                char_height_mm = CAP_HEIGHT
                scale = char_height_mm / 100.0 * size_var
                glyph_top = baseline - scale * 100.0

            elif is_descender and is_ascender:
                # Letters like 'f' that are BOTH ascender and descender.
                # Total rendered height = ASCENDER_HT + DESCENDER_DROP
                # The glyph is stretched taller; top ~65% is the body
                # (ascender height) and bottom ~35% hangs below baseline.
                total_h = ASCENDER_HT + DESCENDER_DROP
                scale = total_h / 100.0 * size_var
                glyph_top = baseline - ASCENDER_HT * size_var

            elif is_descender:
                # g, j, p, q, y, z: body = x-height, tail below baseline
                total_h = X_HEIGHT + DESCENDER_DROP
                scale = total_h / 100.0 * size_var
                # Position so that the body top is at the x-height line
                glyph_top = baseline - X_HEIGHT * size_var
                # The glyph bottom = glyph_top + scale*100
                #                  = (baseline - X_HEIGHT) + (X_HEIGHT + DROP)
                #                  = baseline + DROP   → extends below ✓

            elif is_ascender:
                char_height_mm = ASCENDER_HT
                scale = char_height_mm / 100.0 * size_var
                glyph_top = baseline - scale * 100.0

            else:
                # Regular lowercase: body fills x-height zone
                char_height_mm = X_HEIGHT
                scale = char_height_mm / 100.0 * size_var
                glyph_top = baseline - scale * 100.0

            y_origin = glyph_top + line_drift

            for stroke in char_data['strokes']:
                if len(stroke) < 2:
                    continue

                # 1. Scale & position
                positioned = [
                    [p[0] * scale + current_x,
                     p[1] * scale + y_origin]
                    for p in stroke
                ]

                # 2. Full smoothing pipeline (clean→resample→Chaikin→spline→Gaussian)
                #    Applied to ALL characters: letters, numbers, symbols
                smoothed = smooth_stroke(
                    positioned,
                    resample_spacing=0.20,     # very tight resampling
                    chaikin_iters=3,           # 3 passes of corner cutting
                    spline_factor=2.5,         # dense cubic spline
                    gauss_sigma=2.0,           # strong Gaussian blur for silk-smooth curves
                )

                # 3. Forward cursive slant (gentle)
                slanted = apply_forward_slant(smoothed, shear=0.10)

                # 4. Very subtle micro-jitter (hand tremor)
                jittered = add_micro_jitter(slanted, jitter=0.08)

                # 5. Very subtle baseline wobble
                wobbled = add_baseline_wobble(jittered, wobble=0.03)

                all_strokes.append(wobbled)

            # ── Cursor advancement (standardised widths) ──────
            char_w = CHAR_WIDTH_TABLE.get(char, 0.55)
            current_x += char_w * CAP_HEIGHT * size_var + char_padding
            current_x += np.random.uniform(-0.02, 0.05)

        # Word gap
        current_x += CAP_HEIGHT * 0.50 + np.random.uniform(-0.10, 0.20)

    return all_strokes


# ──────────────────────────────────────────────────────────────
# STANDALONE PREVIEW (matplotlib A4 sheet)
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    user_input = input("Enter text to preview: ").strip()
    if not user_input:
        print("No text entered.")
    else:
        final_path = assemble_human_hierarchy_text(user_input)

        fig, ax = plt.subplots(figsize=(8.27, 11.69))
        fig.patch.set_facecolor('#fffef0')          # paper-like background
        ax.set_facecolor('#fffef0')

        for stroke in final_path:
            xs = [p[0] for p in stroke]
            ys = [p[1] for p in stroke]
            ax.plot(xs, ys, color='#1a1a8c', linewidth=0.9,
                    solid_capstyle='round', solid_joinstyle='round')

        ax.set_aspect('equal')
        ax.set_xlim(0, 210)
        ax.set_ylim(297, 0)
        ax.set_title(f'Human Handwriting Preview  —  "{user_input}"', fontsize=9)
        ax.axis('off')
        plt.tight_layout()
        plt.show()
