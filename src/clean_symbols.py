"""
Generate clean, mathematically-defined strokes for special symbols.
These replace the noisy skeleton-extracted data with smooth curves
that look like natural handwriting.

All coordinates are in normalised space: height = 100, origin = (0, 0).
"""

import numpy as np
import json
import os


def _arc(cx, cy, rx, ry, start_deg, end_deg, n=40):
    """
    Generate an elliptical arc.

    Coordinate system:  x→ right,  y→ DOWN  (y=0 top, y=100 bottom).
    Angle convention:
        0° = right  (+x)
       90° = down   (+y)
      180° = left   (-x)
      270° = up     (-y)
    """
    angles = np.linspace(np.radians(start_deg), np.radians(end_deg), n)
    xs = cx + rx * np.cos(angles)
    ys = cy + ry * np.sin(angles)
    return np.column_stack((xs, ys)).tolist()


def _line(x0, y0, x1, y1, n=10):
    """Generate a straight line with slight natural curve."""
    t = np.linspace(0, 1, n)
    # tiny sine wobble for human feel
    wobble = np.sin(t * np.pi) * 0.3
    xs = x0 + (x1 - x0) * t + wobble
    ys = y0 + (y1 - y0) * t
    return [[round(x, 2), round(y, 2)] for x, y in zip(xs, ys)]


def _round(pts):
    return [[round(x, 2), round(y, 2)] for x, y in pts]


def make_exclamation():
    """!  — vertical stroke + dot below."""
    # Main stroke: slight taper from top to ~75%
    stem = _line(3, 0, 2.5, 72, n=20)
    # Dot: small filled circle
    dot = _arc(3, 88, 3, 4, 0, 360, n=16)
    return {"strokes": [_round(stem), _round(dot)], "width": 6}


def make_comma():
    """,  — small curved tail."""
    pts = _arc(4, 75, 3, 12, -60, 200, n=20)
    return {"strokes": [_round(pts)], "width": 8}


def make_semicolon():
    """;  — dot on top + comma below."""
    dot = _arc(5, 30, 3, 3.5, 0, 360, n=16)
    tail = _arc(5, 70, 3, 15, -60, 200, n=20)
    return {"strokes": [_round(dot), _round(tail)], "width": 10}


def make_dash():
    """-  — simple horizontal stroke."""
    stroke = _line(0, 50, 35, 49, n=12)
    return {"strokes": [stroke], "width": 35}


def make_left_paren():
    """
    (  — smooth C-shaped curve opening to the right.
    Arc sweeps from upper-right → left bulge → lower-right.
    """
    # Center to the right so the left side of the arc draws the (
    # 270° = top, sweeps through 180° (left bulge) to 90° (bottom)
    pts = _arc(15, 50, 15, 50, 270, 90, n=40)
    return {"strokes": [_round(pts)], "width": 15}


def make_right_paren():
    """
    )  — smooth C-shaped curve opening to the left.
    Arc sweeps from upper-left → right bulge → lower-left.
    """
    # Center to the left so the right side of the arc draws the )
    # 270° = top, sweeps through 0° (right bulge) to 90° (bottom)
    pts = _arc(0, 50, 15, 50, -90, 90, n=40)
    return {"strokes": [_round(pts)], "width": 15}


def make_left_bracket():
    """[  — three connected straight segments."""
    top = _line(15, 2, 3, 2, n=6)
    side = _line(3, 2, 3, 98, n=15)
    bot = _line(3, 98, 15, 98, n=6)
    combined = top + side[1:] + bot[1:]
    return {"strokes": [combined], "width": 15}


def make_right_bracket():
    """]  — three connected straight segments."""
    top = _line(0, 2, 12, 2, n=6)
    side = _line(12, 2, 12, 98, n=15)
    bot = _line(12, 98, 0, 98, n=6)
    combined = top + side[1:] + bot[1:]
    return {"strokes": [combined], "width": 15}


def make_left_brace():
    """
    {  — two arcs meeting at a leftward point in the middle.
    Top half:  curves from top-right down to the left point at mid-height.
    Bottom half: curves from the left point down to bottom-right.
    """
    # Top half: start at top-right, curve left, end at middle-left point
    # Arc center right of glyph; 270° (top) sweeps to 180° (left point)
    top = _arc(18, 25, 14, 25, 270, 180, n=25)
    # Bottom half: start at middle-left point, curve left, end at bottom-right
    # Arc center right of glyph; 180° (left) sweeps to 90° (bottom)
    bot = _arc(18, 75, 14, 25, 180, 90, n=25)
    return {"strokes": [_round(top), _round(bot)], "width": 18}


def make_right_brace():
    """
    }  — mirror of left brace; two arcs meeting at a rightward point.
    """
    # Top half: start at top-left, curve right, end at middle-right point
    top = _arc(0, 25, 14, 25, 270, 360, n=25)
    # Bottom half: from middle-right point curving to bottom-left
    bot = _arc(0, 75, 14, 25, 0, 90, n=25)
    return {"strokes": [_round(top), _round(bot)], "width": 18}


def make_ampersand():
    """&  — stylised loop."""
    # Upper loop
    upper = _arc(22, 25, 14, 20, 30, 390, n=40)
    # Diagonal down-stroke connecting to lower tail
    diag = _line(33, 35, 8, 90, n=15)
    # Tail curl
    tail = _arc(18, 85, 14, 10, 140, 30, n=20)
    return {"strokes": [_round(upper), diag, _round(tail)], "width": 42}


def make_percent():
    """
    %  — two small circles with a diagonal slash.
    Top-left circle, diagonal line, bottom-right circle.
    Circles use equal rx/ry for proper round shape.
    """
    top_o = _arc(12, 18, 10, 10, 0, 360, n=28)
    diag = _line(30, 10, 8, 90, n=15)
    bot_o = _arc(28, 78, 10, 10, 0, 360, n=28)
    return {"strokes": [_round(top_o), diag, _round(bot_o)], "width": 40}


# ── Registry ─────────────────────────────────────────────────────
SYMBOL_GENERATORS = {
    '!': make_exclamation,
    ',': make_comma,
    ';': make_semicolon,
    '-': make_dash,
    '(': make_left_paren,
    ')': make_right_paren,
    '[': make_left_bracket,
    ']': make_right_bracket,
    '{': make_left_brace,
    '}': make_right_brace,
    '&': make_ampersand,
    '%': make_percent,
}


def get_clean_symbols():
    """Return a dict of clean symbol definitions ready to merge into the library."""
    return {char: gen() for char, gen in SYMBOL_GENERATORS.items()}


# ── Standalone: patch the normalised library ──────────────────────
if __name__ == "__main__":
    lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            '..', 'normalized_library.json')
    with open(lib_path, 'r') as f:
        lib = json.load(f)

    clean = get_clean_symbols()
    for char, data in clean.items():
        old_pts = sum(len(s) for s in lib.get(char, {}).get('strokes', []))
        new_pts = sum(len(s) for s in data['strokes'])
        lib[char] = data
        print(f"  '{char}': replaced ({old_pts} pts -> {new_pts} pts, width={data['width']})")

    with open(lib_path, 'w') as f:
        json.dump(lib, f, indent=2)
    print("\nSymbol library patched successfully!")
