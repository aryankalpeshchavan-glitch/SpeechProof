import { useState, useEffect, useRef, useCallback } from 'react';
import { WaveformCanvas, type EvidenceRegion } from './WaveformCanvas';
import { HeroCanvas } from './HeroCanvas';
import { startVoiceRecording, type LiveVoiceRecorder } from './audioRecorder';

interface ReadinessInfo {
  status: string;
  device: string;
  cuda_available: boolean;
  compute_type?: string;
  model_name?: string;
  model_cached?: boolean;
}

interface ValidationItem {
  id: string;
  name: string;
  status: 'MET' | 'NOT_MET' | 'PILOT' | 'INCONCLUSIVE' | 'NOT_RUN' | 'NOT_SUPPORTED' | 'FAILED';
  metric: string | null;
  value: any;
  target: string | null;
  reason: string;
  limitations: string[];
  raw_artifact?: string;
}

interface RunRecord {
  run_id: number;
  recording_name: string;
  rubric_version: string;
  scorer_name: string;
  overall_score: number | null;
  sha256_prefix: string;
  sha256: string;
  scores: Record<string, number>;
  duration_s: number | null;
  created_at: string;
}

type TabId = 'analyze' | 'compare' | 'arena' | 'history' | 'validation';

const ACCEPTED_AUDIO = 'audio/*,.wav,.mp3,.m4a,.aac,.flac,.ogg,.webm,.wma,.opus,.m4r';
const FORMATS_HINT = 'WAV · MP3 · M4A · FLAC · OGG · OPUS · WebM · AAC';

function formatBytes(b: number): string {
  if (b < 1024) return `${b} B`;
  if (b < 1048576) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / 1048576).toFixed(1)} MB`;
}

interface DropZoneProps {
  file: File | null;
  onFile: (f: File | null) => void;
  label: string;
  id: string;
}

function DropZone({ file, onFile, label, id }: DropZoneProps) {
  const [dragging, setDragging] = useState(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) onFile(f);
  };

  return (
    <div>
      {!file ? (
        <div
          className={`dropzone${dragging ? ' drag-over' : ''}`}
          onDragOver={e => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          role="button"
          tabIndex={0}
          aria-label={label}
          onKeyDown={e => {
            if (e.key === 'Enter' || e.key === ' ') {
              document.getElementById(id)?.click();
            }
          }}
        >
          <input
            id={id}
            type="file"
            accept={ACCEPTED_AUDIO}
            onChange={e => onFile(e.target.files?.[0] || null)}
            aria-label={label}
          />
          <div className="dropzone-icon">🎵</div>
          <div className="dropzone-label">{label}</div>
          <div className="dropzone-hint">Drag & drop or click to browse</div>
          <div className="dropzone-formats">{FORMATS_HINT}</div>
        </div>
      ) : (
        <div className="file-selected-banner">
          <span className="file-selected-icon">🎧</span>
          <span className="file-selected-name">{file.name}</span>
          <span className="file-selected-size">{formatBytes(file.size)}</span>
          <button
            className="file-remove-btn"
            onClick={() => onFile(null)}
            aria-label="Remove file"
            title="Remove file"
            type="button"
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
}

interface ScoreCardProps {
  label: string;
  value: number | undefined;
  meta: string;
  isOverall?: boolean;
  available?: boolean;
}

function ScoreCard({ label, value, meta, isOverall, available = true }: ScoreCardProps) {
  const pct = (value !== undefined && available && value >= 0) ? Math.min(100, value) : 0;
  return (
    <div className={`score-card${isOverall ? ' overall' : ''}`}>
      <span className="score-card-label">{label}</span>
      {available && value !== undefined ? (
        <>
          <span className="score-card-value">{value.toFixed(1)}</span>
          <div className="score-card-bar">
            <div className="score-card-bar-fill" style={{ width: `${pct}%` }} />
          </div>
        </>
      ) : (
        <span className="score-card-value unavailable">UNAVAILABLE</span>
      )}
      <span className="score-card-meta">{meta}</span>
    </div>
  );
}

export function App() {
  const [activeTab, setActiveTab] = useState<TabId>('analyze');
  const [readiness, setReadiness] = useState<ReadinessInfo | null>(null);
  const workspaceRef = useRef<HTMLDivElement>(null);

  // Analyze
  const [analyzeFile, setAnalyzeFile] = useState<File | null>(null);
  const [analyzeAudioUrl, setAnalyzeAudioUrl] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeResult, setAnalyzeResult] = useState<any>(null);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [audioDuration, setAudioDuration] = useState(0);
  const [selectedRegionIdx, setSelectedRegionIdx] = useState<number | null>(null);
  const [showTechDetails, setShowTechDetails] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Live mic
  const [isRecording, setIsRecording] = useState(false);
  const [recordSeconds, setRecordSeconds] = useState(0);
  const [micLevel, setMicLevel] = useState(0);
  const liveRecorderRef = useRef<LiveVoiceRecorder | null>(null);
  const recordTimerRef = useRef<any>(null);

  // Monitor real-time audio amplitude for Living Audio Orb
  useEffect(() => {
    if (!isRecording) {
      setMicLevel(0);
      return;
    }
    let animId = 0;
    const poll = () => {
      if (liveRecorderRef.current) {
        setMicLevel(liveRecorderRef.current.getAudioLevel());
      }
      animId = requestAnimationFrame(poll);
    };
    animId = requestAnimationFrame(poll);
    return () => cancelAnimationFrame(animId);
  }, [isRecording]);

  // Compare
  const [refFile, setRefFile] = useState<File | null>(null);
  const [candFile, setCandFile] = useState<File | null>(null);
  const [refAudioUrl, setRefAudioUrl] = useState<string | null>(null);
  const [candAudioUrl, setCandAudioUrl] = useState<string | null>(null);
  const [comparing, setComparing] = useState(false);
  const [compareResult, setCompareResult] = useState<any>(null);
  const [compareError, setCompareError] = useState<string | null>(null);

  // Arena
  const [arenaFile, setArenaFile] = useState<File | null>(null);
  const [arenaAudioUrl, setArenaAudioUrl] = useState<string | null>(null);
  const [transformType, setTransformType] = useState<'pause' | 'pace' | 'volume'>('pause');
  const [intensity, setIntensity] = useState<number>(2.0);
  const [transforming, setTransforming] = useState(false);
  const [arenaResult, setArenaResult] = useState<any>(null);
  const [arenaError, setArenaError] = useState<string | null>(null);

  // History
  const [historyRuns, setHistoryRuns] = useState<RunRecord[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historySearch, setHistorySearch] = useState('');
  const [selectedHistoryRun, setSelectedHistoryRun] = useState<RunRecord | null>(null);

  // Validation
  const [validationItems, setValidationItems] = useState<ValidationItem[]>([]);
  const [validationLoading, setValidationLoading] = useState(false);
  const [validationDisclosure, setValidationDisclosure] = useState('');

  useEffect(() => {
    fetch('/ready')
      .then(r => r.json())
      .then(d => setReadiness(d))
      .catch(() => setReadiness({ status: 'offline', device: 'unknown', cuda_available: false }));
  }, []);

  useEffect(() => {
    if (analyzeFile) {
      const url = URL.createObjectURL(analyzeFile);
      setAnalyzeAudioUrl(url);
      setAnalyzeResult(null);
      setAnalyzeError(null);
      setSelectedRegionIdx(null);
      return () => URL.revokeObjectURL(url);
    }
  }, [analyzeFile]);

  useEffect(() => {
    if (refFile) { const u = URL.createObjectURL(refFile); setRefAudioUrl(u); return () => URL.revokeObjectURL(u); }
    else setRefAudioUrl(null);
  }, [refFile]);

  useEffect(() => {
    if (candFile) { const u = URL.createObjectURL(candFile); setCandAudioUrl(u); return () => URL.revokeObjectURL(u); }
    else setCandAudioUrl(null);
  }, [candFile]);

  useEffect(() => {
    if (arenaFile) { const u = URL.createObjectURL(arenaFile); setArenaAudioUrl(u); return () => URL.revokeObjectURL(u); }
    else setArenaAudioUrl(null);
  }, [arenaFile]);

  useEffect(() => {
    if (activeTab === 'history') loadHistory();
    else if (activeTab === 'validation') loadValidation();
  }, [activeTab]);

  const loadHistory = async () => {
    setHistoryLoading(true);
    try {
      const r = await fetch('/leaderboard');
      const d = await r.json();
      setHistoryRuns(d.leaderboard || []);
    } catch { /* ignore */ } finally { setHistoryLoading(false); }
  };

  const loadValidation = async () => {
    setValidationLoading(true);
    try {
      const r = await fetch('/validation');
      const d = await r.json();
      setValidationItems(d.items || []);
      setValidationDisclosure(d.disclosure || '');
    } catch { /* ignore */ } finally { setValidationLoading(false); }
  };

  const handleStartRecord = async () => {
    try {
      setAnalyzeError(null);
      const rec = await startVoiceRecording();
      liveRecorderRef.current = rec;
      setIsRecording(true);
      setRecordSeconds(0);
      recordTimerRef.current = setInterval(() => setRecordSeconds(s => s + 1), 1000);
    } catch (err: any) { setAnalyzeError(err.message || 'Mic access failed.'); }
  };

  const handleStopRecord = async () => {
    clearInterval(recordTimerRef.current);
    setIsRecording(false);
    if (liveRecorderRef.current) {
      try { const f = await liveRecorderRef.current.stop(); setAnalyzeFile(f); }
      catch (err: any) { setAnalyzeError(err.message || 'Recording failed.'); }
      finally { liveRecorderRef.current = null; }
    }
  };

  const handleAnalyze = async () => {
    if (!analyzeFile) return;
    setAnalyzing(true); setAnalyzeError(null); setAnalyzeResult(null);
    const fd = new FormData(); fd.append('audio', analyzeFile);
    try {
      const r = await fetch('/score', { method: 'POST', body: fd });
      if (!r.ok) { const e = await r.json().catch(() => ({ detail: r.statusText })); throw new Error(e.detail); }
      const d = await r.json();
      setAnalyzeResult(d);
      if (d.duration_s) setAudioDuration(d.duration_s);
    } catch (err: any) { setAnalyzeError(err.message || 'Scoring error'); }
    finally { setAnalyzing(false); }
  };

  const handleCompare = async () => {
    if (!refFile || !candFile) return;
    setComparing(true); setCompareError(null); setCompareResult(null);
    const fd = new FormData(); fd.append('reference', refFile); fd.append('candidate', candFile);
    try {
      const r = await fetch('/compare', { method: 'POST', body: fd });
      if (!r.ok) { const e = await r.json().catch(() => ({ detail: r.statusText })); throw new Error(e.detail); }
      setCompareResult(await r.json());
    } catch (err: any) { setCompareError(err.message || 'Compare failed'); }
    finally { setComparing(false); }
  };

  const handleTransform = async () => {
    if (!arenaFile) return;
    setTransforming(true); setArenaError(null); setArenaResult(null);
    const fd = new FormData();
    fd.append('audio', arenaFile);
    fd.append('transform_type', transformType);
    fd.append('intensity', intensity.toString());
    try {
      const r = await fetch('/arena/transform', { method: 'POST', body: fd });
      if (!r.ok) { const e = await r.json().catch(() => ({ detail: r.statusText })); throw new Error(e.detail); }
      setArenaResult(await r.json());
    } catch (err: any) { setArenaError(err.message || 'Transform failed'); }
    finally { setTransforming(false); }
  };

  const seekAudio = useCallback((s: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = s;
      setCurrentTime(s);
      audioRef.current.play().catch(() => {});
    }
  }, []);

  const exportEvidence = () => {
    if (!analyzeResult) return;
    const blob = new Blob([JSON.stringify(analyzeResult, null, 2)], { type: 'application/json' });
    const u = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = u;
    a.download = `speechproof_evidence_${analyzeResult.audio_sha256?.slice(0, 8) || 'export'}.json`;
    a.click(); URL.revokeObjectURL(u);
  };

  const exportReport = () => {
    if (!analyzeResult) return;
    const scores = analyzeResult.scores || {};
    const report = `# SpeechProof Research Analysis Report
**Recording:** ${analyzeFile?.name || 'Input Audio'}
**Duration:** ${analyzeResult.duration_s?.toFixed(2) || 'N/A'}s
**Audio SHA-256:** ${analyzeResult.audio_sha256 || 'N/A'}
**Overall Score:** ${analyzeResult.metadata?.overall_score ?? 'UNAVAILABLE'}
**Scorer:** ${analyzeResult.scorer_name} ${analyzeResult.scorer_version}

## Dimension Scores
- Pace: ${scores.pace !== undefined ? scores.pace : 'UNAVAILABLE'}
- Pausing: ${scores.pausing !== undefined ? scores.pausing : 'UNAVAILABLE'}
- Fluency: ${scores.fluency !== undefined ? scores.fluency : 'UNAVAILABLE (Not Measured)'}
- Pitch Variety: ${scores.pitch !== undefined ? scores.pitch : 'UNAVAILABLE'}
- Vocal Energy: ${scores.energy !== undefined ? scores.energy : 'UNAVAILABLE'}

## Temporal Evidence
${(analyzeResult.regions || []).map((r: any, i: number) => `
### Event #${i + 1}: ${r.type || 'Flaw'}
- Interval: ${(r.start_s ?? r.start ?? 0).toFixed(2)}s - ${(r.end_s ?? r.end ?? 0).toFixed(2)}s
- Value: ${r.value ?? r.measured_value ?? 'N/A'} (Threshold: ${r.threshold ?? 'N/A'})
`).join('')}

---
*Generated by SpeechProof Research Analytics Engine*
`;
    const blob = new Blob([report], { type: 'text/markdown' });
    const u = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = u;
    a.download = `speechproof_report_${analyzeResult.audio_sha256?.slice(0, 8) || 'export'}.md`;
    a.click(); URL.revokeObjectURL(u);
  };

  const renderDelta = (delta: number | null | undefined) => {
    if (delta === null || delta === undefined) return <span className="delta-pill neutral">N/A</span>;
    if (delta > 0) return <span className="delta-pill positive">↑ +{delta.toFixed(2)}</span>;
    if (delta < 0) return <span className="delta-pill negative">↓ {delta.toFixed(2)}</span>;
    return <span className="delta-pill neutral">— 0.00</span>;
  };

  const scrollToWorkspace = () => {
    workspaceRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const navTabs: { id: TabId; label: string; icon: string }[] = [
    { id: 'analyze',    label: 'Analyze',          icon: '◈' },
    { id: 'compare',    label: 'Compare',           icon: '⇄' },
    { id: 'arena',      label: 'Crash Test Lab',    icon: '⚗' },
    { id: 'history',    label: 'Run History',       icon: '◷' },
    { id: 'validation', label: 'Validation Matrix', icon: '✓' },
  ];

  const statusClass =
    readiness?.status === 'ready' ? '' :
    readiness?.status === 'offline' ? ' offline' : ' degraded';

  const orbState: 'idle' | 'recording' | 'analyzing' | 'results' | 'error' =
    isRecording ? 'recording' :
    analyzing ? 'analyzing' :
    analyzeError ? 'error' :
    analyzeResult ? 'results' : 'idle';

  return (
    <>
      {/* HERO SECTION */}
      <section className="hero-section" aria-label="SpeechProof hero">
        <HeroCanvas
          state={orbState}
          audioLevel={micLevel}
          score={analyzeResult?.metadata?.overall_score}
          onOrbClick={() => {
            if (isRecording) {
              handleStopRecord();
            } else {
              setActiveTab('analyze');
              scrollToWorkspace();
            }
          }}
        />
        <div className="hero-gradient-overlay" aria-hidden="true" />
        <div className="hero-grid-lines" aria-hidden="true" />

        <nav className="hero-nav" aria-label="Top navigation">
          <div className="hero-nav-brand">
            <div className="hero-nav-brand-logo" aria-hidden="true">SP</div>
            <span className="hero-nav-brand-name">SpeechProof</span>
          </div>
          <div className="hero-nav-status" role="status" aria-live="polite">
            <span className={`status-dot${statusClass}`} aria-hidden="true" />
            <span>
              {readiness?.status === 'ready'
                ? `CUDA · ${readiness.compute_type || 'float16'} · large-v3`
                : readiness?.status === 'offline'
                  ? 'Backend offline'
                  : `${readiness?.status ?? 'Connecting…'}`
              }
            </span>
          </div>
        </nav>

        <div className="hero-content">
          <div className="hero-eyebrow">Audio Intelligence Research Platform</div>
          <h1 className="hero-headline">
            Every word.<br />Every pause.<br />
            <span className="hero-headline-accent">Fully auditable.</span>
          </h1>
          <p className="hero-sub">
            Deterministic ASR scoring with SHA-256 grounded evidence,
            timestamped flaw intervals, and contrastive crash testing.
            Upload any audio format — we normalize it server-side.
          </p>

          {/* Dynamic Living Orb Status Banner */}
          {isRecording ? (
            <div className="hero-live-status recording" role="status" aria-live="polite">
              <span className="live-rec-dot" />
              <span>RECORDING LIVE AUDIO · {String(Math.floor(recordSeconds / 60)).padStart(2, '0')}:{String(recordSeconds % 60).padStart(2, '0')}</span>
              <div className="hero-vu-meter" title={`Mic level: ${Math.round(micLevel * 100)}%`}>
                <div className="hero-vu-fill" style={{ width: `${Math.min(100, Math.round(micLevel * 100))}%` }} />
              </div>
              <button className="btn btn-hero-stop" onClick={handleStopRecord}>■ Stop & Ingest</button>
            </div>
          ) : analyzing ? (
            <div className="hero-live-status analyzing" role="status" aria-live="polite">
              <span className="spinner mint" />
              <span>EXTRACTING TEMPORAL EVIDENCE & RUNNING DETERMINISTIC SCORER…</span>
            </div>
          ) : analyzeResult ? (
            <div className="hero-live-status results" role="status">
              <span>✓ ANALYSIS COMPLETE · OVERALL SCORE: <strong>{analyzeResult.metadata?.overall_score?.toFixed(1) ?? 'N/A'}</strong></span>
              <button className="btn btn-hero-jump" onClick={scrollToWorkspace}>Inspect Evidence ↓</button>
            </div>
          ) : (
            <div className="hero-actions">
              <button
                className="btn btn-hero-primary"
                onClick={() => { setActiveTab('analyze'); scrollToWorkspace(); }}
              >
                ◈ Analyse a Recording
              </button>
              <button
                className="btn btn-hero-mic"
                onClick={handleStartRecord}
                aria-label="Start recording from microphone"
              >
                🎙 Record Voice
              </button>
              <button
                className="btn btn-hero-secondary"
                onClick={() => { setActiveTab('compare'); scrollToWorkspace(); }}
              >
                ⇄ Compare Deliveries
              </button>
            </div>
          )}
        </div>

        <div className="hero-scroll-hint" aria-hidden="true" onClick={scrollToWorkspace} style={{ cursor: 'pointer' }}>
          <div className="scroll-mouse" />
          <span>Scroll to workspace</span>
        </div>
      </section>

      {/* WORKSPACE SECTION */}
      <section className="workspace-section" ref={workspaceRef}>
        <div className="workspace-container">

          {/* Sticky navigation */}
          <div className="workspace-nav-sticky">
            <nav className="nav-tabs" aria-label="Workspace navigation" role="tablist">
              {navTabs.map(t => (
                <button
                  key={t.id}
                  id={`tab-${t.id}`}
                  className={`nav-tab-btn${activeTab === t.id ? ' active' : ''}`}
                  onClick={() => setActiveTab(t.id)}
                  aria-selected={activeTab === t.id}
                  role="tab"
                  aria-controls={`panel-${t.id}`}
                >
                  <span style={{ opacity: 0.7, marginRight: 5 }}>{t.icon}</span>
                  {t.label}
                </button>
              ))}
            </nav>
          </div>

          {/* TAB: ANALYZE */}
          {activeTab === 'analyze' && (
            <div id="panel-analyze" className="card-enter" role="tabpanel" aria-labelledby="tab-analyze">
              <div className="section-header">
                <div className="section-tag">Recording Analysis</div>
                <h2 className="section-title">Speech Analysis</h2>
                <p className="section-subtitle">
                  Upload any common audio format. Normalized server-side to 16 kHz mono WAV.
                  faster-whisper ASR, deterministic rubric scores, and temporal evidence.
                </p>
              </div>

              <div className="card">
                <div className="card-header">
                  <div>
                    <div className="card-title">Audio Input</div>
                    <div className="card-subtitle">Upload a file or record from your microphone</div>
                  </div>
                  <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
                    {!isRecording ? (
                      <button type="button" className="btn btn-record" onClick={handleStartRecord} aria-label="Start microphone recording">
                        <span style={{ color: '#F87171', fontSize: 12 }}>●</span> Record Mic
                      </button>
                    ) : (
                      <button type="button" className="btn btn-record-active" onClick={handleStopRecord} aria-label="Stop recording">
                        <span className="spinner" style={{ width: 12, height: 12, borderTopColor: '#F87171', borderWidth: 2 }} />
                        Stop {Math.floor(recordSeconds / 60)}:{(recordSeconds % 60).toString().padStart(2, '0')}
                      </button>
                    )}
                    <button
                      className="btn btn-primary"
                      disabled={!analyzeFile || analyzing || isRecording}
                      onClick={handleAnalyze}
                      aria-label="Run speech analysis"
                    >
                      {analyzing ? <><span className="spinner" /> Scoring…</> : '◈ Run Analysis'}
                    </button>
                  </div>
                </div>

                <DropZone file={analyzeFile} onFile={f => setAnalyzeFile(f)} label="Drop audio here or click to upload" id="analyze-file-input" />

                {analyzeAudioUrl && (
                  <div className="audio-player-wrapper" style={{ marginTop: 16 }}>
                    <div className="audio-player-label">Source Audio Playback</div>
                    <audio
                      ref={audioRef}
                      src={analyzeAudioUrl}
                      controls
                      onTimeUpdate={e => setCurrentTime((e.target as HTMLAudioElement).currentTime)}
                      onLoadedMetadata={e => {
                        const d = (e.target as HTMLAudioElement).duration;
                        if (d && isFinite(d)) setAudioDuration(d);
                      }}
                    />
                  </div>
                )}

                {analyzeError && (
                  <div className="notice-banner error" style={{ marginTop: 16 }} role="alert">
                    <strong>Analysis Failed:</strong> {analyzeError}
                  </div>
                )}
              </div>

              {analyzeResult && (
                <>
                  <div className="score-grid">
                    <div className="score-card overall">
                      <span className="score-card-label">Overall Delivery Score</span>
                      {analyzeResult.metadata?.overall_score != null ? (
                        <>
                          <span className="score-card-value">{analyzeResult.metadata.overall_score.toFixed(1)}</span>
                          <div className="score-card-bar">
                            <div className="score-card-bar-fill" style={{ width: `${Math.min(100, analyzeResult.metadata.overall_score)}%` }} />
                          </div>
                        </>
                      ) : (
                        <span className="score-card-value unavailable">N/A</span>
                      )}
                      <span className="score-card-meta" style={{ fontFamily: 'var(--font-mono)', fontSize: 10 }}>
                        {analyzeResult.duration_s?.toFixed(2)}s · SHA: {analyzeResult.audio_sha256?.slice(0, 10)}…
                      </span>
                    </div>
                    <ScoreCard label="Pace" value={analyzeResult.scores?.pace} meta="Target: 100–180 WPM" />
                    <ScoreCard
                      label="Fluency"
                      value={analyzeResult.scores?.fluency}
                      meta={
                        analyzeResult.scores?.fluency !== undefined
                          ? "Heuristic (≤ 5 fillers/min)"
                          : "Uncalibrated in offline Whisper (omitted to avoid false zero)"
                      }
                      available={analyzeResult.scores?.fluency !== undefined}
                    />
                    <ScoreCard label="Pitch Variety" value={analyzeResult.scores?.pitch} meta="Target: ≥ 1.0 semitone std" />
                    <ScoreCard label="Vocal Energy" value={analyzeResult.scores?.energy} meta="Target: ≥ 3.0 dB RMS std" />
                  </div>

                  <div className="notice-banner info" style={{ marginTop: 14 }}>
                    <strong>Scientific Transparency:</strong> Pace, Pausing, Pitch Variety, and Vocal Energy are deterministically measured from acoustic signal features. Fluency (filler word rate) requires dedicated acoustic disfluency modeling; because offline Whisper produces intended text without guaranteed filler tagging, SpeechProof explicitly omits Fluency (marked <em>UNAVAILABLE</em>) rather than injecting an arbitrary zero penalty into the delivery score.
                  </div>

                  {analyzeResult.quality_flags?.length > 0 && (
                    <div className="notice-banner warning">
                      <strong>Pipeline Flags:</strong> {analyzeResult.quality_flags.join(', ')}
                    </div>
                  )}

                  <div className="card">
                    <div className="card-header">
                      <div>
                        <div className="card-title">Temporal Waveform & Evidence Anchors</div>
                        <div className="card-subtitle">Click regions to inspect evidence. Seek bar stays synchronized.</div>
                      </div>
                      <div style={{ display: 'flex', gap: 8 }}>
                        <button className="btn btn-secondary" onClick={exportEvidence} aria-label="Export evidence as JSON">Export JSON</button>
                        <button className="btn btn-ghost" onClick={exportReport} aria-label="Download markdown report">Report MD</button>
                      </div>
                    </div>

                    <WaveformCanvas
                      audioFile={analyzeFile}
                      regions={analyzeResult.regions || []}
                      selectedRegionIndex={selectedRegionIdx}
                      onSelectRegion={idx => setSelectedRegionIdx(idx)}
                      currentTime={currentTime}
                      duration={analyzeResult.duration_s || audioDuration || 1}
                      onSeek={seekAudio}
                    />

                    {selectedRegionIdx !== null && analyzeResult.regions?.[selectedRegionIdx] && (() => {
                      const reg: EvidenceRegion = analyzeResult.regions[selectedRegionIdx];
                      const start = reg.start_s ?? reg.start ?? 0;
                      const end = reg.end_s ?? reg.end ?? start;
                      const val = reg.value ?? reg.measured_value ?? 'N/A';
                      const thresh = reg.threshold ?? '—';
                      return (
                        <div className="evidence-inspector">
                          <div className="evidence-inspector-header">
                            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                              <span className="evidence-badge">{reg.type || 'flaw'}</span>
                              <span className="evidence-time">
                                {start.toFixed(2)}s → {end.toFixed(2)}s
                                <span style={{ fontSize: 12, color: 'var(--muted-text)', marginLeft: 8 }}>({(end - start).toFixed(2)}s)</span>
                              </span>
                            </div>
                            <button className="btn btn-secondary" style={{ padding: '6px 14px', fontSize: 12 }} onClick={() => seekAudio(start)} aria-label="Seek to evidence interval">
                              ▶ Play Interval
                            </button>
                          </div>
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, fontSize: 13, color: 'var(--muted-text)' }}>
                            <div>Measured: <strong style={{ color: 'var(--soft-canvas)' }}>{val}s</strong></div>
                            <div>Threshold: <strong style={{ color: 'var(--soft-canvas)' }}>{thresh}s</strong></div>
                          </div>
                          {reg.words_before && reg.words_after && (
                            <div className="evidence-context" style={{ marginTop: 10 }}>
                              Context: "<em>{(reg.words_before || []).join(' ')}</em>{' '}
                              <span className="evidence-flaw-mark">[FLAW]</span>{' '}
                              <em>{(reg.words_after || []).join(' ')}</em>"
                            </div>
                          )}
                        </div>
                      );
                    })()}

                    <div style={{ marginTop: 20 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                        <h4 style={{ fontSize: 12, color: 'var(--muted-text)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.8px' }}>
                          Detected Flaw Intervals ({analyzeResult.regions?.length || 0})
                        </h4>
                      </div>
                      {analyzeResult.regions?.length > 0 ? (
                        <div className="table-responsive">
                          <table className="regions-table" aria-label="Evidence regions">
                            <thead>
                              <tr>
                                <th>Type</th><th>Time Window</th><th>Duration</th>
                                <th>Measured</th><th>Threshold</th><th>Context</th><th>Seek</th>
                              </tr>
                            </thead>
                            <tbody>
                              {analyzeResult.regions.map((reg: any, idx: number) => {
                                const s = reg.start_s ?? reg.start ?? 0;
                                const e = reg.end_s ?? reg.end ?? s;
                                return (
                                  <tr key={idx} className={selectedRegionIdx === idx ? 'selected' : ''} onClick={() => setSelectedRegionIdx(idx)}>
                                    <td><span className="badge badge-inconclusive">{reg.type || 'flaw'}</span></td>
                                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>{s.toFixed(2)}s – {e.toFixed(2)}s</td>
                                    <td style={{ fontFamily: 'var(--font-mono)' }}>{(e - s).toFixed(2)}s</td>
                                    <td>{reg.value ?? reg.measured_value ?? '—'}</td>
                                    <td>{reg.threshold ?? '—'}</td>
                                    <td style={{ maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 12, color: 'var(--muted-text)' }}>
                                      {(reg.words_before || []).join(' ')} … {(reg.words_after || []).join(' ')}
                                    </td>
                                    <td>
                                      <button
                                        className="btn btn-secondary"
                                        style={{ padding: '4px 10px', fontSize: 11 }}
                                        onClick={ev => { ev.stopPropagation(); setSelectedRegionIdx(idx); seekAudio(s); }}
                                        aria-label={`Seek to ${s.toFixed(2)}s`}
                                      >▶</button>
                                    </td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <p style={{ color: 'var(--muted-text)', fontSize: 13 }}>No threshold-exceeding flaws detected in this recording.</p>
                      )}
                    </div>
                  </div>

                  <div className="card">
                    <div
                      className="flex-between"
                      style={{ cursor: 'pointer' }}
                      onClick={() => setShowTechDetails(!showTechDetails)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={e => { if (e.key === 'Enter') setShowTechDetails(v => !v); }}
                      aria-expanded={showTechDetails}
                    >
                      <div className="card-title" style={{ fontSize: 14 }}>Advanced Evidence Integrity & Model Metadata</div>
                      <span style={{ fontSize: 12, color: 'var(--violet-light)' }}>{showTechDetails ? '▲ Collapse' : '▼ Expand'}</span>
                    </div>
                    {showTechDetails && (
                      <div style={{ marginTop: 16 }}>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))', gap: 12, marginBottom: 16, fontSize: 12, color: 'var(--muted-text)' }}>
                          <div>Audio SHA-256: <code style={{ color: 'var(--mint)', fontSize: 11 }}>{analyzeResult.audio_sha256}</code></div>
                          <div>Evidence SHA-256: <code style={{ color: 'var(--mint)', fontSize: 11 }}>{analyzeResult.metadata?.evidence_sha256}</code></div>
                          <div>Run ID: <code>{analyzeResult.metadata?.run_id || 'N/A'}</code></div>
                          <div>Rubric: <code>{analyzeResult.metadata?.rubric_version}</code></div>
                        </div>
                        <pre className="code-block">{JSON.stringify(analyzeResult, null, 2)}</pre>
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          )}

          {/* TAB: COMPARE */}
          {activeTab === 'compare' && (
            <div id="panel-compare" className="card-enter" role="tabpanel" aria-labelledby="tab-compare">
              <div className="section-header">
                <div className="section-tag">Contrastive Analysis</div>
                <h2 className="section-title">Compare Deliveries</h2>
                <p className="section-subtitle">
                  Delta = Candidate − Reference. A positive delta indicates higher candidate scoring.
                  It does not imply statistical significance or clinical superiority.
                </p>
              </div>

              <div className="card">
                <div className="compare-grid" style={{ marginBottom: 20 }}>
                  <div className="compare-panel">
                    <div className="compare-panel-label reference">◈ Reference Recording</div>
                    <DropZone file={refFile} onFile={f => { setRefFile(f); setCompareResult(null); setCompareError(null); }} label="Upload reference audio" id="ref-file-input" />
                    {refAudioUrl && (
                      <div className="audio-player-wrapper">
                        <div className="audio-player-label">Reference Playback</div>
                        <audio src={refAudioUrl} controls />
                      </div>
                    )}
                  </div>
                  <div className="compare-panel">
                    <div className="compare-panel-label candidate">◈ Candidate Recording</div>
                    <DropZone file={candFile} onFile={f => { setCandFile(f); setCompareResult(null); setCompareError(null); }} label="Upload candidate audio" id="cand-file-input" />
                    {candAudioUrl && (
                      <div className="audio-player-wrapper">
                        <div className="audio-player-label">Candidate Playback</div>
                        <audio src={candAudioUrl} controls />
                      </div>
                    )}
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <button className="btn btn-primary" disabled={!refFile || !candFile || comparing} onClick={handleCompare}>
                    {comparing ? <><span className="spinner" /> Scoring Deliveries…</> : '⇄ Run Comparison'}
                  </button>
                </div>

                {compareError && (
                  <div className="notice-banner error" style={{ marginTop: 16 }} role="alert">
                    <strong>Comparison Error:</strong> {compareError}
                  </div>
                )}
              </div>

              {compareResult && (
                <>
                  <div className="notice-banner">
                    <strong>Scientific Methodology Notice:</strong> This quantifies rubric deltas between two files.
                    A positive delta indicates higher candidate scoring on that dimension.
                    Statistical significance, clinical superiority, and transcript alignment are not asserted.
                  </div>
                  <div className="card">
                    <div className="card-title" style={{ marginBottom: 16 }}>Score Deltas Breakdown</div>
                    <div className="table-responsive">
                      <table className="regions-table" aria-label="Score comparison table">
                        <thead>
                          <tr>
                            <th>Dimension</th><th>Reference</th><th>Candidate</th>
                            <th>Delta (Cand − Ref)</th><th>Direction</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td><strong>Overall</strong></td>
                            <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{compareResult.reference?.metadata?.overall_score ?? '—'}</td>
                            <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{compareResult.candidate?.metadata?.overall_score ?? '—'}</td>
                            <td>{renderDelta(compareResult.overall_delta)}</td>
                            <td style={{ fontSize: 12, color: 'var(--muted-text)' }}>
                              {compareResult.overall_delta > 0 ? '↑ Higher' : compareResult.overall_delta < 0 ? '↓ Lower' : '— Same'}
                            </td>
                          </tr>
                          {['pace', 'pausing', 'pitch', 'energy'].map(dim => {
                            const rv = compareResult.reference?.scores?.[dim];
                            const cv = compareResult.candidate?.scores?.[dim];
                            const diff = compareResult.differences?.[dim];
                            return (
                              <tr key={dim}>
                                <td style={{ textTransform: 'capitalize' }}>{dim}</td>
                                <td>{rv !== undefined ? rv.toFixed(1) : <span style={{ color: 'var(--muted-text)' }}>N/A</span>}</td>
                                <td>{cv !== undefined ? cv.toFixed(1) : <span style={{ color: 'var(--muted-text)' }}>N/A</span>}</td>
                                <td>{renderDelta(diff)}</td>
                                <td style={{ fontSize: 12, color: 'var(--muted-text)' }}>
                                  {diff > 0 ? '↑ Higher' : diff < 0 ? '↓ Lower' : '— Same'}
                                </td>
                              </tr>
                            );
                          })}
                          <tr>
                            <td>Fluency</td>
                            <td><span style={{ color: 'var(--muted-text)', fontSize: 12 }}>UNAVAILABLE</span></td>
                            <td><span style={{ color: 'var(--muted-text)', fontSize: 12 }}>UNAVAILABLE</span></td>
                            <td><span className="delta-pill neutral">N/A</span></td>
                            <td style={{ fontSize: 12, color: 'var(--muted-text)' }}>Uncalibrated in v0.1</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <div style={{ marginTop: 16, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, fontSize: 12, color: 'var(--muted-text)' }}>
                      <div>
                        Ref SHA: <code style={{ color: 'var(--mint)', fontSize: 11 }}>{compareResult.reference_sha256?.slice(0, 16)}…</code><br />
                        Duration: {compareResult.reference_duration_s?.toFixed(2)}s
                      </div>
                      <div>
                        Cand SHA: <code style={{ color: 'var(--mint)', fontSize: 11 }}>{compareResult.candidate_sha256?.slice(0, 16)}…</code><br />
                        Duration: {compareResult.candidate_duration_s?.toFixed(2)}s
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* TAB: CRASH TEST LAB */}
          {activeTab === 'arena' && (
            <div id="panel-arena" className="card-enter" role="tabpanel" aria-labelledby="tab-arena">
              <div className="section-header">
                <div className="section-tag">Controlled Flaw Injection</div>
                <h2 className="section-title">Crash Test Lab ⚗</h2>
                <p className="section-subtitle">
                  Deterministic audio transformations to audit rubric response.
                  Safety ranges shown are interface bounds, not scientifically calibrated thresholds.
                </p>
              </div>

              <div className="card crash-lab-header-accent">
                <div className="grid-2">
                  <div>
                    <div className="card-title" style={{ marginBottom: 16 }}>Base Recording</div>
                    <DropZone file={arenaFile} onFile={f => { setArenaFile(f); setArenaResult(null); setArenaError(null); }} label="Upload audio for transformation" id="arena-file-input" />
                    {arenaAudioUrl && (
                      <div className="audio-player-wrapper">
                        <div className="audio-player-label">Original Audio</div>
                        <audio src={arenaAudioUrl} controls />
                      </div>
                    )}
                  </div>

                  <div className="crash-transform-controls">
                    <div className="card-title" style={{ marginBottom: 16 }}>Transformation Controls</div>
                    <div className="form-group">
                      <label className="form-label" htmlFor="transform-type">Transformation Type</label>
                      <select
                        id="transform-type"
                        className="form-control"
                        value={transformType}
                        onChange={e => {
                          const t = e.target.value as 'pause' | 'pace' | 'volume';
                          setTransformType(t);
                          if (t === 'pause') setIntensity(2.0);
                          else if (t === 'pace') setIntensity(1.2);
                          else setIntensity(-6.0);
                        }}
                      >
                        <option value="pause">Pause Insertion → Pausing score</option>
                        <option value="pace">Pace Modification → Pace score</option>
                        <option value="volume">Volume Modification → Energy score</option>
                      </select>
                    </div>
                    <div className="form-group">
                      <label className="form-label" htmlFor="intensity-input">
                        {transformType === 'pause' && `Pause Duration: ${intensity.toFixed(1)}s [0.5 – 5.0s]`}
                        {transformType === 'pace' && `Speed Rate: ${intensity.toFixed(2)}× [0.5× – 1.5×]`}
                        {transformType === 'volume' && `Gain: ${intensity > 0 ? '+' : ''}${intensity.toFixed(1)} dB [−12 – +12 dB]`}
                      </label>
                      <input
                        id="intensity-input"
                        type="range"
                        className="form-control"
                        value={intensity}
                        step={transformType === 'pace' ? 0.05 : transformType === 'pause' ? 0.1 : 1}
                        min={transformType === 'volume' ? -12 : 0.5}
                        max={transformType === 'volume' ? 12 : transformType === 'pace' ? 1.5 : 5}
                        onChange={e => setIntensity(parseFloat(e.target.value))}
                        aria-label="Transformation intensity"
                      />
                      <div className="form-helper">
                        {transformType === 'pause' && 'Splits audio at midpoint and inserts exact silence interval.'}
                        {transformType === 'pace' && 'Time-stretches via phase vocoder, preserving pitch.'}
                        {transformType === 'volume' && 'Applies linear gain and flags hard clipping events.'}
                      </div>
                    </div>
                    <button
                      className="btn btn-primary"
                      style={{ width: '100%', marginTop: 8 }}
                      disabled={!arenaFile || transforming}
                      onClick={handleTransform}
                    >
                      {transforming ? <><span className="spinner" /> Transforming & Scoring…</> : '⚗ Execute Crash Test'}
                    </button>
                  </div>
                </div>

                {arenaError && (
                  <div className="notice-banner error" style={{ marginTop: 16 }} role="alert">
                    <strong>Crash Test Failed:</strong> {arenaError}
                  </div>
                )}
              </div>

              {arenaResult && (
                <>
                  <div className="card">
                    <div className="card-title" style={{ marginBottom: 14 }}>Automated Verification Outcome</div>
                    <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 16 }}>
                      <div className="crash-outcome-badge good">✓ Transformation Complete</div>
                      <div className="crash-outcome-badge good">✓ Scoring Complete</div>
                      <div className={`crash-outcome-badge ${arenaResult.target_responded ? 'good' : 'warn'}`}>
                        {arenaResult.target_responded ? '✓' : '!'} Target ({arenaResult.intended_target}): {arenaResult.target_responded ? 'Responded' : 'Unchanged'}
                      </div>
                      <div className={`crash-outcome-badge ${arenaResult.unrelated_changed ? 'warn' : 'good'}`}>
                        {arenaResult.unrelated_changed ? '!' : '✓'} Cross-Talk: {arenaResult.unrelated_changed ? 'Off-target affected' : 'Isolated'}
                      </div>
                      <div className={`crash-outcome-badge ${arenaResult.clipping_occurred ? 'bad' : 'good'}`}>
                        {arenaResult.clipping_occurred ? '⚠ Clipping detected' : '✓ Clean signal'}
                      </div>
                    </div>
                    {arenaResult.warnings?.length > 0 && (
                      <div className="notice-banner warning">
                        {arenaResult.warnings.map((w: string, i: number) => <div key={i}>{w}</div>)}
                      </div>
                    )}
                    {arenaResult.audio_data_url && (
                      <div className="audio-player-wrapper">
                        <div className="audio-player-label">Transformed Output Audio</div>
                        <audio src={arenaResult.audio_data_url} controls />
                      </div>
                    )}
                  </div>

                  <div className="card">
                    <div className="card-title" style={{ marginBottom: 14 }}>Original vs Transformed Rubric Scores</div>
                    <div className="table-responsive">
                      <table className="regions-table" aria-label="Crash test score comparison">
                        <thead>
                          <tr>
                            <th>Dimension</th><th>Original</th><th>Transformed</th><th>Delta</th><th>Role</th>
                          </tr>
                        </thead>
                        <tbody>
                          {['pace', 'pausing', 'pitch', 'energy'].map(dim => {
                            const ov = arenaResult.original?.scores?.[dim];
                            const tv = arenaResult.transformed?.scores?.[dim];
                            const delta = arenaResult.differences?.[dim];
                            const isTarget = dim === arenaResult.intended_target;
                            return (
                              <tr key={dim} style={{ background: isTarget ? 'rgba(121,107,250,0.08)' : undefined }}>
                                <td style={{ textTransform: 'capitalize', fontWeight: isTarget ? 700 : 400 }}>
                                  {dim} {isTarget && '🎯'}
                                </td>
                                <td>{ov !== undefined ? ov.toFixed(1) : <span style={{ color: 'var(--muted-text)' }}>—</span>}</td>
                                <td>{tv !== undefined ? tv.toFixed(1) : <span style={{ color: 'var(--muted-text)' }}>—</span>}</td>
                                <td>{renderDelta(delta)}</td>
                                <td>
                                  {isTarget
                                    ? <span className="badge badge-pilot">Intended Target</span>
                                    : <span style={{ color: 'var(--muted-text)', fontSize: 11 }}>Off-target</span>
                                  }
                                </td>
                              </tr>
                            );
                          })}
                          <tr>
                            <td><strong>Overall</strong></td>
                            <td style={{ fontWeight: 600 }}>{arenaResult.original?.metadata?.overall_score ?? '—'}</td>
                            <td style={{ fontWeight: 600 }}>{arenaResult.transformed?.metadata?.overall_score ?? '—'}</td>
                            <td>{renderDelta(arenaResult.overall_delta)}</td>
                            <td><span style={{ color: 'var(--muted-text)', fontSize: 11 }}>Composite</span></td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <div style={{ marginTop: 14, fontSize: 11, color: 'var(--muted-text)', fontFamily: 'var(--font-mono)' }}>
                      Original SHA: {arenaResult.original_sha256?.slice(0, 16)}… | Transformed SHA: {arenaResult.transformed_sha256?.slice(0, 16)}…
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* TAB: HISTORY */}
          {activeTab === 'history' && (
            <div id="panel-history" className="card-enter" role="tabpanel" aria-labelledby="tab-history">
              <div className="section-header">
                <div className="section-tag">Audit Ledger</div>
                <h2 className="section-title">Run History</h2>
                <p className="section-subtitle">All scoring runs persisted in SQLite. File paths sanitized. SHA-256 integrity preserved.</p>
              </div>

              <div className="card">
                <div className="card-header">
                  <div className="card-title">Scoring Ledger</div>
                  <button className="btn btn-secondary" onClick={loadHistory} disabled={historyLoading} aria-label="Refresh ledger">
                    {historyLoading ? <span className="spinner violet" /> : '↻ Refresh'}
                  </button>
                </div>

                <div className="history-search">
                  <input
                    type="text"
                    className="form-control"
                    placeholder="Filter by file name or SHA-256 prefix…"
                    value={historySearch}
                    onChange={e => setHistorySearch(e.target.value)}
                    aria-label="Search history"
                  />
                </div>

                <div className="table-responsive">
                  <table className="regions-table" aria-label="Run history table">
                    <thead>
                      <tr>
                        <th>Run ID</th><th>Recording</th><th>Overall</th>
                        <th>Dimensions</th><th>Duration</th><th>SHA-256</th><th>Recorded At</th>
                      </tr>
                    </thead>
                    <tbody>
                      {historyLoading ? (
                        <tr><td colSpan={7} style={{ textAlign: 'center', padding: 24 }}><span className="spinner violet" /></td></tr>
                      ) : historyRuns
                        .filter(r =>
                          r.recording_name.toLowerCase().includes(historySearch.toLowerCase()) ||
                          r.sha256_prefix.toLowerCase().includes(historySearch.toLowerCase())
                        )
                        .map(run => (
                          <tr key={run.run_id} onClick={() => setSelectedHistoryRun(run === selectedHistoryRun ? null : run)}>
                            <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>#{run.run_id}</td>
                            <td><strong>{run.recording_name}</strong></td>
                            <td>
                              {run.overall_score !== null
                                ? <span className="badge badge-met" style={{ fontSize: 12 }}>{run.overall_score.toFixed(1)}</span>
                                : <span className="badge badge-notrun">N/A</span>
                              }
                            </td>
                            <td style={{ fontSize: 12 }}>
                              {Object.entries(run.scores || {}).map(([k, v]) => (
                                <span key={k} style={{ marginRight: 8, color: 'var(--muted-text)' }}>{k}: {v}</span>
                              ))}
                            </td>
                            <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>{run.duration_s ? `${run.duration_s.toFixed(1)}s` : '—'}</td>
                            <td style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--mint)' }}>{run.sha256_prefix}…</td>
                            <td style={{ fontSize: 12, color: 'var(--muted-text)' }}>{run.created_at}</td>
                          </tr>
                        ))
                      }
                    </tbody>
                  </table>
                </div>

                {selectedHistoryRun && (
                  <div className="history-run-details">
                    <div className="flex-between" style={{ marginBottom: 12 }}>
                      <h4 style={{ fontFamily: 'var(--font-display)', fontSize: 15 }}>Run #{selectedHistoryRun.run_id} Details</h4>
                      <button className="btn btn-ghost" style={{ padding: '4px 10px', fontSize: 12 }} onClick={() => setSelectedHistoryRun(null)}>✕ Close</button>
                    </div>
                    <div style={{ fontSize: 13, lineHeight: 1.8, color: 'var(--muted-text)' }}>
                      <div><strong style={{ color: 'var(--soft-canvas)' }}>File:</strong> {selectedHistoryRun.recording_name}</div>
                      <div><strong style={{ color: 'var(--soft-canvas)' }}>SHA-256:</strong> <code style={{ fontSize: 11, color: 'var(--mint)' }}>{selectedHistoryRun.sha256}</code></div>
                      <div><strong style={{ color: 'var(--soft-canvas)' }}>Scorer / Rubric:</strong> {selectedHistoryRun.scorer_name} ({selectedHistoryRun.rubric_version})</div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB: VALIDATION */}
          {activeTab === 'validation' && (
            <div id="panel-validation" className="card-enter" role="tabpanel" aria-labelledby="tab-validation">
              <div className="section-header">
                <div className="section-tag">Empirical Validation Battery</div>
                <h2 className="section-title">Validation Matrix</h2>
                <p className="section-subtitle">
                  Live verification results from T1-T9 evaluation artifacts.
                  Strictly distinguishing MET, PILOT, INCONCLUSIVE, and NOT_RUN.
                </p>
              </div>

              <div className="card">
                <div className="card-header">
                  <div className="card-title">T1–T9 & A1–A5 Evaluations</div>
                  <button className="btn btn-secondary" onClick={loadValidation} disabled={validationLoading} aria-label="Reload artifacts">
                    {validationLoading ? <span className="spinner violet" /> : '↻ Reload Artifacts'}
                  </button>
                </div>

                {validationDisclosure && (
                  <div className="notice-banner warning" style={{ marginBottom: 20 }}>
                    {validationDisclosure}
                  </div>
                )}

                {validationLoading ? (
                  <div style={{ textAlign: 'center', padding: 40 }}><span className="spinner violet" /></div>
                ) : (
                  <div className="validation-grid">
                    {validationItems.map(item => {
                      let badgeClass = 'badge-inconclusive';
                      if (item.status === 'MET') badgeClass = 'badge-met';
                      else if (item.status === 'PILOT') badgeClass = 'badge-pilot';
                      else if (item.status === 'NOT_RUN' || item.status === 'NOT_SUPPORTED') badgeClass = 'badge-notrun';
                      else if (item.status === 'FAILED') badgeClass = 'badge-failed';
                      return (
                        <div key={item.id} className="validation-card">
                          <div className="validation-card-header">
                            <span className="validation-card-title">{item.name}</span>
                            <span className={`badge ${badgeClass}`}>{item.status}</span>
                          </div>
                          {item.metric && (
                            <div className="validation-metric-row">
                              <span className="validation-metric-label">Metric</span>
                              <span className="validation-metric-val">{item.metric}</span>
                            </div>
                          )}
                          {item.value != null && (
                            <div className="validation-metric-row">
                              <span className="validation-metric-label">Observed</span>
                              <span className="validation-metric-val">{String(item.value)}</span>
                            </div>
                          )}
                          {item.target && (
                            <div className="validation-metric-row">
                              <span className="validation-metric-label">Target</span>
                              <span className="validation-metric-val" style={{ fontSize: 11 }}>{item.target}</span>
                            </div>
                          )}
                          <div style={{ fontSize: 12, color: 'var(--muted-text)', lineHeight: 1.5 }}>{item.reason}</div>
                          {item.limitations?.length > 0 && (
                            <div style={{ fontSize: 11, color: 'var(--status-inconclusive)', lineHeight: 1.4 }}>
                              <strong>Limitations:</strong> {item.limitations.join('; ')}
                            </div>
                          )}
                          {item.raw_artifact && (
                            <div style={{ fontSize: 10, color: 'var(--muted-text)', fontFamily: 'var(--font-mono)', marginTop: 4 }}>
                              {item.raw_artifact}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          )}

        </div>
      </section>
    </>
  );
}

export default App;
