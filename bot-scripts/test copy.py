import sounddevice as sd
print(sd.query_devices())
print("Default input device:", sd.default.device)
