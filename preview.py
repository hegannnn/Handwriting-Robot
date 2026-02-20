"""
Matplotlib handwriting preview — A4 paper with ruled lines.
Usage:  python preview.py "Your text here"
        python preview.py          (prompts for text)
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from word_assembler import assemble_human_hierarchy_text
import matplotlib.pyplot as plt

# ── Text input ────────────────────────────────────────────────
if len(sys.argv) > 1:
    text = " ".join(sys.argv[1:])
else:
    text = input("Enter text to preview: ").strip()

if not text:
    print("No text entered.")
    sys.exit()

# ── Generate strokes ──────────────────────────────────────────
strokes = assemble_human_hierarchy_text(text)

# ── Plot ──────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8.27, 11.69))   # A4 size
fig.patch.set_facecolor("#fffef0")               # warm paper colour
ax.set_facecolor("#fffef0")

# Ruled lines: cap-top (faint blue), baseline (medium blue), descender (dotted)
LINE_TOP  = 25   # matches current_y start in word_assembler
CAP_H     = 7    # BASE_SCALE * 100  (mm)
SPACING   = 13   # line_height (mm)
DESC_DROP = 2    # DESCENDER_DROP rounded (mm)

for i in range(20):
    top      = LINE_TOP + i * SPACING
    baseline = top + CAP_H
    desc     = baseline + DESC_DROP
    if top > 297:
        break
    # Cap-height guide line (very faint)
    ax.axhline(top,      color="#d0e4f0", linewidth=0.35, zorder=0)
    # Baseline (solid, slightly darker — where letters sit)
    ax.axhline(baseline, color="#a0bcd8", linewidth=0.55, zorder=1)
    # Descender guide (dashed, subtle)
    ax.axhline(desc,     color="#d4c8e0", linewidth=0.35, linestyle="--",
               dashes=(4, 6), zorder=0)

# Left margin line
ax.axvline(10, color="#f0b0b0", linewidth=0.5, zorder=0)

# Draw handwriting strokes
for stroke in strokes:
    xs = [p[0] for p in stroke]
    ys = [p[1] for p in stroke]
    ax.plot(xs, ys,
            color="#1a1a8c",
            linewidth=0.7,
            solid_capstyle="round",
            solid_joinstyle="round",
            zorder=2)

ax.set_aspect("equal")
ax.set_xlim(0, 210)
ax.set_ylim(297, 0)
ax.set_title(f'Handwriting Preview   "{text}"', fontsize=9, pad=8)
ax.set_xlabel("X (mm)", fontsize=7)
ax.set_ylabel("Y (mm)", fontsize=7)
ax.tick_params(labelsize=7)

for spine in ax.spines.values():
    spine.set_edgecolor("#bbbbbb")

plt.tight_layout()
plt.show()
