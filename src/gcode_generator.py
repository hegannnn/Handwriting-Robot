import os
import math
import sys


def strokes_to_gcode(
    strokes,
    filename="handwriting",
    rapid_feed=2500,      # XY rapid move speed (mm/min)
    cut_feed=1000,        # Drawing speed (mm/min)
    pen_up_s=0,           # Spindle S value for pen UP   (tune if pen doesn't lift fully)
    pen_down_s=90,        # Spindle S value for pen DOWN (tune until pen presses paper)
    servo_dwell=0.4,      # Seconds to wait after each pen up/down for servo to finish moving
    flip_y=True,          # Flip Y-axis for machine orientation
    scale_factor=1.0      # Scale all coordinates
):
    """
    Converts stroke paths to GRBL 1.1f G-code with servo pen control.

    Pen up/down is controlled via GRBL spindle PWM (M3/M5), which drives
    the servo connected to the spindle output pin (D11 on Arduino Nano/Uno).

    Tuning:
      • Run $$ in GRBL console and check $30 (max spindle speed).
      • pen_down_s and pen_up_s are S values in the range 0..$30.
      • Adjust pen_down_s until the pen just touches the paper.
      • Adjust pen_up_s until the pen clears the paper reliably.
      • If pen moves wrong way, swap pen_up_s and pen_down_s values.
      • Increase servo_dwell (e.g. 0.6) if servo hasn't finished moving before XY starts.
    """

    # ─── Pre-process: Find bounds ───────────────────
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
    gcode.append("G21")           # Metric units
    gcode.append("G90")           # Absolute positioning
    gcode.append("G92 X0 Y0")    # Set current XY as origin (no homing needed)
    # Lift pen at start
    gcode.append(f"M3 S{pen_up_s}")
    gcode.append(f"G4 P{servo_dwell:.2f}")
    gcode.append("")

    path_count = 0

    for stroke in strokes:
        if len(stroke) < 2:
            continue

        path_count += 1
        gcode.append(f"; Path {path_count}")

        x0, y0 = stroke[0]
        y0 = transform_y(y0)

        # ─── Rapid XY move to stroke start (pen is up) ──
        gcode.append(f"G1 X{x0:.4f} Y{y0:.4f} F{rapid_feed}")

        # ─── Pen down ───────────────────────────────────
        gcode.append("; Pen down")
        gcode.append(f"M3 S{pen_down_s}")
        gcode.append(f"G4 P{servo_dwell:.2f}")

        # ─── Draw stroke ────────────────────────────────
        gcode.append("; Cut")
        for j, (x, y) in enumerate(stroke):
            y = transform_y(y)
            if j == 0:
                gcode.append(f"G1 X{x:.4f} Y{y:.4f} F{cut_feed}")
            else:
                gcode.append(f"G1 X{x:.4f} Y{y:.4f}")

        # ─── Pen up ─────────────────────────────────────
        gcode.append("; Pen up")
        gcode.append(f"M3 S{pen_up_s}")
        gcode.append(f"G4 P{servo_dwell:.2f}")
        gcode.append("")

    # ─── Return Home ────────────────────────────────────
    gcode.append("; Return Home")
    gcode.append(f"G1 X0 Y0 F{rapid_feed}")
    gcode.append("M5")     # Spindle/servo off
    gcode.append("M2")     # Program end

    # ─── Save File ──────────────────────────────────────
    try:
        os.makedirs("output_gcode", exist_ok=True)
    except Exception as e:
        print(f"Failed to create output_gcode directory: {e}")
        return gcode

    filepath = f"output_gcode/{filename}.gcode"
    abs_filepath = os.path.abspath(filepath)

    try:
        with open(filepath, "w") as f:
            f.write("\n".join(gcode))
        print(f"G-CODE SAVED: {abs_filepath}")
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
