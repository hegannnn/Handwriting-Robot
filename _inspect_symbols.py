"""Inspect special symbol stroke data."""
import json

lib = json.load(open('normalized_library.json'))
symbols = ['!', ',', ';', '-', '(', ')', '[', ']', '{', '}', '&', '%']

for c in symbols:
    if c in lib and lib[c] is not None:
        strokes = lib[c]['strokes']
        pts_per_stroke = [len(s) for s in strokes]
        total_pts = sum(pts_per_stroke)
        print(f"'{c}': {len(strokes)} strokes, points_per_stroke={pts_per_stroke}, total={total_pts}, width={lib[c]['width']}")
        # Show first few points of first stroke to check data quality
        if strokes and len(strokes[0]) >= 3:
            print(f"     first 3 pts: {strokes[0][:3]}")
            print(f"     last  3 pts: {strokes[0][-3:]}")
    else:
        print(f"'{c}': NOT FOUND or None in library")
