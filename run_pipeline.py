#!/usr/bin/env python3
"""
AI Handwriting Robot — Interactive Runner
Keeps looping: type text → see matplotlib preview + generate G-code.
Type 'quit' or 'exit' to stop.
"""

import sys
import os

# Make sure src/ is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import matplotlib.pyplot as plt
from word_assembler import assemble_human_hierarchy_text
from gcode_generator import strokes_to_gcode

BLOCK_WORDS = ["signature", "sign", "sincerely"]

# Layout constants (must match word_assembler values)
LINE_TOP  = 25
CAP_H     = 7
SPACING   = 13
DESC_DROP = 2.0


def render_preview(text, strokes):
    """Show a ruled-paper matplotlib preview of the handwriting."""
    fig, ax = plt.subplots(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("#fffef0")
    ax.set_facecolor("#fffef0")

    # Ruled lines: cap-top, baseline, descender guide
    for i in range(22):
        top      = LINE_TOP + i * SPACING
        baseline = top + CAP_H
        desc     = baseline + DESC_DROP
        if top > 297:
            break
        ax.axhline(top,      color="#d0e4f0", linewidth=0.35, zorder=0)
        ax.axhline(baseline, color="#a0bcd8", linewidth=0.55, zorder=1)
        ax.axhline(desc,     color="#d4c8e0", linewidth=0.35,
                   linestyle="--", dashes=(4, 6), zorder=0)

    # Left margin
    ax.axvline(10, color="#f0b0b0", linewidth=0.5, zorder=0)

    # Handwriting strokes
    for stroke in strokes:
        xs = [p[0] for p in stroke]
        ys = [p[1] for p in stroke]
        ax.plot(xs, ys,
                color="#1a1a8c", linewidth=0.7,
                solid_capstyle="round", solid_joinstyle="round", zorder=2)

    ax.set_aspect("equal")
    ax.set_xlim(0, 210)
    ax.set_ylim(297, 0)
    ax.set_title(f'Handwriting Preview  -  "{text}"', fontsize=9, pad=8)
    ax.set_xlabel("X (mm)", fontsize=7)
    ax.set_ylabel("Y (mm)", fontsize=7)
    ax.tick_params(labelsize=7)

    for spine in ax.spines.values():
        spine.set_edgecolor("#bbbbbb")

    plt.tight_layout()
    plt.show()


def main():
    print("=" * 50)
    print("   AI Handwriting Robot  -  Interactive Mode")
    print("=" * 50)
    print("Type any text and press Enter.")
    print("  -> Matplotlib preview will open automatically")
    print("  -> G-code saved to output_gcode/my_handwriting.gcode")
    print("Type 'quit' or 'exit' to stop.\n")

    while True:
        try:
            text = input(">> Enter text: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not text:
            print("   (empty — try again)\n")
            continue

        if text.lower() in ("quit", "exit", "q"):
            print("Bye!")
            break

        # Ethics guard
        blocked = False
        for word in BLOCK_WORDS:
            if word in text.lower():
                print(f"   BLOCKED: '{word}' is not allowed.\n")
                blocked = True
                break
        if blocked:
            continue

        # Assemble strokes
        strokes = assemble_human_hierarchy_text(text)
        print(f"   {len(strokes)} strokes assembled")

        # Generate G-code
        strokes_to_gcode(strokes, filename="my_handwriting")

        # Show preview (blocks until window is closed)
        render_preview(text, strokes)

        print()   # blank line before next prompt


if __name__ == "__main__":
    main()

