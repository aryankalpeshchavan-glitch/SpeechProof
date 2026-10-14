# SpeechProof — 4–5 Minute Demo Video Script

**Target Duration:** 4 minutes 15 seconds – 4 minutes 45 seconds  
**Video Requirements:** 1080p 60fps, English audio / subtitles, Unlisted YouTube link.

---

### Running Order Summary

| Timestamp | Segment | Key Focus |
|---|---|---|
| **00:00 – 00:25** | Introduction & Problem Statement | The black-box problem with AI speech scoring |
| **00:25 – 00:55** | System Architecture & Living Audio Orb | Tech stack, CUDA large-v3, Living Orb states |
| **00:55 – 01:45** | Audio Ingestion & Live Microphone Recording | Multi-format upload, mic recording with real-time VU reactivity |
| **01:45 – 02:20** | Evidence Inspection & Deterministic Scoring | Waveform anchors, exact timestamps, word context, fluency policy |
| **02:20 – 03:00** | Contrastive Comparison Lab | Reference vs. candidate takes, metric deltas |
| **03:00 – 03:35** | Controlled Crash Test Lab | Pause injection, pace stretching, cross-talk verification |
| **03:35 – 04:05** | Run History & Pre-Registered Validation Matrix | SQLite audit ledger, SHA-256 hashes, T1–T9 results |
| **04:05 – 04:35** | Limitations, Ethical Disclosures & Conclusion | Scientific transparency, offline privacy, wrap-up |

---

### Detailed Scene-by-Scene Script

#### Scene 1: Introduction & The Problem (00:00 – 00:25)
- **On Screen:** Close-up of browser at `http://localhost:8000`. The dark midnight-indigo hero appears with the gently breathing volumetric Living Audio Orb.
- **Action:** Move cursor over the hero headline. Highlight the status pill in the top right: `CUDA · float16 · large-v3`.
- **Narration:**
  > "Hello! When people practice public speaking or prepare for an interview, existing AI speech tools give them a black-box number: 'Your delivery score is 74.' But they never explain *why*, they don't link the score to the audio, and they can't prove whether their rubric can be gamed.  
  > This is **SpeechProof** — an auditable speech scoring platform with verifiable acoustic evidence, a Siri-inspired Living Audio Orb, and an adversarial Crash Test Lab."

---

#### Scene 2: System Architecture & Living Audio Orb (00:25 – 00:55)
- **On Screen:** Full hero section showing the glowing multi-harmonic orb.
- **Action:** Hover over the Living Audio Orb. Show how it smoothly animates with concentric contours, layered volumetric lighting, and orbiting particles.
- **Narration:**
  > "SpeechProof is built with a React 19 frontend and a FastAPI backend. At the center is our Living Audio Orb, rendered on a high-DPI 2D canvas with zero external 3D engine bloat.  
  > Behind the scenes, we run `faster-whisper` large-v3 locally using CTranslate2 on an NVIDIA GPU with CUDA float16. There are no cloud APIs, and we enforce a strict no-silent-CPU-fallback policy to guarantee reproducible, bit-identical results."

---

#### Scene 3: Universal Audio Ingestion & Live Recording (00:55 – 01:45)
- **On Screen:** Click the **🎙 Record Voice** button in the hero.
- **Action:**
  - The Living Audio Orb immediately switches to `RECORDING` state.
  - The live recording HUD appears with elapsed timer and real-time VU energy meter.
  - Speak into the microphone: *"Good morning everyone. Today we are presenting SpeechProof..."*
  - Notice the orb surface ripples dynamically to voice amplitude and spikes mint/cyan flares.
  - Click **■ Stop & Ingest**.
  - The orb transitions to `ANALYZING` state, with particles converging into a focused scanning ring.
  - Within ~2 seconds, the analysis completes, the orb stabilizes into `RESULTS` state, and a green badge appears: `✓ ANALYSIS COMPLETE`.
- **Narration:**
  > "SpeechProof supports universal audio ingestion. You don't need to manually prepare 16 kHz mono WAV files. Whether you upload MP3, M4A, FLAC, AAC, WebM, or record directly through the browser microphone, our ingestion pipeline handles demuxing, stream extraction, and 16 kHz resampling server-side.  
  > Notice how the Living Audio Orb responds to my actual voice amplitude in real time, transitions into an analysis state, and signals when the audit is complete."

---

#### Scene 4: Interactive Waveform & Evidence Inspection (01:45 – 02:20)
- **On Screen:** Click **Inspect Evidence ↓** or scroll down to the **Analyze** workspace.
- **Action:**
  - Show the 5 Score Cards: Overall Delivery Score (e.g., `85.2`), Pace (`138 WPM`), Pausing (`14% pause ratio`), Fluency (`UNAVAILABLE`), Pitch Variety (`1.4 st`), and Vocal Energy (`3.8 dB`).
  - Highlight the Fluency card and read the note: *Uncalibrated in offline Whisper (omitted to avoid false zero penalty)*.
  - Scroll to the interactive HTML5 Canvas waveform.
  - Click on a red/amber highlighted pause interval region in the waveform.
  - The Evidence Inspector panel opens below, displaying:
    - Interval bounds: `start_s = 2.40s`, `end_s = 3.65s` (duration: 1.25s).
    - Threshold: `> 0.8s`.
    - Surrounding word context: *"everyone [PAUSE 1.25s] Today"*.
    - The audio player seeks immediately to `2.40s` and plays.
- **Narration:**
  > "Here are the deterministic results. Notice the Fluency dimension: offline Whisper models transcribe vocabulary without guaranteed acoustic filler tagging. Rather than penalizing the user with an arbitrary zero, SpeechProof explicitly marks Fluency as UNAVAILABLE and computes the overall score solely over verified acoustic dimensions.  
  > On the waveform, every flaw is anchored to an exact temporal interval. When I click this pause marker, it shows the exact 1.25-second gap, the words before and after, and seeks playback directly to that timestamp."

---

#### Scene 5: Contrastive Take Comparison (02:20 – 03:00)
- **On Screen:** Click the **Compare** tab in the sticky navigation.
- **Action:**
  - Select reference recording (Take 1) and candidate recording (Take 2).
  - Click **Run Contrastive Comparison**.
  - Show the side-by-side comparison panels: Reference Score vs. Candidate Score, with dimension deltas (+14 WPM pace, -6% pause ratio, overall delta +4.5).
  - Point out the limitation banner: *"Contrastive comparison assumes comparable acoustic environments; a numerical difference is not automatically statistical significance."*
- **Narration:**
  > "In the Compare workspace, speakers can evaluate multiple takes side-by-side. The system computes exact deltas for pace, pausing, and energy, with dual synchronized players. We also display clear methodological warnings: a positive delta indicates measured change, but not guaranteed clinical or statistical improvement."

---

#### Scene 6: Controlled Crash Test Lab (03:00 – 03:35)
- **On Screen:** Click the **Crash Test Lab** tab.
- **Action:**
  - Select an audio file.
  - Select transform type: **Pause Insertion**.
  - Adjust slider to `2.5 seconds`.
  - Click **Run Crash Test**.
  - The results card displays:
    - Pre-transformation vs. Post-transformation scores.
    - Pausing score dropped by 38 points.
    - Target dimension responded: `YES`.
    - Off-target dimensions (Pace, Pitch): invariant (`NO CROSS-TALK`).
    - Base64 synthesized audio player with clipping check: `NO CLIPPING`.
- **Narration:**
  > "Now, how do we know our scoring algorithm deserves trust? In the Crash Test Lab, we stress-test the rubric using calibrated signal transformations. Here, I inject a 2.5-second silence gap into the audio.  
  > As expected, the pausing score drops significantly, while unrelated dimensions like pitch variety remain unaffected. This verifies dose-response monotonicity and cross-talk isolation."

---

#### Scene 7: Run History & Validation Matrix (03:35 – 04:05)
- **On Screen:** Click **Run History**, then click **Validation Matrix**.
- **Action:**
  - In Run History, show the SQLite ledger entries with SHA-256 prefixes, durations, and timestamps.
  - In the Validation Matrix, show the pre-registered tests:
    - T1 (Deterministic Reproducibility): **MET** (Bit-identical across runs).
    - T2 (Dose-Response): **PILOT**.
    - T3 (Cross-Talk): **PILOT**.
    - T6, T7: **NOT_RUN** (Honest explanation: multi-speaker human dataset not available).
- **Narration:**
  > "Every evaluation is cryptographically sealed with a SHA-256 hash in our local SQLite ledger. And in our Validation Matrix, we display our pre-registered empirical evaluations honestly. Test T1 is MET with 100% bit-identical scores across runs, while T6 and T7 are marked NOT_RUN because human rating cohorts were not available. We report real science, not fabricated benchmarks."

---

#### Scene 8: Limitations, Ethics & Wrap-Up (04:05 – 04:35)
- **On Screen:** Scroll back to the top hero section with the glowing Living Audio Orb.
- **Action:** Bring up the terminal showing `113 passed in 17.89s`.
- **Narration:**
  > "All processing in SpeechProof runs 100% locally on your machine, ensuring full privacy and speaker consent. The entire repository is backed by 113 passing automated tests, verified production builds, and open-source documentation.  
  > Thank you for reviewing SpeechProof — where speech intelligence is truly auditable."

---

### Tips for Recording
1. Use OBS Studio or QuickTime screen recorder at 1920x1080 resolution.
2. Ensure clear microphone audio (use a headset or dedicated USB condenser mic).
3. Test audio playback on the system before recording to ensure system sound is captured.
4. Upload to YouTube as **Unlisted** (NOT Private) and paste the link into the Devpost submission.
