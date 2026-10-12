
import soundfile as sf

audio, sample_rate = sf.read("data/real/sample_speech.wav")

# Keep the first 5 seconds
short_audio = audio[:5 * sample_rate]

sf.write("data/real/short_speech.wav", short_audio, sample_rate)

print("Created data/real/short_speech.wav")
