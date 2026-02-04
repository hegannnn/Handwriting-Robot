import os

def strokes_to_gcode(strokes, filename="handwriting"):
    """YOUR strokes → Robot G-code commands"""
    gcode = []
    gcode.append("G21")        # mm units
    gcode.append("G90")        # absolute mode  
    gcode.append("G1 F1000")   # speed
    
    for i, stroke in enumerate(strokes):
        if len(stroke) < 2: 
            continue
            
        # Pen UP → Move to start position
        gcode.append("M5")           # Pen up
        x0, y0 = stroke[0]
        gcode.append(f"G0 X{x0:.1f} Y{y0:.1f}")
        
        # Pen DOWN → Draw stroke
        gcode.append("M3 S500")      # Pen down
        for x, y in stroke:
            gcode.append(f"G1 X{x:.1f} Y{y:.1f}")
        gcode.append("M5")           # Pen up
    
    gcode.append("G0 X0 Y0")     # Home
    gcode.append("M2")           # End program
    
    # SAVE FOR YOUR ROBOT
    os.makedirs("output_gcode", exist_ok=True)
    filepath = f'output_gcode/{filename}.gcode'
    with open(filepath, 'w') as f:
        f.write('\n'.join(gcode))
    
    print(f"🚀 G-CODE SAVED: {filepath}")
    print(f"📏 {len(strokes)} strokes → Ready for EasyDraw V2!")
    return gcode
