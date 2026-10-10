import argparse
import numpy as np
import soundfile as sf
import hashlib
from typing import Dict, Any

def inject_volume(input_path: str, output_path: str, gain_db: float) -> Dict[str, Any]:
    """
    Applies a volume change to an audio file in decibels.
    
    Returns metadata about the transformation.
    """
    audio, sr = sf.read(input_path)
    
    if len(audio.shape) > 1 and audio.shape[1] > 1:
        # Convert to mono if necessary
        audio = np.mean(audio, axis=1)
        
    multiplier = 10 ** (gain_db / 20.0)
    transformed_audio = audio * multiplier
    
    max_val = np.max(np.abs(transformed_audio))
    clipping = bool(max_val >= 1.0)
    
    if clipping:
        print(f"WARNING: Clipping occurred! Maximum amplitude: {max_val:.4f}")
        # Apply hard clipping to stay within [-1, 1] range for 16-bit PCM safety
        transformed_audio = np.clip(transformed_audio, -1.0, 1.0)
        
    sf.write(output_path, transformed_audio, sr, subtype='PCM_16')
    
    # Calculate hashes
    with open(input_path, 'rb') as f:
        in_hash = hashlib.sha256(f.read()).hexdigest()
    with open(output_path, 'rb') as f:
        out_hash = hashlib.sha256(f.read()).hexdigest()
        
    return {
        "injection_type": "volume",
        "gain_db": float(gain_db),
        "clipping_occurred": clipping,
        "max_amplitude": float(max_val),
        "input_sha256": in_hash,
        "output_sha256": out_hash,
        "sample_rate": sr
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inject volume change into audio")
    parser.add_argument("input", help="Input WAV file")
    parser.add_argument("output", help="Output WAV file")
    parser.add_argument("--gain", type=float, required=True, help="Gain in dB (e.g., -6.0 or +3.0)")
    args = parser.parse_args()
    
    meta = inject_volume(args.input, args.output, args.gain)
    print("Injection metadata:", meta)
