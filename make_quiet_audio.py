
import soundfile as sf

input_file = "data/real/sample_speech.wav"
output_file = "data/real/quiet_speech.wav"

audio, sample_rate = sf.read(input_file)

# Reduce volume to 50%
quiet_audio = audio * 0.5

sf.write(output_file, quiet_audio, sample_rate)

print("Created:", output_file)
