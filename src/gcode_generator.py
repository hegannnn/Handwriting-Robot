import os
import sys


def strokes_to_gcode(
    strokes,
    filename="handwriting",
    clearance_z=5.0,      # Pen UP height (mm) — Z+ is pen up
    draw_z=0.0,           # Pen DOWN (mm)  — Z=0 is pen touching paper at origin
    plunge_feed=127,      # Z plunge speed (mm/min) — controlled pen drop
    cut_feed=1000,        # Drawing speed (mm/min)
    flip_x=True,          # Machine X+ = left,  software X+ = right  → flip
    flip_y=True,          # Machine Y+ = up,    software Y+ = down   → flip
):
    """
    Converts stroke paths to G-code for this pen plotter.

    Machine coordinate system:
      Origin : bottom-right corner of paper
      X+     : moves LEFT
      Y+     : moves UP
      Z+     : pen UP  (Z=0 = pen touching paper)

    Software coordinate system (word_assembler output):
      Origin : top-left
      X+     : right
      Y+     : down

    Both axes are flipped to match.  The flip uses the bounding box of
    the generated strokes so the drawing is centred on the usable area.
    """

    print(f"DEBUG: Received {len(strokes)} strokes")

    if not strokes:
        print("WARNING: No strokes provided!")
        return []

    # ─── Bounding box (used for axis flips) ─────────────────────────
    all_x = [pt[0] for stroke in strokes for pt in stroke if len(pt) >= 2]
    all_y = [pt[1] for stroke in strokes for pt in stroke if len(pt) >= 2]

    if not all_x or not all_y:
        print("WARNING: No valid coordinate points found!")
        return []

    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    print(f"STROKE BOUNDS: X[{min_x:.1f}, {max_x:.1f}]  Y[{min_y:.1f}, {max_y:.1f}]")

    def tx(x):
        """Flip X so software-right becomes machine-left."""
        return max_x - (x - min_x) if flip_x else x

    def ty(y):
        """Flip Y so software-down becomes machine-up."""
        return max_y - (y - min_y) if flip_y else y

    gcode = []

    # ─── Header ─────────────────────────────────────────────────────
    gcode.append("G21 ; millimeters")
    gcode.append("G90 ; absolute coordinate")
    gcode.append("G17 ; XY plane")
    gcode.append("G94 ; units per minute feed rate mode")
    gcode.append("")

    # ─── Initialization ─────────────────────────────────────────────
    gcode.append(f"G0 Z{clearance_z:.4f} ; Go to safety height")
    gcode.append("G0 X0 Y0 ; Go to zero location")
    gcode.append("G0 Z0")
    gcode.append("")

    path_count = 0

    for stroke in strokes:
        if len(stroke) < 2:
            continue

        path_count += 1
        gcode.append(f"; Path {path_count}")

        x0 = tx(stroke[0][0])
        y0 = ty(stroke[0][1])

        # Lift → rapid travel → controlled plunge
        gcode.append(f"G0 Z{clearance_z:.4f}")
        gcode.append(f"G0 X{x0:.4f} Y{y0:.4f}")
        gcode.append(f"G1 Z{draw_z:.4f} F{plunge_feed}")

        # Draw stroke
        for j, (x, y) in enumerate(stroke):
            if j == 0:
                gcode.append(f"G1 X{tx(x):.4f} Y{ty(y):.4f} F{cut_feed}")
            else:
                gcode.append(f"G1 X{tx(x):.4f} Y{ty(y):.4f}")

        gcode.append("")

    # ─── End: lift, home, stop ───────────────────────────────────────
    gcode.append(f"G0 Z{clearance_z:.4f}")
    gcode.append("G0 X0 Y0")
    gcode.append("M5")

    # ─── Save file ───────────────────────────────────────────────────
    try:
        os.makedirs("output_gcode", exist_ok=True)
    except Exception as e:
        print(f"Failed to create output_gcode directory: {e}")
        return gcode

    filepath = f"output_gcode/{filename}.gcode"
    try:
        with open(filepath, "w") as f:
            f.write("\n".join(gcode))
        print(f"G-CODE SAVED: {os.path.abspath(filepath)}")
        print(f"{path_count} paths, {len(gcode)} lines")
    except Exception as e:
        print(f"ERROR saving G-code: {e}")

    return gcode


# ─── Standalone entry ────────────────────────────────────────────────
if __name__ == "__main__":
    _src_dir = os.path.dirname(os.path.abspath(__file__))
    if _src_dir not in sys.path:
        sys.path.insert(0, _src_dir)

    from word_assembler import assemble_human_hierarchy_text

    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("Enter text: ").strip()

    if text:
        strokes = assemble_human_hierarchy_text(text)
        strokes_to_gcode(strokes, filename="my_handwriting")
