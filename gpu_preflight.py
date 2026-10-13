import ctranslate2
import faster_whisper
import traceback

def main():
    print("Preflight check for GPU...")
    try:
        types = ctranslate2.get_supported_compute_types("cuda")
        print(f"ctranslate2 cuda supported types: {types}")
        if not types:
            raise RuntimeError("ctranslate2 reports no CUDA compute types.")
        
        # Test WhisperModel initialization
        print("Initializing WhisperModel on CUDA...")
        model = faster_whisper.WhisperModel(
            "large-v3",
            device="cuda",
            compute_type="float16",
            download_root="./model_cache",
            local_files_only=True,
            device_index=0
        )
        print("WhisperModel initialized successfully on GPU.")
    except Exception as e:
        print(f"Failed to initialize on GPU: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
