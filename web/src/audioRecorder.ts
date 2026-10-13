/**
 * SpeechProof In-Browser Audio Normalizer & Recorder
 * Converts any browser-supported recording/upload (mic stream, M4A, AAC, WebM, MP3, OGG)
 * directly into 16 kHz mono 16-bit PCM WAV for immediate deterministic analysis.
 */

export async function convertAudioBufferToWavFile(
  audioBuffer: AudioBuffer,
  filename = 'recording_16k.wav'
): Promise<File> {
  // Resample to 16 kHz mono
  const targetSampleRate = 16000;
  const targetLength = Math.max(1, Math.round(audioBuffer.duration * targetSampleRate));
  const offlineCtx = new (window.OfflineAudioContext || (window as any).webkitOfflineAudioContext)(
    1,
    targetLength,
    targetSampleRate
  );

  const source = offlineCtx.createBufferSource();
  source.buffer = audioBuffer;
  source.connect(offlineCtx.destination);
  source.start(0);

  const renderedBuffer = await offlineCtx.startRendering();
  const channelData = renderedBuffer.getChannelData(0);

  // Encode 16-bit PCM WAV header + samples
  const wavBuffer = new ArrayBuffer(44 + channelData.length * 2);
  const view = new DataView(wavBuffer);

  const writeString = (offset: number, str: string) => {
    for (let i = 0; i < str.length; i++) {
      view.setUint8(offset + i, str.charCodeAt(i));
    }
  };

  writeString(0, 'RIFF');
  view.setUint32(4, 36 + channelData.length * 2, true);
  writeString(8, 'WAVE');
  writeString(12, 'fmt ');
  view.setUint32(16, 16, true); // PCM subchunk size
  view.setUint16(20, 1, true); // Format 1 = PCM
  view.setUint16(22, 1, true); // 1 channel (mono)
  view.setUint32(24, targetSampleRate, true);
  view.setUint32(28, targetSampleRate * 2, true); // byte rate
  view.setUint16(32, 2, true); // block align
  view.setUint16(34, 16, true); // bits per sample
  writeString(36, 'data');
  view.setUint32(40, channelData.length * 2, true);

  let offset = 44;
  for (let i = 0; i < channelData.length; i++, offset += 2) {
    const s = Math.max(-1, Math.min(1, channelData[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }

  return new File([wavBuffer], filename, { type: 'audio/wav' });
}

export async function convertBlobToWavFile(blob: Blob, filename = 'speech_recording.wav'): Promise<File> {
  try {
    const arrayBuffer = await blob.arrayBuffer();
    const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
    const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);
    return await convertAudioBufferToWavFile(audioBuffer, filename);
  } catch (err) {
    // If Web Audio API cannot decode (e.g., rare container), return blob as raw File for backend PyAV processing
    const mime = blob.type || 'audio/webm';
    return new File([blob], filename, { type: mime });
  }
}

export interface LiveVoiceRecorder {
  stop: () => Promise<File>;
  cancel: () => void;
}

export async function startVoiceRecording(): Promise<LiveVoiceRecorder> {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    throw new Error('Microphone audio recording is not supported in this browser environment.');
  }

  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
    ? 'audio/webm;codecs=opus'
    : MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')
    ? 'audio/ogg;codecs=opus'
    : '';

  const mediaRecorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
  const chunks: Blob[] = [];

  mediaRecorder.ondataavailable = (e) => {
    if (e.data && e.data.size > 0) {
      chunks.push(e.data);
    }
  };

  mediaRecorder.start(250);

  return {
    stop: async () => {
      return new Promise<File>((resolve, reject) => {
        mediaRecorder.onstop = async () => {
          stream.getTracks().forEach((track) => track.stop());
          try {
            const rawBlob = new Blob(chunks, { type: mimeType || 'audio/webm' });
            const wavFile = await convertBlobToWavFile(rawBlob, `mic_recording_${Date.now()}.wav`);
            resolve(wavFile);
          } catch (e) {
            reject(e);
          }
        };
        mediaRecorder.stop();
      });
    },
    cancel: () => {
      try {
        stream.getTracks().forEach((track) => track.stop());
        if (mediaRecorder.state !== 'inactive') {
          mediaRecorder.stop();
        }
      } catch (err) {
        // no-op
      }
    }
  };
}
