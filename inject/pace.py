import argparse
import numpy as np
import soundfile as sf
import librosa
import hashlib
from typing import Dict, Any

def inject_pace(input_path: str, output_path: str, rate: float) -> Dict[str, Any]:
    """
    Applies a speaking rate (pace) change using time-stretching (preserves pitch).
    rate > 1.0 means faster, rate < 1.0 means slower.
    
    Returns metadata about the transformation.
    """
    if rate <= 0:
        raise ValueError("Rate must be strictly positive.")
        
    audio, sr = sf.read(input_path)
    
    if len(audio.shape) > 1 and audio.shape[1] > 1:
        # Convert to mono if necessary
        audio = np.mean(audio, axis=1)
        
    # Apply time stretch. librosa uses a phase vocoder.
    # Note: librosa.effects.time_stretch expects floating point data.
    transformed_audio = librosa.effects.time_stretch(audio, rate=rate)
    
    # Check for clipping
    max_val = np.max(np.abs(transformed_audio))
    clipping = bool(max_val >= 1.0)
    
    if clipping:
        print(f"WARNING: Clipping occurred during pace adjustment! Maximum amplitude: {max_val:.4f}")
        transformed_audio = np.clip(transformed_audio, -1.0, 1.0)
        
    sf.write(output_path, transformed_audio, sr, subtype='PCM_16')
    
    # Calculate hashes
    with open(input_path, 'rb') as f:
        in_hash = hashlib.sha256(f.read()).hexdigest()
    with open(output_path, 'rb') as f:
        out_hash = hashlib.sha256(f.read()).hexdigest()
        
    return {
        "injection_type": "pace",
        "rate_multiplier": float(rate),
        "input_duration_s": len(audio) / sr,
        "output_duration_s": len(transformed_audio) / sr,
        "clipping_occurred": clipping,
        "input_sha256": in_hash,
        "output_sha256": out_hash,
        "sample_rate": sr
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inject pace change into audio without altering pitch")
    parser.add_argument("input", help="Input WAV file")
    parser.add_argument("output", help="Output WAV file")
    parser.add_argument("--rate", type=float, required=True, help="Rate multiplier (e.g., 0.8 for 20% slower, 1.2 for 20% faster)")
    args = parser.parse_args()
    
    meta = inject_pace(args.input, args.output, args.rate)
    print("Injection metadata:", meta)
