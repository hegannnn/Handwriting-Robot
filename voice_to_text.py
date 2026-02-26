
import whisper
import sounddevice as sd
from scipy.io.wavfile import write

fs = 44100
seconds = 10  
print("Speak now...")
recording = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
sd.wait()
write("voice.wav", fs, recording)
print("Recording saved as voice.wav")


model = whisper.load_model("base")  
print("Whisper model loaded... transcribing")

result = model.transcribe("voice.wav")
print("Recognized Text:", result["text"])