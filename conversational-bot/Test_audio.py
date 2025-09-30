import sounddevice as sd
import numpy as np

# Check available audio devices and show default
print(sd.query_devices())
print("Default input device:", sd.default.device)

# Select the appropriate one
duration = 3  # seconds
print("speaking for 3 seconds...")
sd.default.device = (2, None)  # (input_device, output_device)
audio = sd.rec(int(duration * 16000), samplerate=16000, channels=1, dtype="int16")
sd.wait()
print("ended recording")

# Play the recorded audio
sd.play(audio, samplerate=16000)
sd.wait()

