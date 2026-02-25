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

BLOCK_WORDS = ["Signature", "Sign here", "Yours sincerely", "Yours faithfully"]


def render_preview(text, strokes):
    """Show a plain A4 white-paper matplotlib preview of the handwriting."""
    fig, ax = plt.subplots(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

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

    # Clean paper look: no ticks, no labels, no borders
    ax.axis("off")

    # Thin light-grey paper border (simulates sheet edge)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_edgecolor("#cccccc")
        spine.set_linewidth(0.8)

    ax.set_title(f'"{text}"', fontsize=9, pad=6, color="#444444")

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

