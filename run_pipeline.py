#!/usr/bin/env python3

import subprocess
import sys

def main():
    print(" AI Handwriting Robot ")
    
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
    else:
        text = input(" Enter text (or 'aaa'): ")
    
    print(f" Processing: '{text}'")
    
    # BULLETPROOF: Call your working main.py directly
    result = subprocess.run([
        sys.executable, "src/gcode_generator.py", text
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(" SUCCESS: G-code generated!")
        print(" Check: output_gcode/my_handwriting.gcode")
    else:
        print(" Error - using direct main.py")
        subprocess.run([sys.executable, "main.py"])

if __name__ == "__main__":
    main()
