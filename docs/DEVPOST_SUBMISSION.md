# Devpost Submission — SpeechProof

**Project Title:** SpeechProof  
**Tagline:** Auditable speech scoring with verifiable acoustic evidence, a Siri-inspired Living Audio Orb, and an adversarial Crash Test Lab.

---

## 💡 Inspiration

Most commercial and educational speech evaluation tools act like black boxes. An executive coach or automated interview prep tool presents a candidate with a score: "Your delivery score is 74/100." 

When the user asks *why*, the system offers vague, AI-generated platitudes. Even worse, if you ask whether the scoring model is robust or can be gamed with simple acoustic perturbations (like talking louder or speeding up audio), there is no evidence, no cryptographic audit trail, and no transparency.

We built **SpeechProof** to answer a fundamental research and engineering question:  
*Can speech intelligence be made completely auditable, deterministic, and verifiable down to the exact millisecond and byte?*

---

## 🎯 What It Does

SpeechProof is a full-stack speech intelligence platform and algorithmic audit laboratory:

1. **Universal Audio Ingestion:** Ingests any audio or video container (WAV, MP3, M4A, AAC, FLAC, OGG, WebM, MP4, Opus) and automatically normalizes it to canonical 16 kHz mono 16-bit PCM WAV.
2. **In-Browser Microphone Recording:** Users can record directly from the browser with real-time VU energy meter feedback, client-side Web Audio normalization, and one-click analysis.
3. **Living Audio Orb & Immersive UI:** A volumetric 3D-effect canvas orb inspired by Siri aesthetics that breathes gently during idle, pulses with real-time harmonic ripples to microphone speech, focuses into a quantum ring during analysis, and calms on results.
4. **Deterministic ASR & Acoustic Rubric:** Runs local offline speech recognition via `faster-whisper` (`large-v3` on CUDA `float16`). From word timestamps and audio waveforms, it extracts objective metrics:
   - **Pace:** Words per minute (target: 100–180 WPM).
   - **Pausing:** Ratio of silence to duration, with penalties for pauses > 0.8s.
   - **Pitch Variety:** Standard deviation of fundamental frequency $F_0$ in semitones (target: $\ge 1.0$).
   - **Vocal Energy:** Dynamic range standard deviation of RMS decibels (target: $\ge 3.0$ dB).
5. **Interactive Evidence Inspector:** Maps flagged intervals onto an HTML5 Canvas waveform. Clicking any evidence marker highlights the exact time interval, shows measured vs. threshold values, displays word context, and scrubs the audio player to that exact moment.
6. **Contrastive Comparison Lab:** Compares reference vs. candidate takes side-by-side with dimension deltas, direction of change, and dual waveform players.
7. **The Crash Test Lab:** An adversarial testbed that applies calibrated audio transformations (pause injection, phase-vocoder time-stretching, and dB gain scaling) to test whether rubric dimensions respond selectively to intended signal changes without off-target cross-talk.
8. **Tamper-Evident SHA-256 Ledger:** Computes dual SHA-256 digests of the raw audio bytes and the canonical evidence JSON, stored in an SQLite run ledger (`db/ledger.sqlite`).
9. **Pre-Registered Validation Matrix:** Displays real status results for tests T1–T9 and A1–A5 (Deterministic Reproducibility, Dose-Response, Cross-Talk, etc.) with honest disclosures.

---

## 🛠️ How We Built It

- **Frontend:** React 19, TypeScript, and Vite. Designed with an immersive midnight indigo palette, Syne display typography, and Space Grotesk body copy. The Living Audio Orb is implemented using a custom high-DPI HTML5 2D Canvas rendering pipeline with zero external 3D engine bloat.
- **Audio Ingestion:** Built a dedicated audio I/O module (`speechproof/audio_io.py`) using PyAV (`av`), Librosa, and SoundFile to handle demuxing, stream extraction, channel downmixing, and 16 kHz resampling.
- **ASR & Inference:** `faster-whisper` backed by CTranslate2 running on an NVIDIA GPU with CUDA `float16`. Enforces a strict no-silent-CPU-fallback policy to guarantee reproducible timing and floating-point stability.
- **Signal Processing:** `librosa` and `scipy` for pitch estimation (`pyin`), amplitude envelopes, and phase-vocoder time-stretching.
- **Backend API:** FastAPI and Uvicorn hosting RESTful endpoints (`/score`, `/compare`, `/arena/transform`, `/leaderboard`, `/validation`, `/ready`, `/health`) and serving the compiled React bundle.
- **Testing & Quality Assurance:** Comprehensive Pytest test suite containing **113 passing tests** across 23 test modules.

---

## 🌟 What Makes Our Approach Distinctive

1. **No Hallucinations, No Black Boxes:** SpeechProof does not use generative LLMs to make up subjective scores. All scores come from verifiable acoustic equations and word-level alignments.
2. **Honest Metric Calibration (The Fluency Policy):** Many speech apps claim to measure "fluency" by returning an arbitrary number. SpeechProof recognizes that offline Whisper models transcribe intended text without guaranteed acoustic filler word tagging (*um, uh, like*). Rather than returning a deceptive zero score or guessing, SpeechProof marks Fluency as *UNAVAILABLE* and computes overall scores solely across genuinely measured acoustic dimensions.
3. **Adversarial Crash Testing:** Instead of claiming our rubric is perfect, we built a tool to deliberately attack it. We inject pauses, stretch speech rates, and alter volume to verify dose-response and cross-talk isolation.
4. **Cryptographic Proof of Evaluation:** Every result includes a SHA-256 hash of the normalized audio and the evidence JSON. If a single audio sample or evidence field is modified, the audit hash fails verification.

---

## 🧗 Challenges Encountered

- **Cross-Platform Audio Normalization:** Browser microphones record in varied formats (WebM Opus on Chrome, Ogg on Firefox, AAC on Safari). Creating a seamless pipeline that takes any uploaded container or live browser recording and renders a strict 16 kHz mono 16-bit PCM WAV required multi-tiered decoding using Web Audio API in the browser and PyAV/Librosa on the server.
- **Real-Time VU Reactivity Without Lag:** Rendering a complex multi-layered 3D-effect canvas orb while sampling browser microphone audio required an optimized `requestAnimationFrame` loop with smooth exponential averaging and high-DPI canvas scaling.
- **Phase Vocoder Artifacts:** Time-stretching speech for pace testing can cause acoustic phase artifacts or digital clipping. We added automated clipping detection and safe boundary constraints.

---

## 🏆 Accomplishments

- Built a complete, production-grade speech intelligence application with 113 automated tests passing.
- Implemented universal audio upload supporting WAV, MP3, M4A, AAC, FLAC, OGG, WebM, MP4, and Opus.
- Created a Siri-inspired Living Audio Orb with multi-state visual feedback (idle, recording, analyzing, results, error).
- Preserved strict scientific integrity: T1–T9 evaluations report real empirical findings without fabricating results.

---

## 🔬 Research Limitations & Future Work

- **Cohort Size:** The empirical benchmark evaluations (T4–T9) were conducted on a single authorized participant (`aryan_test.wav`, N=1). Multi-speaker validation cohorts are required before claiming general population validity.
- **Acoustic Disfluency Classifier:** Future work will integrate a dedicated acoustic filler detection model to calibrate the Fluency metric empirically.
- **Cross-Hardware Float16 Validation:** T1 demonstrated 100% bit-identical reproducibility on a single CUDA machine; multi-GPU cross-architecture equivalence remains to be tested across different hardware vendors.

---

## 🤖 Built With

- **AI Tools & Models:**
  - `faster-whisper` (`large-v3`, CTranslate2, CUDA float16)
  - Google Antigravity Agentic IDE (AI coding assistance for test suites, canvas rendering, and ingestion modules)
- **Languages & Frameworks:** Python 3.11+, TypeScript, React 19, FastAPI, Vite
- **Audio & Scientific Computing:** PyAV, Librosa, SoundFile, NumPy, SciPy
- **Database & Storage:** SQLite (`db/ledger.sqlite`), SHA-256

---

## 🔗 Project Links

- **GitHub Repository:** [https://github.com/aryankalpeshchavan-glitch/SpeechProof](https://github.com/aryankalpeshchavan-glitch/SpeechProof)
- **Demo Video:** [YouTube Video Walkthrough](https://youtu.be/placeholder) *(3-10 minutes, English narration)*
- **Team Members:** [Aryan Chavan - Lead Engineer & Researcher]
