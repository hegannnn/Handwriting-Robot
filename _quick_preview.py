"""Quick runner — generates preview with all character types."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from word_assembler import assemble_human_hierarchy_text
from gcode_generator import strokes_to_gcode
import matplotlib.pyplot as plt

text = "Hello (World) {test} 50% done, yes; nice & quick-fox!"
strokes = assemble_human_hierarchy_text(text)
print(f"{len(strokes)} strokes assembled")
strokes_to_gcode(strokes, filename="my_handwriting")

# Show preview
fig, ax = plt.subplots(figsize=(8.27, 11.69))
fig.patch.set_facecolor("#fffef0")
ax.set_facecolor("#fffef0")
LINE_TOP, CAP_H, SPACING, DESC_DROP = 25, 7, 13, 2.0
for i in range(22):
    top = LINE_TOP + i * SPACING
    baseline = top + CAP_H
    desc = baseline + DESC_DROP
    if top > 297:
        break
    ax.axhline(top, color="#d0e4f0", linewidth=0.35, zorder=0)
    ax.axhline(baseline, color="#a0bcd8", linewidth=0.55, zorder=1)
    ax.axhline(desc, color="#d4c8e0", linewidth=0.35,
               linestyle="--", dashes=(4, 6), zorder=0)
ax.axvline(10, color="#f0b0b0", linewidth=0.5, zorder=0)
for stroke in strokes:
    xs = [p[0] for p in stroke]
    ys = [p[1] for p in stroke]
    ax.plot(xs, ys, color="#1a1a8c", linewidth=0.7,
            solid_capstyle="round", solid_joinstyle="round", zorder=2)
ax.set_aspect("equal")
ax.set_xlim(0, 210)
ax.set_ylim(297, 0)
ax.set_title(f'Smoothed Handwriting Preview  -  "{text}"', fontsize=9, pad=8)
ax.set_xlabel("X (mm)", fontsize=7)
ax.set_ylabel("Y (mm)", fontsize=7)
ax.tick_params(labelsize=7)
plt.tight_layout()
plt.show()
print("Done!")
