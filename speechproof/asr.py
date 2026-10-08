import os
import wave
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import site
try:
    for site_dir in site.getsitepackages():
        nv_dir = os.path.join(site_dir, "nvidia")
        if os.path.exists(nv_dir):
            for lib in ["cublas", "cudnn", "cufft", "curand", "cusolver", "cusparse"]:
                bin_dir = os.path.join(nv_dir, lib, "bin")
                if os.path.exists(bin_dir):
                    if hasattr(os, "add_dll_directory"):
                        os.add_dll_directory(bin_dir)
                    os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
except Exception:
    pass

import faster_whisper
from speechproof.config import config

@dataclass
class ASRWord:
    word: str
    start_s: float
    end_s: float
    confidence: Optional[float] = None

@dataclass
class ASRSegment:
    text: str
    start_s: float
    end_s: float
    words: List[ASRWord]

@dataclass
class ASRTranscript:
    text: str
    segments: List[ASRSegment]
    metadata: Dict[str, Any]

class ASREngine:
    def transcribe(self, audio_path: str) -> ASRTranscript:
        raise NotImplementedError("Offline ASR engine is not implemented yet. Do not fabricate transcripts.")

def validate_audio(audio_path: str) -> None:
    if not os.path.exists(audio_path):
        raise ValueError(f"Audio file not found: {audio_path}")
    if not audio_path.lower().endswith('.wav'):
        raise ValueError("Audio file must be a WAV file.")
    try:
        with wave.open(audio_path, 'rb') as f:
            if f.getnchannels() != 1:
                raise ValueError("Audio must be mono.")
            if f.getframerate() != 16000:
                raise ValueError("Audio sample rate must be 16 kHz.")
            frames = f.getnframes()
            if frames <= 0:
                raise ValueError("Audio duration must be > 0.")
    except wave.Error as e:
        raise ValueError(f"Invalid WAV file: {e}")

class FasterWhisperASREngine(ASREngine):
    def __init__(self, local_files_only: bool = True):
        self.cfg = config.asr
        if self.cfg.device == "cuda":
            import ctranslate2
            if not ctranslate2.get_supported_compute_types("cuda"):
                raise RuntimeError("CUDA requested but not available in ctranslate2. No CPU fallback allowed.")
                
        # Validate model cache exists if local_files_only is True
        model_path = os.path.join(self.cfg.model_cache_dir, f"models--Systran--faster-whisper-{self.cfg.model_name}")
        
        self.model = faster_whisper.WhisperModel(
            self.cfg.model_name,
            device=self.cfg.device,
            device_index=[0] if self.cfg.device == "cuda" else 0,
            compute_type=self.cfg.compute_type,
            download_root=self.cfg.model_cache_dir,
            local_files_only=local_files_only,
            num_workers=1
        )

    def transcribe(self, audio_path: str) -> ASRTranscript:
        validate_audio(audio_path)
        
        import scipy.io.wavfile as wav
        sr, audio_data = wav.read(audio_path)
        # convert to float32 between -1 and 1
        if audio_data.dtype != 'float32':
            import numpy as np
            audio_data = audio_data.astype(np.float32) / 32768.0

        segments_gen, info = self.model.transcribe(
            audio_data,
            language=self.cfg.language,
            beam_size=self.cfg.beam_size,
            word_timestamps=self.cfg.word_timestamps,
            vad_filter=self.cfg.vad_filter,
            condition_on_previous_text=self.cfg.condition_on_previous_text
        )
        
        parsed_segments = []
        full_text = ""
        word_count = 0
        
        for segment in segments_gen:
            if segment.start < 0 or segment.end < segment.start:
                raise ValueError("Invalid segment timestamps.")
                
            parsed_words = []
            if segment.words:
                last_word_end = -1.0
                for w in segment.words:
                    if w.start < 0 or w.end < w.start:
                        raise ValueError("Invalid word timestamps.")
                    if w.start < last_word_end:
                        raise ValueError("Words are not chronologically ordered.")
                    if w.start < segment.start or w.end > segment.end:
                        raise ValueError("Word boundaries outside segment boundaries.")
                    parsed_words.append(ASRWord(w.word, w.start, w.end, w.probability))
                    last_word_end = w.end
                    word_count += 1
                    
            parsed_segments.append(ASRSegment(segment.text, segment.start, segment.end, parsed_words))
            full_text += segment.text
            
        import hashlib
        with open(audio_path, 'rb') as f:
            audio_sha256 = hashlib.sha256(f.read()).hexdigest()
            
        metadata = {
            "audio_path": audio_path,
            "audio_sha256": audio_sha256,
            "model_name": self.cfg.model_name,
            "language": info.language,
            "language_probability": info.language_probability,
            "asr_engine_name": "faster-whisper",
            "asr_engine_version": faster_whisper.__version__,
            "beam_size": self.cfg.beam_size,
            "word_timestamps_enabled": self.cfg.word_timestamps,
            "vad_enabled": self.cfg.vad_filter,
            "duration_s": info.duration,
            "segment_count": len(parsed_segments),
            "word_count": word_count
        }
        
        return ASRTranscript(full_text, parsed_segments, metadata)

def extract_asr(audio_path: str, engine: Optional[ASREngine] = None) -> ASRTranscript:
    if engine is None:
        engine = FasterWhisperASREngine(local_files_only=True)
    return engine.transcribe(audio_path)

def transcribe(wav: str):
    """
    Day-1 backward compatibility adapter for Krishna's pipeline.
    Translates ASRTranscript object into a list of word dictionaries.
    """
    transcript = extract_asr(wav)
    words = []
    for segment in transcript.segments:
        for word in segment.words:
            words.append({
                "word": word.word.strip(),
                "start": round(word.start_s, 3),
                "end": round(word.end_s, 3)
            })
    return words

if __name__ == "__main__":
    import sys
    import argparse
    parser = argparse.ArgumentParser(description="SpeechProof ASR Utility")
    parser.add_argument("--prepare-model", action="store_true", help="Download model to cache")
    args = parser.parse_args()
    if args.prepare_model:
        from speechproof.config import config
        cfg = config.asr
        print(f"Preparing model: {cfg.model_name}")
        print(f"Destination: {cfg.model_cache_dir}")
        try:
            faster_whisper.WhisperModel(
                cfg.model_name,
                device="cpu", # download is device independent
                compute_type="int8",
                download_root=cfg.model_cache_dir,
                local_files_only=False
            )
            print("SUCCESS: Model downloaded and ready for offline use.")
        except Exception as e:
            print(f"FAILURE: {e}")
            sys.exit(1)
