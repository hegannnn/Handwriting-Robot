import os
import math
import sys


def strokes_to_gcode(
    strokes,
    filename="handwriting",
    clearance_z=3.0,      # Pen UP height
    draw_z=-3,          # Pen DOWN depth
    rapid_feed=2500,      # Rapid move speed
    plunge_feed=150,      # Z down speed
    cut_feed=1000,        # Drawing speed
    flip_y=True,          # Flip Y-axis for machine orientation
    scale_factor=1.0      # Scale all coordinates (for workspace size adjustment)
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

    # ─── Pre-process: Find bounds & apply scale ───
    print(f"DEBUG: Received {len(strokes)} strokes")
    
    if strokes:
        for i, stroke in enumerate(strokes[:3]):  # Show first 3 strokes
            print(f"  Stroke {i}: {len(stroke)} points")
        
        all_x = [pt[0] for stroke in strokes for pt in stroke if len(pt) >= 2]
        all_y = [pt[1] for stroke in strokes for pt in stroke if len(pt) >= 2]
        
        if all_x and all_y:
            min_x, max_x = min(all_x), max(all_x)
            min_y, max_y = min(all_y), max(all_y)
            width = max_x - min_x
            height = max_y - min_y
            print(f"STROKE BOUNDS: X[{min_x:.1f}, {max_x:.1f}] (width={width:.1f}mm), Y[{min_y:.1f}, {max_y:.1f}] (height={height:.1f}mm)")
        else:
            print("WARNING: No valid coordinate points found in strokes!")
            min_y = max_y = 0
    else:
        print("WARNING: No strokes provided!")
        min_y = max_y = 0
    
    def transform_y(y):
        if flip_y:
            return max_y - (y - min_y)  # Flip around center
        return y

    gcode = []

    # ─── Header ─────────────────────────────────────
    gcode.append("G21")                      # Metric units
    gcode.append("G90")                      # Absolute positioning
    gcode.append("G92 X0 Y0 Z0")             # Set current position as origin (no homing needed)
    gcode.append(f"G1 Z{clearance_z:.2f} F{rapid_feed}")  # Move to clearance height
    gcode.append("")

    path_count = 0

    for stroke in strokes:

       

        if len(stroke) < 2:
            continue

        path_count += 1
        gcode.append(f"; Path {path_count}")

        x0, y0 = stroke[0]
        y0 = transform_y(y0)

        # ─── Rapid XY Move to first point WITH pen retracted ─────────────────────────
        gcode.append(f"G1 X{x0:.4f} Y{y0:.4f} Z{clearance_z:.2f} F{rapid_feed}")

        # ─── Plunge Down directly to draw depth ───────────────────────────
        gcode.append("; Plunge")
        gcode.append(f"G1 Z{draw_z:.4f} F{plunge_feed}")

        # ─── Draw Stroke ───────────────────────────
        gcode.append("; Cut")

        n = len(stroke)

        for j, (x, y) in enumerate(stroke):
            y = transform_y(y)  # Apply Y-flip transformation
            
            # Use consistent feedrate for better control
            if j == 0:
                # First point - set drawing feedrate
                gcode.append(f"G1 X{x:.4f} Y{y:.4f} F{cut_feed}")
            else:
                # Subsequent points - maintain feedrate
                gcode.append(f"G1 X{x:.4f} Y{y:.4f} F{cut_feed}")

        # ─── Lift Pen ──────────────────────────────
        gcode.append("")
        gcode.append("; Retract pen")
        gcode.append(f"G1 Z{clearance_z:.2f} F{rapid_feed}")
        gcode.append("")

    # ─── Return Home ───────────────────────────────
    gcode.append("")
    gcode.append("; Return Home")
    gcode.append(f"G1 Z{clearance_z:.2f} F{rapid_feed}")  # Lift pen first
    gcode.append(f"G1 X0 Y0 F{rapid_feed}")               # Return to origin
    gcode.append("M2")                                     # Program end

    # ─── Save File ─────────────────────────────────
    try:
        os.makedirs("output_gcode", exist_ok=True)
        print(f"✓ Directory exists/created: output_gcode")
    except Exception as e:
        print(f"✗ Failed to create output_gcode directory: {e}")
        return gcode
    
    filepath = f"output_gcode/{filename}.gcode"
    abs_filepath = os.path.abspath(filepath)
    print(f"  Target path: {abs_filepath}")
    print(f"  Path writable: {os.access(os.path.dirname(abs_filepath), os.W_OK)}")

    try:
        with open(filepath, "w") as f:
            bytes_written = f.write("\n".join(gcode))
        
        print(f"✓ G-CODE SAVED: {filepath}")
        print(f"✓ {path_count} paths generated successfully!")
        print(f"✓ Total lines: {len(gcode)}")
        print(f"✓ Bytes written: {bytes_written}")
        
        # Verify file exists
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"✓ File verified - Size: {file_size} bytes")
        else:
            print(f"✗ File was not created!")
        
    except PermissionError as e:
        print(f"✗ PERMISSION DENIED: {e}")
        print(f"✗ Cannot write to: {filepath}")
    except IOError as e:
        print(f"✗ IO ERROR: {e}")
    except Exception as e:
        print(f"✗ UNEXPECTED ERROR saving G-code: {e}")
        import traceback
        traceback.print_exc()

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