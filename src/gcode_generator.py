import os
import math
import sys


def strokes_to_gcode(
    strokes,
    filename="handwriting",
    clearance_z=3.0,      # Pen UP height
    draw_z=-2.5,          # Pen DOWN depth
    rapid_feed=2500,      # Rapid move speed
    plunge_feed=150,      # Z down speed
    cut_feed=1000,        # Drawing speed
    flip_y=True           # Flip Y-axis for machine orientation
):
    """
    Converts stroke paths → CNC-style G-code for stepper motors.
    Uses Z-axis for pen up/down (no servo).

    Machine Behavior:
      • G21 (mm)
      • G90 (absolute)
      • Z clearance move
      • Z plunge
      • G1 drawing moves
    """

    # ─── Pre-process: Find Y bounds for flipping ───
    if flip_y and strokes:
        all_y = [pt[1] for stroke in strokes for pt in stroke if len(pt) >= 2]
        if all_y:
            min_y = min(all_y)
            max_y = max(all_y)
        else:
            min_y = max_y = 0
    
    def transform_y(y):
        if flip_y:
            return max_y - (y - min_y)  # Flip around center
        return y

    gcode = []

    # ─── Header ─────────────────────────────────────
    gcode.append("G21")                      # Metric units
    gcode.append("G90")                      # Absolute positioning
    gcode.append(f"G1 Z{clearance_z:.2f} F{rapid_feed}")  # Move to clearance height
    gcode.append("")

    path_count = 0

    for stroke in strokes:
        if len(stroke) < 2:
            continue

        path_count += 1
        gcode.append(f"; Path {path_count}")
        gcode.append("; Rapid to initial position")

        x0, y0 = stroke[0]
        y0 = transform_y(y0)

        # ─── Rapid XY Move ─────────────────────────
        gcode.append(f"G1 X{x0:.4f} Y{y0:.4f} F{rapid_feed}")

        # ─── Move to Safe Z Before Plunge ──────────
        gcode.append(f"G1 Z0.5000")

        # ─── Plunge Down ───────────────────────────
        gcode.append("; Plunge")
        gcode.append(f"G1 Z{draw_z:.4f} F{plunge_feed}")

        # ─── Draw Stroke ───────────────────────────
        gcode.append("; Cut")

        n = len(stroke)

        for j, (x, y) in enumerate(stroke):
            y = transform_y(y)  # Apply Y-flip transformation
            
            # Smooth acceleration curve
            t = j / max(n - 1, 1)
            curve = 0.5 * (1 - math.cos(math.pi * t))

            # Smooth speed variation
            dynamic_feed = int(cut_feed * (0.7 + 0.3 * curve))

            if j == 0:
                gcode.append(f"G1 X{x:.4f} Y{y:.4f} F{dynamic_feed}")
            else:
                gcode.append(f"G1 X{x:.4f} Y{y:.4f}")

        # ─── Lift Pen ──────────────────────────────
        gcode.append("")
        gcode.append("; Retract")
        gcode.append(f"G1 Z{clearance_z:.2f} F{rapid_feed}")
        gcode.append("")

    # ─── Return Home ───────────────────────────────
    gcode.append("; Return Home")
    gcode.append(f"G1 X0 Y0 F{rapid_feed}")
    gcode.append("M2")

    # ─── Save File ─────────────────────────────────
    os.makedirs("output_gcode", exist_ok=True)
    filepath = f"output_gcode/{filename}.gcode"

    with open(filepath, "w") as f:
        f.write("\n".join(gcode))

    print(f"G-CODE SAVED: {filepath}")
    print(f"{path_count} paths generated successfully!")

    return gcode


# ─── Standalone Entry ──────────────────────────────
if __name__ == "__main__":
    _src_dir = os.path.dirname(os.path.abspath(__file__))
    if _src_dir not in sys.path:
        sys.path.insert(0, _src_dir)

    from word_assembler import assemble_human_hierarchy_text

    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("Enter text: ").strip()

    if text:
        strokes = assemble_human_hierarchy_text(text)
        strokes_to_gcode(strokes, filename="my_handwriting")