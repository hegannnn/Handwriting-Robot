import os
import math
import sys


def strokes_to_gcode(
    strokes,
    filename="handwriting",
    clearance_z=1.0,      # Pen UP height (mm) — small lift just off paper
    draw_z=-0.1,          # Pen DOWN depth (mm) — very light touch on paper
    rapid_feed=2540,      # XY rapid move speed (mm/min) — from working final.gcode
    plunge_feed=127,      # Z plunge speed (mm/min) — from working final.gcode
    cut_feed=1016,        # Drawing speed (mm/min) — from working final.gcode
    flip_y=True,          # Flip Y-axis for machine orientation
):
    """
    Converts stroke paths to G-code for this pen plotter.

    Pen up/down uses Z-axis G-code, matching the format of the working final.gcode:
      Pen up:   G1 Z{clearance_z} F{rapid_feed}
      Pre-dive: G1 Z0.5
      Pen down: G1 Z{draw_z} F{plunge_feed}
    """

    # ─── Pre-process: Find Y bounds for flipping ────
    print(f"DEBUG: Received {len(strokes)} strokes")

    if strokes:
        all_x = [pt[0] for stroke in strokes for pt in stroke if len(pt) >= 2]
        all_y = [pt[1] for stroke in strokes for pt in stroke if len(pt) >= 2]
        if all_x and all_y:
            min_x, max_x = min(all_x), max(all_x)
            min_y, max_y = min(all_y), max(all_y)
            print(f"STROKE BOUNDS: X[{min_x:.1f}, {max_x:.1f}] Y[{min_y:.1f}, {max_y:.1f}]")
        else:
            print("WARNING: No valid coordinate points found!")
            min_y = max_y = 0
    else:
        print("WARNING: No strokes provided!")
        min_y = max_y = 0

    def transform_y(y):
        if flip_y:
            return max_y - (y - min_y)
        return y

    gcode = []

    # ─── Header ─────────────────────────────────────
    gcode.append("G21         ; Set units to mm")
    gcode.append("G90         ; Absolute positioning")
    gcode.append(f"G1 Z{clearance_z:.4f} F{rapid_feed}      ; Move to clearance level")
    gcode.append("")

    path_count = 0

    for stroke in strokes:
        if len(stroke) < 2:
            continue

        path_count += 1
        gcode.append(f"; Path {path_count}")

        x0, y0 = stroke[0]
        y0 = transform_y(y0)

        # ─── Rapid XY move to stroke start (pen up) ─
        gcode.append("; Rapid to initial position")
        gcode.append(f"G1 X{x0:.4f} Y{y0:.4f} F{rapid_feed}")

        # ─── Intermediate Z before plunge ───────────
        gcode.append(f"G1 Z{clearance_z * 0.5:.4f}")

        # ─── Pen down ───────────────────────────────
        gcode.append("; plunge")
        gcode.append(f"G1 Z{draw_z:.4f} F{plunge_feed}")

        # ─── Draw stroke ────────────────────────────
        gcode.append("; cut")
        for j, (x, y) in enumerate(stroke):
            y = transform_y(y)
            if j == 0:
                gcode.append(f"G1 X{x:.4f} Y{y:.4f} F{cut_feed}")
            else:
                gcode.append(f"G1 X{x:.4f} Y{y:.4f}")

        # ─── Pen up ─────────────────────────────────
        gcode.append(f"G1 Z{clearance_z:.4f} F{rapid_feed}")
        gcode.append("")

    # ─── Return Home ────────────────────────────────
    gcode.append(f"G1 Z{clearance_z:.4f} F{rapid_feed}")
    gcode.append(f"G1 X0 Y0 F{rapid_feed}")
    gcode.append("M2")

    # ─── Save File ──────────────────────────────────
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


# ─── Standalone Entry ────────────────────────────────
if __name__ == "__main__":
    _src_dir = os.path.dirname(os.path.abspath(__file__))
    if _src_dir not in sys.path:
        sys.path.insert(0, _src_dir)

    from word_assembler import assemble_human_hierarchy_text

    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("Enter text: ").strip()

    if text:
        strokes = assemble_human_hierarchy_text(text)
        strokes_to_gcode(strokes, filename="my_handwriting")
