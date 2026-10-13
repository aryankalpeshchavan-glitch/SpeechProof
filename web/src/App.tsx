import { useState, useEffect, useRef } from 'react';
import { WaveformCanvas, type EvidenceRegion } from './WaveformCanvas';

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

export function App() {
  const [activeTab, setActiveTab] = useState<'analyze' | 'compare' | 'arena' | 'history' | 'validation'>('analyze');
  const [readiness, setReadiness] = useState<ReadinessInfo | null>(null);

  // Analyze Tab State
  const [analyzeFile, setAnalyzeFile] = useState<File | null>(null);
  const [analyzeAudioUrl, setAnalyzeAudioUrl] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeResult, setAnalyzeResult] = useState<any>(null);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [audioDuration, setAudioDuration] = useState(0);
  const [selectedRegionIdx, setSelectedRegionIdx] = useState<number | null>(null);
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Compare Tab State
  const [refFile, setRefFile] = useState<File | null>(null);
  const [candFile, setCandFile] = useState<File | null>(null);
  const [refAudioUrl, setRefAudioUrl] = useState<string | null>(null);
  const [candAudioUrl, setCandAudioUrl] = useState<string | null>(null);
  const [comparing, setComparing] = useState(false);
  const [compareResult, setCompareResult] = useState<any>(null);
  const [compareError, setCompareError] = useState<string | null>(null);

  // Arena (Crash Test Lab) State
  const [arenaFile, setArenaFile] = useState<File | null>(null);
  const [arenaAudioUrl, setArenaAudioUrl] = useState<string | null>(null);
  const [transformType, setTransformType] = useState<'pause' | 'pace' | 'volume'>('pause');
  const [intensity, setIntensity] = useState<number>(2.0);
  const [transforming, setTransforming] = useState(false);
  const [arenaResult, setArenaResult] = useState<any>(null);
  const [arenaError, setArenaError] = useState<string | null>(null);

  // History Tab State
  const [historyRuns, setHistoryRuns] = useState<RunRecord[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historySearch, setHistorySearch] = useState('');
  const [selectedHistoryRun, setSelectedHistoryRun] = useState<RunRecord | null>(null);

  // Validation Tab State
  const [validationItems, setValidationItems] = useState<ValidationItem[]>([]);
  const [validationLoading, setValidationLoading] = useState(false);
  const [validationDisclosure, setValidationDisclosure] = useState<string>('');

  // Initial Check: System Readiness
  useEffect(() => {
    fetch('/ready')
      .then(res => res.json())
      .then(data => setReadiness(data))
      .catch(() => setReadiness({ status: 'offline', device: 'unknown', cuda_available: false }));
  }, []);

  // Update duration and URL when analyze file changes
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
    if (refFile) {
      const url = URL.createObjectURL(refFile);
      setRefAudioUrl(url);
      return () => URL.revokeObjectURL(url);
    }
  }, [refFile]);

  useEffect(() => {
    if (candFile) {
      const url = URL.createObjectURL(candFile);
      setCandAudioUrl(url);
      return () => URL.revokeObjectURL(url);
    }
  }, [candFile]);

  useEffect(() => {
    if (arenaFile) {
      const url = URL.createObjectURL(arenaFile);
      setArenaAudioUrl(url);
      setArenaResult(null);
      setArenaError(null);
      return () => URL.revokeObjectURL(url);
    }
  }, [arenaFile]);

  // Load history when tab opens
  useEffect(() => {
    if (activeTab === 'history') {
      loadHistory();
    } else if (activeTab === 'validation') {
      loadValidation();
    }
  }, [activeTab]);

  const loadHistory = async () => {
    setHistoryLoading(true);
    try {
      const res = await fetch('/leaderboard');
      const data = await res.json();
      setHistoryRuns(data.leaderboard || []);
    } catch (err) {
      console.error(err);
    } finally {
      setHistoryLoading(false);
    }
  };

  const loadValidation = async () => {
    setValidationLoading(true);
    try {
      const res = await fetch('/validation');
      const data = await res.json();
      setValidationItems(data.items || []);
      setValidationDisclosure(data.disclosure || '');
    } catch (err) {
      console.error(err);
    } finally {
      setValidationLoading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!analyzeFile) return;
    setAnalyzing(true);
    setAnalyzeError(null);
    setAnalyzeResult(null);

    const formData = new FormData();
    formData.append('audio', analyzeFile);

    try {
      const res = await fetch('/score', { method: 'POST', body: formData });
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(errJson.detail || 'Analysis request failed.');
      }
      const data = await res.json();
      setAnalyzeResult(data);
      if (data.duration_s) setAudioDuration(data.duration_s);
    } catch (err: any) {
      setAnalyzeError(err.message || 'Scoring error');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleCompare = async () => {
    if (!refFile || !candFile) return;
    setComparing(true);
    setCompareError(null);
    setCompareResult(null);

    const formData = new FormData();
    formData.append('reference', refFile);
    formData.append('candidate', candFile);

    try {
      const res = await fetch('/compare', { method: 'POST', body: formData });
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(errJson.detail || 'Comparison failed.');
      }
      const data = await res.json();
      setCompareResult(data);
    } catch (err: any) {
      setCompareError(err.message || 'Comparison failed');
    } finally {
      setComparing(false);
    }
  };

  const handleArenaTransform = async () => {
    if (!arenaFile) return;
    setTransforming(true);
    setArenaError(null);
    setArenaResult(null);

    const formData = new FormData();
    formData.append('audio', arenaFile);
    formData.append('transform_type', transformType);
    formData.append('intensity', intensity.toString());

    try {
      const res = await fetch('/arena/transform', { method: 'POST', body: formData });
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(errJson.detail || 'Crash test transformation failed.');
      }
      const data = await res.json();
      setArenaResult(data);
    } catch (err: any) {
      setArenaError(err.message || 'Transformation failed');
    } finally {
      setTransforming(false);
    }
  };

  const seekAudio = (seconds: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = seconds;
      setCurrentTime(seconds);
      audioRef.current.play().catch(() => {});
    }
  };

  const exportEvidenceJSON = () => {
    if (!analyzeResult) return;
    const blob = new Blob([JSON.stringify(analyzeResult, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `speechproof_evidence_${analyzeResult.audio_sha256?.slice(0, 8) || 'export'}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportReportMarkdown = () => {
    if (!analyzeResult) return;
    const scores = analyzeResult.scores || {};
    const report = `# SpeechProof Research Analysis Report
**Recording:** ${analyzeFile?.name || 'Input WAV'}
**Duration:** ${analyzeResult.duration_s?.toFixed(2) || 'N/A'}s
**Audio SHA-256:** ${analyzeResult.audio_sha256 || 'N/A'}
**Overall Score:** ${analyzeResult.metadata?.overall_score ?? 'UNAVAILABLE'}
**Scorer Version:** ${analyzeResult.scorer_name} ${analyzeResult.scorer_version}

## Measured Dimension Rubrics
- **Pace:** ${scores.pace !== undefined ? scores.pace : 'UNAVAILABLE'}
- **Pausing:** ${scores.pausing !== undefined ? scores.pausing : 'UNAVAILABLE'}
- **Fluency:** ${scores.fluency !== undefined ? scores.fluency : 'UNAVAILABLE (Not Measured)'}
- **Pitch Variety:** ${scores.pitch !== undefined ? scores.pitch : 'UNAVAILABLE'}
- **Vocal Energy:** ${scores.energy !== undefined ? scores.energy : 'UNAVAILABLE'}

## Temporal Evidence Regions
${(analyzeResult.regions || []).map((r: any, idx: number) => `
### Event #${idx + 1}: ${r.type || 'Flaw'}
- **Interval:** ${(r.start_s ?? r.start ?? 0).toFixed(2)}s - ${(r.end_s ?? r.end ?? 0).toFixed(2)}s
- **Measured Value:** ${r.value ?? r.measured_value ?? 'N/A'} (Threshold: ${r.threshold ?? 'N/A'})
- **Context:** "...${(r.words_before || []).join(' ')} [FLAW] ${(r.words_after || []).join(' ')}..."
`).join('\n')}

---
*Generated by SpeechProof Research Analytics Engine*
`;
    const blob = new Blob([report], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `speechproof_report_${analyzeResult.audio_sha256?.slice(0, 8) || 'export'}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Helper to render delta
  const renderDelta = (delta: number | null | undefined) => {
    if (delta === null || delta === undefined) return <span className="delta-pill neutral">N/A</span>;
    if (delta > 0) return <span className="delta-pill positive">+{delta.toFixed(2)}</span>;
    if (delta < 0) return <span className="delta-pill negative">{delta.toFixed(2)}</span>;
    return <span className="delta-pill neutral">0.00</span>;
  };

  return (
    <div className="app-container">
      {/* Top Header */}
      <header className="app-header">
        <div className="brand-section">
          <div className="brand-logo">SP</div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="brand-title">SpeechProof</span>
              <span className="brand-tag">Auditable ASR & Rubric Platform</span>
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Deterministic Scoring • SHA-256 Grounded Evidence • Contrastive Crash Testing
            </div>
          </div>
        </div>

        <div className="header-status">
          <div className="status-pill">
            <span className={`status-dot ${readiness?.status === 'ready' ? '' : 'degraded'}`} />
            <span>
              {readiness?.status === 'ready'
                ? `Engine Ready • CUDA ${readiness.compute_type || 'float16'}`
                : `Engine: ${readiness?.status || 'Connecting...'}`}
            </span>
          </div>
        </div>
      </header>

      {/* Main Navigation Bar */}
      <nav className="nav-tabs">
        <button
          className={`nav-tab-btn ${activeTab === 'analyze' ? 'active' : ''}`}
          onClick={() => setActiveTab('analyze')}
        >
          1. Analyze
        </button>
        <button
          className={`nav-tab-btn ${activeTab === 'compare' ? 'active' : ''}`}
          onClick={() => setActiveTab('compare')}
        >
          2. Compare
        </button>
        <button
          className={`nav-tab-btn ${activeTab === 'arena' ? 'active' : ''}`}
          onClick={() => setActiveTab('arena')}
        >
          3. Crash Test Lab
        </button>
        <button
          className={`nav-tab-btn ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          4. Run History
        </button>
        <button
          className={`nav-tab-btn ${activeTab === 'validation' ? 'active' : ''}`}
          onClick={() => setActiveTab('validation')}
        >
          5. Validation Matrix
        </button>
      </nav>

      {/* ========================================================================= */}
      {/* TAB 1: ANALYZE */}
      {/* ========================================================================= */}
      {activeTab === 'analyze' && (
        <div>
          <div className="card">
            <div className="card-header">
              <div>
                <h2 className="card-title">Recording Analysis</h2>
                <p className="card-subtitle">
                  Upload an audio recording to extract faster-whisper ASR transcript, calculate deterministic rubric scores, and inspect temporal flaw intervals.
                </p>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '16px', alignItems: 'center' }}>
              <div>
                <label className="form-label">Speech Audio File (Mono 16 kHz WAV)</label>
                <input
                  type="file"
                  accept="audio/wav"
                  className="form-control"
                  onChange={e => setAnalyzeFile(e.target.files?.[0] || null)}
                />
              </div>
              <div style={{ paddingTop: '22px' }}>
                <button
                  className="btn btn-primary"
                  disabled={!analyzeFile || analyzing}
                  onClick={handleAnalyze}
                >
                  {analyzing ? (
                    <>
                      <span className="spinner" /> Scoring Audio...
                    </>
                  ) : (
                    'Run Speech Analysis'
                  )}
                </button>
              </div>
            </div>

            {analyzeAudioUrl && (
              <div style={{ marginTop: '16px' }}>
                <label className="form-label">Source Audio Playback</label>
                <audio
                  ref={audioRef}
                  src={analyzeAudioUrl}
                  controls
                  onTimeUpdate={e => setCurrentTime((e.target as HTMLAudioElement).currentTime)}
                  onLoadedMetadata={e => {
                    const d = (e.target as HTMLAudioElement).duration;
                    if (d && !isNaN(d) && isFinite(d)) setAudioDuration(d);
                  }}
                />
              </div>
            )}

            {analyzeError && (
              <div className="notice-banner warning" style={{ marginTop: '16px' }}>
                <strong>Analysis Failed:</strong> {analyzeError}
              </div>
            )}
          </div>

          {/* Analysis Results Display */}
          {analyzeResult && (
            <div>
              {/* Overall & Dimension Score Cards */}
              <div className="score-grid">
                <div className="score-card overall">
                  <span className="score-card-label">Overall Delivery</span>
                  <span className="score-card-value">
                    {analyzeResult.metadata?.overall_score !== null && analyzeResult.metadata?.overall_score !== undefined
                      ? analyzeResult.metadata.overall_score.toFixed(1)
                      : 'N/A'}
                  </span>
                  <span className="score-card-meta">
                    Duration: {analyzeResult.duration_s?.toFixed(2)}s • SHA-256: {analyzeResult.audio_sha256?.slice(0, 8)}...
                  </span>
                </div>

                <div className="score-card">
                  <span className="score-card-label">Pace</span>
                  <span className="score-card-value">
                    {analyzeResult.scores?.pace !== undefined ? analyzeResult.scores.pace.toFixed(1) : 'UNAVAILABLE'}
                  </span>
                  <span className="score-card-meta">Target: 100 - 180 WPM</span>
                </div>

                <div className="score-card">
                  <span className="score-card-label">Pausing</span>
                  <span className="score-card-value">
                    {analyzeResult.scores?.pausing !== undefined ? analyzeResult.scores.pausing.toFixed(1) : 'UNAVAILABLE'}
                  </span>
                  <span className="score-card-meta">Target: &le; 20% pause ratio</span>
                </div>

                <div className="score-card">
                  <span className="score-card-label">Fluency</span>
                  <span className="score-card-value unavailable">
                    {analyzeResult.scores?.fluency !== undefined ? analyzeResult.scores.fluency.toFixed(1) : 'UNAVAILABLE'}
                  </span>
                  <span className="score-card-meta">Filler model uncalibrated</span>
                </div>

                <div className="score-card">
                  <span className="score-card-label">Pitch Variety</span>
                  <span className="score-card-value">
                    {analyzeResult.scores?.pitch !== undefined ? analyzeResult.scores.pitch.toFixed(1) : 'UNAVAILABLE'}
                  </span>
                  <span className="score-card-meta">Target: &ge; 1.0 semitones std</span>
                </div>

                <div className="score-card">
                  <span className="score-card-label">Vocal Energy</span>
                  <span className="score-card-value">
                    {analyzeResult.scores?.energy !== undefined ? analyzeResult.scores.energy.toFixed(1) : 'UNAVAILABLE'}
                  </span>
                  <span className="score-card-meta">Target: &ge; 3.0 dB RMS std</span>
                </div>
              </div>

              {/* Quality Flags Notice */}
              {analyzeResult.quality_flags && analyzeResult.quality_flags.length > 0 && (
                <div className="notice-banner">
                  <strong>Pipeline Flags:</strong> {analyzeResult.quality_flags.join(', ')}
                </div>
              )}

              {/* Waveform Visualization Card */}
              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">Temporal Waveform & Evidence Anchors</h3>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button className="btn btn-secondary" onClick={exportEvidenceJSON}>
                      Export Evidence JSON
                    </button>
                    <button className="btn btn-secondary" onClick={exportReportMarkdown}>
                      Download Report (MD)
                    </button>
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

                {/* Selected Region Detailed Inspector */}
                {selectedRegionIdx !== null && analyzeResult.regions?.[selectedRegionIdx] && (
                  <div style={{ background: 'var(--bg-surface)', padding: '16px', borderRadius: '8px', marginTop: '16px', border: '1px solid var(--accent-cyan)' }}>
                    {(() => {
                      const reg: EvidenceRegion = analyzeResult.regions[selectedRegionIdx];
                      const start = reg.start_s ?? reg.start ?? 0;
                      const end = reg.end_s ?? reg.end ?? start;
                      const val = reg.value ?? reg.measured_value ?? 'N/A';
                      const thresh = reg.threshold ?? 0.4;
                      return (
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '16px', alignItems: 'center' }}>
                          <div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                              <span className="badge badge-inconclusive">{reg.type || 'flaw'}</span>
                              <strong style={{ fontSize: '15px' }}>
                                Timestamp: {start.toFixed(2)}s - {end.toFixed(2)}s (Duration: {(end - start).toFixed(2)}s)
                              </strong>
                            </div>
                            <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                              Measured Gap: <strong>{val}s</strong> (Threshold: {thresh}s)
                            </div>
                            {reg.words_before && reg.words_after && (
                              <div style={{ fontSize: '13px', marginTop: '6px', color: '#cbd5e1' }}>
                                Context: "<em>{(reg.words_before || []).join(' ')}</em>{' '}
                                <span style={{ color: '#ef4444', fontWeight: 'bold' }}>[FLAW]</span>{' '}
                                <em>{(reg.words_after || []).join(' ')}</em>"
                              </div>
                            )}
                          </div>
                          <div>
                            <button className="btn btn-secondary" onClick={() => seekAudio(start)}>
                              Play Interval
                            </button>
                          </div>
                        </div>
                      );
                    })()}
                  </div>
                )}

                {/* Evidence Region List Table */}
                <div style={{ marginTop: '20px' }}>
                  <h4 style={{ fontSize: '14px', marginBottom: '10px', color: 'var(--text-secondary)' }}>
                    Detected Flaw Intervals ({analyzeResult.regions?.length || 0})
                  </h4>
                  {analyzeResult.regions && analyzeResult.regions.length > 0 ? (
                    <div className="table-responsive">
                      <table className="regions-table">
                        <thead>
                          <tr>
                            <th>Type</th>
                            <th>Time Window</th>
                            <th>Duration</th>
                            <th>Measured Value</th>
                            <th>Threshold</th>
                            <th>Surrounding Words</th>
                            <th>Action</th>
                          </tr>
                        </thead>
                        <tbody>
                          {analyzeResult.regions.map((reg: any, idx: number) => {
                            const start = reg.start_s ?? reg.start ?? 0;
                            const end = reg.end_s ?? reg.end ?? start;
                            return (
                              <tr
                                key={idx}
                                className={selectedRegionIdx === idx ? 'selected' : ''}
                                onClick={() => setSelectedRegionIdx(idx)}
                              >
                                <td><span className="badge badge-inconclusive">{reg.type || 'flaw'}</span></td>
                                <td style={{ fontFamily: 'var(--font-mono)' }}>{start.toFixed(2)}s - {end.toFixed(2)}s</td>
                                <td>{(end - start).toFixed(2)}s</td>
                                <td>{reg.value ?? reg.measured_value ?? 'N/A'}</td>
                                <td>{reg.threshold ?? 'N/A'}</td>
                                <td style={{ maxWidth: '280px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                  {(reg.words_before || []).join(' ')} ... {(reg.words_after || []).join(' ')}
                                </td>
                                <td>
                                  <button
                                    className="btn btn-secondary"
                                    style={{ padding: '4px 10px', fontSize: '11px' }}
                                    onClick={e => {
                                      e.stopPropagation();
                                      setSelectedRegionIdx(idx);
                                      seekAudio(start);
                                    }}
                                  >
                                    Seek
                                  </button>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
                      No threshold-exceeding flaws detected in this recording.
                    </p>
                  )}
                </div>
              </div>

              {/* Technical Details Expandable Card */}
              <div className="card">
                <div
                  className="flex-between"
                  style={{ cursor: 'pointer' }}
                  onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
                >
                  <h4 style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
                    Advanced Evidence Integrity & Model Metadata
                  </h4>
                  <span style={{ fontSize: '12px', color: 'var(--accent-cyan)' }}>
                    {showTechnicalDetails ? 'Collapse' : 'Expand'}
                  </span>
                </div>

                {showTechnicalDetails && (
                  <div style={{ marginTop: '16px' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '12px', marginBottom: '16px', fontSize: '13px' }}>
                      <div>Audio SHA-256: <code style={{ fontSize: '11px' }}>{analyzeResult.audio_sha256}</code></div>
                      <div>Evidence SHA-256: <code style={{ fontSize: '11px' }}>{analyzeResult.metadata?.evidence_sha256}</code></div>
                      <div>Run ID: <code>{analyzeResult.metadata?.run_id || 'N/A'}</code></div>
                      <div>Rubric: <code>{analyzeResult.metadata?.rubric_version}</code></div>
                    </div>
                    <pre className="code-block">{JSON.stringify(analyzeResult, null, 2)}</pre>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: CONTRASTIVE COMPARE */}
      {/* ========================================================================= */}
      {activeTab === 'compare' && (
        <div>
          <div className="card">
            <div className="card-header">
              <div>
                <h2 className="card-title">Contrastive Candidate vs Reference Comparison</h2>
                <p className="card-subtitle">
                  Compare two takes of the same speech to measure objective parameter changes (Delta = Candidate - Reference).
                </p>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
              <div>
                <label className="form-label">Reference Recording (WAV)</label>
                <input
                  type="file"
                  accept="audio/wav"
                  className="form-control"
                  onChange={e => setRefFile(e.target.files?.[0] || null)}
                />
                {refAudioUrl && (
                  <audio src={refAudioUrl} controls style={{ marginTop: '8px' }} />
                )}
              </div>

              <div>
                <label className="form-label">Candidate Delivery (WAV)</label>
                <input
                  type="file"
                  accept="audio/wav"
                  className="form-control"
                  onChange={e => setCandFile(e.target.files?.[0] || null)}
                />
                {candAudioUrl && (
                  <audio src={candAudioUrl} controls style={{ marginTop: '8px' }} />
                )}
              </div>
            </div>

            <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end' }}>
              <button
                className="btn btn-primary"
                disabled={!refFile || !candFile || comparing}
                onClick={handleCompare}
              >
                {comparing ? <><span className="spinner" /> Scoring Deliveries...</> : 'Run Contrastive Comparison'}
              </button>
            </div>

            {compareError && (
              <div className="notice-banner warning" style={{ marginTop: '16px' }}>
                <strong>Comparison Error:</strong> {compareError}
              </div>
            )}
          </div>

          {compareResult && (
            <div>
              <div className="notice-banner">
                <strong>Scientific Methodology Notice:</strong> Contrastive analysis quantifies rubric deltas across two files. A positive delta indicates higher candidate scoring. It does not imply clinical superiority or word-level alignment across takes.
              </div>

              <div className="card">
                <h3 className="card-title" style={{ marginBottom: '16px' }}>Score Deltas Breakdown</h3>
                <div className="table-responsive">
                  <table className="regions-table">
                    <thead>
                      <tr>
                        <th>Rubric Dimension</th>
                        <th>Reference Score</th>
                        <th>Candidate Score</th>
                        <th>Delta (Cand - Ref)</th>
                        <th>Interpretation</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td><strong>Overall Score</strong></td>
                        <td style={{ fontWeight: 600 }}>{compareResult.reference?.metadata?.overall_score ?? 'N/A'}</td>
                        <td style={{ fontWeight: 600 }}>{compareResult.candidate?.metadata?.overall_score ?? 'N/A'}</td>
                        <td>{renderDelta(compareResult.overall_delta)}</td>
                        <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                          {compareResult.overall_delta > 0 ? 'Candidate overall higher' : compareResult.overall_delta < 0 ? 'Candidate overall lower' : 'Identical score'}
                        </td>
                      </tr>
                      {['pace', 'pausing', 'pitch', 'energy'].map(dim => {
                        const refVal = compareResult.reference?.scores?.[dim];
                        const candVal = compareResult.candidate?.scores?.[dim];
                        const diff = compareResult.differences?.[dim];
                        return (
                          <tr key={dim}>
                            <td style={{ textTransform: 'capitalize' }}>{dim}</td>
                            <td>{refVal !== undefined ? refVal.toFixed(1) : 'UNAVAILABLE'}</td>
                            <td>{candVal !== undefined ? candVal.toFixed(1) : 'UNAVAILABLE'}</td>
                            <td>{renderDelta(diff)}</td>
                            <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                              {diff > 0 ? 'Higher score' : diff < 0 ? 'Lower score' : 'Invariant'}
                            </td>
                          </tr>
                        );
                      })}
                      <tr>
                        <td>Fluency</td>
                        <td style={{ color: 'var(--text-muted)' }}>UNAVAILABLE</td>
                        <td style={{ color: 'var(--text-muted)' }}>UNAVAILABLE</td>
                        <td><span className="delta-pill neutral">N/A</span></td>
                        <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Uncalibrated in v0.1 rubric</td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                <div style={{ marginTop: '20px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', fontSize: '12px', color: 'var(--text-muted)' }}>
                  <div>
                    Reference Hash: <code>{compareResult.reference_sha256?.slice(0, 16)}...</code><br />
                    Duration: {compareResult.reference_duration_s?.toFixed(2)}s
                  </div>
                  <div>
                    Candidate Hash: <code>{compareResult.candidate_sha256?.slice(0, 16)}...</code><br />
                    Duration: {compareResult.candidate_duration_s?.toFixed(2)}s
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: CRASH TEST LAB */}
      {/* ========================================================================= */}
      {activeTab === 'arena' && (
        <div>
          <div className="card">
            <div className="card-header">
              <div>
                <h2 className="card-title">Crash Test Lab: Controlled Flaw Injection</h2>
                <p className="card-subtitle">
                  Apply deterministic audio transformations (Pause insertion, Pace time-stretch, Volume gain) to audit the rubric response.
                </p>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              <div>
                <label className="form-label">Base Recording (Mono 16 kHz WAV)</label>
                <input
                  type="file"
                  accept="audio/wav"
                  className="form-control"
                  onChange={e => setArenaFile(e.target.files?.[0] || null)}
                />
                {arenaAudioUrl && (
                  <div style={{ marginTop: '10px' }}>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Original Audio:</span>
                    <audio src={arenaAudioUrl} controls />
                  </div>
                )}
              </div>

              <div>
                <div className="form-group">
                  <label className="form-label">Transformation Type</label>
                  <select
                    className="form-control"
                    value={transformType}
                    onChange={e => {
                      const t = e.target.value as 'pause' | 'pace' | 'volume';
                      setTransformType(t);
                      if (t === 'pause') setIntensity(2.0);
                      if (t === 'pace') setIntensity(1.2);
                      if (t === 'volume') setIntensity(-6.0);
                    }}
                  >
                    <option value="pause">Pause Insertion (Target: Pausing score)</option>
                    <option value="pace">Pace Modification (Target: Pace score)</option>
                    <option value="volume">Volume Modification (Target: Energy score)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">
                    {transformType === 'pause' && 'Pause Duration (Seconds) [0.5s - 5.0s]'}
                    {transformType === 'pace' && 'Speed Rate Multiplier (x) [0.5x - 1.5x]'}
                    {transformType === 'volume' && 'Gain Adjustment (dB) [-12.0 dB - +12.0 dB]'}
                  </label>
                  <input
                    type="number"
                    className="form-control"
                    value={intensity}
                    step={transformType === 'pace' ? 0.05 : transformType === 'pause' ? 0.2 : 1.0}
                    min={transformType === 'volume' ? -12.0 : 0.5}
                    max={transformType === 'volume' ? 12.0 : transformType === 'pace' ? 1.5 : 5.0}
                    onChange={e => setIntensity(parseFloat(e.target.value) || 0)}
                  />
                  <div className="form-helper">
                    {transformType === 'pause' && 'Splits audio at midpoint and inserts exact silence interval.'}
                    {transformType === 'pace' && 'Time-stretches audio via phase vocoder while preserving pitch.'}
                    {transformType === 'volume' && 'Applies linear gain scaling and flags hard clipping.'}
                  </div>
                </div>

                <button
                  className="btn btn-primary"
                  style={{ width: '100%', marginTop: '8px' }}
                  disabled={!arenaFile || transforming}
                  onClick={handleArenaTransform}
                >
                  {transforming ? <><span className="spinner" /> Transforming & Scoring...</> : 'Execute Crash Test'}
                </button>
              </div>
            </div>

            {arenaError && (
              <div className="notice-banner warning" style={{ marginTop: '16px' }}>
                <strong>Crash Test Failure:</strong> {arenaError}
              </div>
            )}
          </div>

          {/* Crash Test Results */}
          {arenaResult && (
            <div>
              {/* Outcome Verification Badges */}
              <div className="card">
                <h3 className="card-title" style={{ marginBottom: '14px' }}>Automated Verification Outcome</h3>
                <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                  <div className="badge badge-met">Transformation: Completed</div>
                  <div className="badge badge-met">Scoring: Completed</div>
                  <div className={`badge ${arenaResult.target_responded ? 'badge-met' : 'badge-inconclusive'}`}>
                    Target ({arenaResult.intended_target}): {arenaResult.target_responded ? 'Responded to Dose' : 'Unchanged'}
                  </div>
                  <div className={`badge ${arenaResult.unrelated_changed ? 'badge-inconclusive' : 'badge-met'}`}>
                    Cross-Talk: {arenaResult.unrelated_changed ? 'Off-Target Affected' : 'Isolated'}
                  </div>
                  <div className={`badge ${arenaResult.clipping_occurred ? 'badge-failed' : 'badge-met'}`}>
                    Clipping: {arenaResult.clipping_occurred ? 'Clipping Detected' : 'Clean Signal'}
                  </div>
                </div>

                {arenaResult.warnings && arenaResult.warnings.length > 0 && (
                  <div className="notice-banner warning" style={{ marginTop: '16px' }}>
                    {arenaResult.warnings.map((w: string, i: number) => <div key={i}>{w}</div>)}
                  </div>
                )}

                {/* Transformed Audio Player */}
                {arenaResult.audio_data_url && (
                  <div style={{ marginTop: '16px' }}>
                    <label className="form-label">Transformed Output Audio (Generated in Sandbox)</label>
                    <audio src={arenaResult.audio_data_url} controls />
                  </div>
                )}
              </div>

              {/* Score Response Table */}
              <div className="card">
                <h3 className="card-title" style={{ marginBottom: '14px' }}>Original vs Transformed Rubric Scores</h3>
                <div className="table-responsive">
                  <table className="regions-table">
                    <thead>
                      <tr>
                        <th>Dimension</th>
                        <th>Original Score</th>
                        <th>Transformed Score</th>
                        <th>Score Delta</th>
                        <th>Target Role</th>
                      </tr>
                    </thead>
                    <tbody>
                      {['pace', 'pausing', 'pitch', 'energy'].map(dim => {
                        const origVal = arenaResult.original?.scores?.[dim];
                        const transVal = arenaResult.transformed?.scores?.[dim];
                        const delta = arenaResult.differences?.[dim];
                        const isTarget = dim === arenaResult.intended_target;
                        return (
                          <tr
                            key={dim}
                            style={{ background: isTarget ? 'rgba(56, 189, 248, 0.08)' : undefined }}
                          >
                            <td style={{ textTransform: 'capitalize', fontWeight: isTarget ? 700 : 400 }}>
                              {dim} {isTarget && '🎯'}
                            </td>
                            <td>{origVal !== undefined ? origVal.toFixed(1) : 'UNAVAILABLE'}</td>
                            <td>{transVal !== undefined ? transVal.toFixed(1) : 'UNAVAILABLE'}</td>
                            <td>{renderDelta(delta)}</td>
                            <td>
                              {isTarget ? (
                                <span className="badge badge-pilot">Intended Target</span>
                              ) : (
                                <span style={{ color: 'var(--text-muted)', fontSize: '11px' }}>Off-target</span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                      <tr>
                        <td><strong>Overall Score</strong></td>
                        <td style={{ fontWeight: 600 }}>{arenaResult.original?.metadata?.overall_score ?? 'N/A'}</td>
                        <td style={{ fontWeight: 600 }}>{arenaResult.transformed?.metadata?.overall_score ?? 'N/A'}</td>
                        <td>{renderDelta(arenaResult.overall_delta)}</td>
                        <td><span style={{ color: 'var(--text-muted)', fontSize: '11px' }}>Composite</span></td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                <div style={{ marginTop: '16px', fontSize: '12px', color: 'var(--text-muted)' }}>
                  Original Audio SHA-256: <code>{arenaResult.original_sha256}</code><br />
                  Transformed Audio SHA-256: <code>{arenaResult.transformed_sha256}</code>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 4: RUN HISTORY */}
      {/* ========================================================================= */}
      {activeTab === 'history' && (
        <div>
          <div className="card">
            <div className="card-header">
              <div>
                <h2 className="card-title">Run History & Audit Ledger</h2>
                <p className="card-subtitle">
                  Inspect persistent scoring runs recorded in SQLite (db/ledger.sqlite). All filepaths sanitized for research disclosure.
                </p>
              </div>
              <div>
                <button className="btn btn-secondary" onClick={loadHistory} disabled={historyLoading}>
                  {historyLoading ? <span className="spinner" /> : 'Refresh Ledger'}
                </button>
              </div>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <input
                type="text"
                placeholder="Filter by recording name or SHA-256 prefix..."
                className="form-control"
                value={historySearch}
                onChange={e => setHistorySearch(e.target.value)}
              />
            </div>

            <div className="table-responsive">
              <table className="regions-table">
                <thead>
                  <tr>
                    <th>Run ID</th>
                    <th>Recording</th>
                    <th>Overall Score</th>
                    <th>Dimensions Measured</th>
                    <th>Duration</th>
                    <th>SHA-256</th>
                    <th>Recorded At</th>
                  </tr>
                </thead>
                <tbody>
                  {historyRuns
                    .filter(r =>
                      r.recording_name.toLowerCase().includes(historySearch.toLowerCase()) ||
                      r.sha256_prefix.toLowerCase().includes(historySearch.toLowerCase())
                    )
                    .map(run => (
                      <tr
                        key={run.run_id}
                        onClick={() => setSelectedHistoryRun(run)}
                      >
                        <td style={{ fontFamily: 'var(--font-mono)' }}>#{run.run_id}</td>
                        <td><strong>{run.recording_name}</strong></td>
                        <td>
                          {run.overall_score !== null ? (
                            <span className="badge badge-met" style={{ fontSize: '12px' }}>
                              {run.overall_score.toFixed(1)}
                            </span>
                          ) : (
                            <span className="badge badge-notrun">N/A</span>
                          )}
                        </td>
                        <td style={{ fontSize: '12px' }}>
                          {Object.keys(run.scores || {}).length > 0 ? (
                            Object.entries(run.scores).map(([k, v]) => (
                              <span key={k} style={{ marginRight: '8px', color: 'var(--text-secondary)' }}>
                                {k}: {v}
                              </span>
                            ))
                          ) : (
                            <span style={{ color: 'var(--text-muted)' }}>None stored</span>
                          )}
                        </td>
                        <td>{run.duration_s ? `${run.duration_s.toFixed(1)}s` : '—'}</td>
                        <td style={{ fontFamily: 'var(--font-mono)' }}>{run.sha256_prefix}...</td>
                        <td style={{ color: 'var(--text-muted)', fontSize: '12px' }}>{run.created_at}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>

            {selectedHistoryRun && (
              <div style={{ marginTop: '24px', padding: '16px', background: 'var(--bg-surface)', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <div className="flex-between" style={{ marginBottom: '10px' }}>
                  <h4>Run #{selectedHistoryRun.run_id} Inspection</h4>
                  <button className="btn btn-secondary" style={{ padding: '2px 8px', fontSize: '12px' }} onClick={() => setSelectedHistoryRun(null)}>
                    Close
                  </button>
                </div>
                <div style={{ fontSize: '13px', lineHeight: 1.6 }}>
                  <div><strong>File:</strong> {selectedHistoryRun.recording_name}</div>
                  <div><strong>Full SHA-256:</strong> <code>{selectedHistoryRun.sha256}</code></div>
                  <div><strong>Scorer / Rubric:</strong> {selectedHistoryRun.scorer_name} ({selectedHistoryRun.rubric_version})</div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 5: VALIDATION MATRIX */}
      {/* ========================================================================= */}
      {activeTab === 'validation' && (
        <div>
          <div className="card">
            <div className="card-header">
              <div>
                <h2 className="card-title">Empirical Validation Battery (T1-T9 & A1-A5)</h2>
                <p className="card-subtitle">
                  Live verification results read directly from evaluation artifacts. Strictly distinguishing MET, PILOT, INCONCLUSIVE, and NOT_RUN.
                </p>
              </div>
              <button className="btn btn-secondary" onClick={loadValidation} disabled={validationLoading}>
                {validationLoading ? <span className="spinner" /> : 'Reload Artifacts'}
              </button>
            </div>

            {validationDisclosure && (
              <div className="notice-banner warning">
                {validationDisclosure}
              </div>
            )}

            <div className="validation-grid">
              {validationItems.map(item => {
                let badgeClass = 'badge-inconclusive';
                if (item.status === 'MET') badgeClass = 'badge-met';
                else if (item.status === 'PILOT') badgeClass = 'badge-pilot';
                else if (item.status === 'NOT_RUN') badgeClass = 'badge-notrun';
                else if (item.status === 'FAILED') badgeClass = 'badge-failed';

                return (
                  <div key={item.id} className="validation-card">
                    <div className="validation-card-header">
                      <span className="validation-card-title">{item.name}</span>
                      <span className={`badge ${badgeClass}`}>{item.status}</span>
                    </div>

                    <div style={{ flex: 1 }}>
                      {item.metric && (
                        <div className="validation-metric-row">
                          <span className="validation-metric-label">Metric</span>
                          <span className="validation-metric-val">{item.metric}</span>
                        </div>
                      )}

                      {item.value !== null && item.value !== undefined && (
                        <div className="validation-metric-row">
                          <span className="validation-metric-label">Observed Value</span>
                          <span className="validation-metric-val">{String(item.value)}</span>
                        </div>
                      )}

                      {item.target && (
                        <div className="validation-metric-row">
                          <span className="validation-metric-label">Target Criteria</span>
                          <span className="validation-metric-val" style={{ fontSize: '11px' }}>{item.target}</span>
                        </div>
                      )}

                      <div style={{ marginTop: '10px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                        {item.reason}
                      </div>

                      {item.limitations && item.limitations.length > 0 && (
                        <div style={{ marginTop: '8px', fontSize: '11px', color: '#f59e0b' }}>
                          <strong>Limitations:</strong> {item.limitations.join('; ')}
                        </div>
                      )}
                    </div>

                    {item.raw_artifact && (
                      <div style={{ marginTop: '12px', fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        Source: {item.raw_artifact}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
