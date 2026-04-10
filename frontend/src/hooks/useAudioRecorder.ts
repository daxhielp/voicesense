import { useRef, useCallback } from 'react'

export interface AudioRecorderControls {
  startRecording: () => Promise<void>
  stopRecording: () => Promise<Blob>
  analyserNode: React.MutableRefObject<AnalyserNode | null>
}

/**
 * Abstracts MediaRecorder + Web Audio API.
 * The AnalyserNode ref is populated during recording so WaveformVisualizer
 * can read real-time time-domain data at 60fps via requestAnimationFrame.
 */
export function useAudioRecorder(): AudioRecorderControls {
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef        = useRef<Blob[]>([])
  const streamRef        = useRef<MediaStream | null>(null)
  const audioCtxRef      = useRef<AudioContext | null>(null)
  const analyserRef      = useRef<AnalyserNode | null>(null)
  const resolveRef       = useRef<((blob: Blob) => void) | null>(null)

  const startRecording = useCallback(async () => {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        sampleRate: 44100,
      },
    })
    streamRef.current = stream

    // Web Audio API — create AnalyserNode for real-time waveform visualization
    const audioCtx = new AudioContext()
    const source   = audioCtx.createMediaStreamSource(stream)
    const analyser = audioCtx.createAnalyser()
    analyser.fftSize               = 256
    analyser.smoothingTimeConstant = 0.8
    source.connect(analyser)
    // Note: intentionally NOT connecting analyser to audioCtx.destination
    // so the user doesn't hear their own voice played back
    audioCtxRef.current = audioCtx
    analyserRef.current = analyser

    // Pick the best supported MIME type
    const mimeType =
      MediaRecorder.isTypeSupported('audio/webm;codecs=opus') ? 'audio/webm;codecs=opus'
      : MediaRecorder.isTypeSupported('audio/webm')           ? 'audio/webm'
      :                                                          'audio/ogg;codecs=opus'

    const recorder  = new MediaRecorder(stream, { mimeType })
    chunksRef.current = []

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data)
    }

    recorder.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: mimeType })
      resolveRef.current?.(blob)
      audioCtxRef.current?.close()
      audioCtxRef.current = null
      analyserRef.current = null
    }

    recorder.start(100) // collect a chunk every 100ms
    mediaRecorderRef.current = recorder
  }, [])

  const stopRecording = useCallback((): Promise<Blob> => {
    return new Promise((resolve, reject) => {
      const recorder = mediaRecorderRef.current
      if (!recorder || recorder.state === 'inactive') {
        reject(new Error('No active recording'))
        return
      }
      resolveRef.current = resolve
      recorder.stop()
      streamRef.current?.getTracks().forEach((t) => t.stop())
    })
  }, [])

  return { startRecording, stopRecording, analyserNode: analyserRef }
}
