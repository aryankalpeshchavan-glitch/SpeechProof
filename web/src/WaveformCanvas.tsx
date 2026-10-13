import { useEffect, useRef, useState, type FC, type MouseEvent } from 'react';

export interface EvidenceRegion {
  type: string;
  start_s?: number;
  end_s?: number;
  start?: number;
  end?: number;
  value?: number;
  measured_value?: number;
  threshold?: number;
  dimension?: string;
  measure?: string;
  words_before?: any;
  words_after?: any;
}

interface WaveformCanvasProps {
  audioFile?: File | null;
  audioUrl?: string | null;
  regions: EvidenceRegion[];
  selectedRegionIndex: number | null;
  onSelectRegion: (index: number) => void;
  currentTime: number;
  duration: number;
  onSeek: (time: number) => void;
}

export const WaveformCanvas: FC<WaveformCanvasProps> = ({
  audioFile,
  audioUrl,
  regions,
  selectedRegionIndex,
  onSelectRegion,
  currentTime,
  duration,
  onSeek
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [peaks, setPeaks] = useState<number[]>([]);
  const [loadingAudio, setLoadingAudio] = useState(false);

  // Extract audio peaks using Web Audio API
  useEffect(() => {
    let isMounted = true;
    if (!audioFile && !audioUrl) {
      setPeaks([]);
      return;
    }

    const loadAndDecode = async () => {
      setLoadingAudio(true);
      try {
        let arrayBuffer: ArrayBuffer;
        if (audioFile) {
          arrayBuffer = await audioFile.arrayBuffer();
        } else if (audioUrl) {
          const resp = await fetch(audioUrl);
          arrayBuffer = await resp.arrayBuffer();
        } else {
          return;
        }

        const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
        const decoded = await audioCtx.decodeAudioData(arrayBuffer);
        const channelData = decoded.getChannelData(0);

        const sampleCount = 600;
        const blockSize = Math.floor(channelData.length / sampleCount);
        const extractedPeaks: number[] = [];

        for (let i = 0; i < sampleCount; i++) {
          let maxVal = 0;
          const start = i * blockSize;
          const end = Math.min(start + blockSize, channelData.length);
          for (let j = start; j < end; j++) {
            const abs = Math.abs(channelData[j]);
            if (abs > maxVal) maxVal = abs;
          }
          extractedPeaks.push(maxVal);
        }

        audioCtx.close();
        if (isMounted) setPeaks(extractedPeaks);
      } catch (err) {
        console.warn("Waveform decoding fallback: ", err);
        // Synthetic fallback envelope
        const fallback = Array.from({ length: 400 }, (_, i) => 0.2 + 0.6 * Math.sin(i / 15) ** 2);
        if (isMounted) setPeaks(fallback);
      } finally {
        if (isMounted) setLoadingAudio(false);
      }
    };

    loadAndDecode();
    return () => { isMounted = false; };
  }, [audioFile, audioUrl]);

  // Draw waveform and overlays
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    ctx.clearRect(0, 0, width, height);

    // Background
    ctx.fillStyle = '#06090e';
    ctx.fillRect(0, 0, width, height);

    // Centerline
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, height / 2);
    ctx.lineTo(width, height / 2);
    ctx.stroke();

    const effectiveDuration = duration > 0 ? duration : 1.0;

    // Draw evidence region overlays
    regions.forEach((reg, idx) => {
      const regStart = reg.start_s ?? reg.start ?? 0;
      const regEnd = reg.end_s ?? reg.end ?? regStart;
      if (regEnd <= regStart) return;

      const x1 = Math.max(0, (regStart / effectiveDuration) * width);
      const x2 = Math.min(width, (regEnd / effectiveDuration) * width);
      const regWidth = Math.max(x2 - x1, 4);

      const isSelected = selectedRegionIndex === idx;

      ctx.fillStyle = isSelected ? 'rgba(239, 68, 68, 0.35)' : 'rgba(245, 158, 11, 0.22)';
      ctx.fillRect(x1, 0, regWidth, height);

      ctx.strokeStyle = isSelected ? '#ef4444' : '#f59e0b';
      ctx.lineWidth = isSelected ? 2 : 1;
      ctx.strokeRect(x1, 0, regWidth, height);

      // Label
      ctx.fillStyle = isSelected ? '#ffffff' : '#fde68a';
      ctx.font = '10px ui-monospace, monospace';
      ctx.fillText(reg.type || 'flaw', x1 + 4, 14);
    });

    // Draw waveform bars
    if (peaks.length > 0) {
      const barWidth = width / peaks.length;
      peaks.forEach((peak, i) => {
        const x = i * barWidth;
        const barHeight = Math.max(peak * (height * 0.85), 2);
        const y = (height - barHeight) / 2;

        const timeAtX = (i / peaks.length) * effectiveDuration;
        const isPlayed = timeAtX <= currentTime;

        ctx.fillStyle = isPlayed ? '#38bdf8' : '#334155';
        ctx.fillRect(x, y, Math.max(barWidth - 0.5, 1), barHeight);
      });
    }

    // Draw playback playhead
    if (duration > 0 && currentTime >= 0) {
      const playheadX = Math.min(width, (currentTime / effectiveDuration) * width);
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      ctx.shadowColor = '#38bdf8';
      ctx.shadowBlur = 6;
      ctx.beginPath();
      ctx.moveTo(playheadX, 0);
      ctx.lineTo(playheadX, height);
      ctx.stroke();
      ctx.shadowBlur = 0; // reset
    }
  }, [peaks, regions, selectedRegionIndex, currentTime, duration]);

  const handleCanvasClick = (e: MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas || duration <= 0) return;

    const rect = canvas.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickedRatio = Math.max(0, Math.min(1, clickX / rect.width));
    const seekTime = clickedRatio * duration;

    // Check if clicked inside an evidence region
    let matchedIndex = -1;
    regions.forEach((reg, i) => {
      const s = reg.start_s ?? reg.start ?? 0;
      const end = reg.end_s ?? reg.end ?? s;
      if (seekTime >= s && seekTime <= end) {
        matchedIndex = i;
      }
    });

    if (matchedIndex !== -1) {
      onSelectRegion(matchedIndex);
    }
    onSeek(seekTime);
  };

  return (
    <div className="waveform-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
        <span style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8' }}>
          TEMPORAL EVIDENCE WAVEFORM {loadingAudio && "(Generating Amplitude Envelope...)"}
        </span>
        <span style={{ fontSize: '11px', color: '#64748b' }}>
          Click waveform or region marker to seek
        </span>
      </div>
      <canvas
        ref={canvasRef}
        width={900}
        height={130}
        className="waveform-canvas"
        onClick={handleCanvasClick}
      />
      <div className="waveform-timeline-labels">
        <span>0.00s</span>
        <span>{currentTime.toFixed(2)}s / {duration.toFixed(2)}s</span>
        <span>{duration.toFixed(2)}s</span>
      </div>
    </div>
  );
};
