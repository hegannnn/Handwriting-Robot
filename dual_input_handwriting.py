import whisper
import sounddevice as sd
from scipy.io.wavfile import write
import sys
import os

try:
    from src.word_assembler import assemble_human_hierarchy_text
except ImportError:
    from word_assembler import assemble_human_hierarchy_text

import matplotlib.pyplot as plt

# -------------------------
# Step 1: Ask for input method
# -------------------------
print("Choose input method:")
print("1 → Speak")
print("2 → Type")
choice = input("Enter 1 or 2: ").strip()

if choice == "1":
    # -------------------------
    # Voice Input
    # -------------------------
    fs = 44100
    seconds = 5
    print("Speak now...")
    recording = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
    sd.wait()
    write("voice.wav", fs, recording)
    print("Recording saved as voice.wav")

    model = whisper.load_model("base")
    print("Whisper model loaded... transcribing")
    result = model.transcribe("voice.wav")
    text = result["text"].strip()
    print("Recognized Text:", text)

    if not text:
        print("No speech detected, exiting...")
        sys.exit()

elif choice == "2":
    # -------------------------
    # Keyboard Input
    # -------------------------
    text = input("Type your text: ").strip()
    if not text:
        print("No text entered, exiting...")
        sys.exit()
else:
    print("Invalid choice, exiting...")
    sys.exit()

# -------------------------
# Step 3: Generate handwriting
# -------------------------
print("Generating handwriting...")
final_path = assemble_human_hierarchy_text(text)

# -------------------------
# Step 4: Preview using matplotlib
# -------------------------
fig, ax = plt.subplots(figsize=(8.27, 11.69))
fig.patch.set_facecolor('#fffef0')  # paper-like background
ax.set_facecolor('#fffef0')

for stroke in final_path:
    xs = [p[0] for p in stroke]
    ys = [p[1] for p in stroke]
    ax.plot(xs, ys, color='#1a1a8c', linewidth=0.9,
            solid_capstyle='round', solid_joinstyle='round')

ax.set_aspect('equal')
ax.set_xlim(0, 210)
ax.set_ylim(297, 0)
ax.set_title(f'Human Handwriting Preview — "{text}"', fontsize=9)
ax.axis('off')
plt.tight_layout()
plt.show()

print("Done! Handwriting preview displayed.")