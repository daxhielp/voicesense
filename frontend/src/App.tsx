import { useState, useCallback, useEffect } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import axios from 'axios'
import { ParticleBackground }  from './components/ParticleBackground'
import { IdleView }            from './components/IdleView'
import { RecordingView }       from './components/RecordingView'
import { ResultView }          from './components/ResultView'
import { ErrorView }           from './components/ErrorView'
import { useAudioRecorder }    from './hooks/useAudioRecorder'
import { predictEmotion, API_BASE, type PredictionResult } from './api/predict'

type AppState = 'idle' | 'recording' | 'processing' | 'result' | 'error'

function ProcessingView({ elapsedSeconds }: { elapsedSeconds: number }) {
  const message =
    elapsedSeconds < 5  ? 'Analyzing your voice...'           :
    elapsedSeconds < 12 ? 'Processing audio...'               :
    elapsedSeconds < 20 ? 'Server warming up, please wait...' :
                          'Almost there...'

  return (
    <motion.div
      className="flex flex-col items-center gap-5 py-10"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="relative flex items-center justify-center w-16 h-16">
        {/* Spinning ring */}
        <motion.div
          className="absolute inset-0 rounded-full border-2 border-violet-500/30 border-t-violet-400"
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
        />
        {/* Inner pulse */}
        <motion.div
          className="w-4 h-4 rounded-full bg-violet-500/50"
          animate={{ scale: [1, 1.4, 1], opacity: [0.6, 1, 0.6] }}
          transition={{ duration: 1, repeat: Infinity }}
        />
      </div>
      <p className="text-slate-400 text-sm tracking-wide">{message}</p>
      {elapsedSeconds >= 20 && (
        <p className="text-slate-600 text-xs">{elapsedSeconds}s elapsed</p>
      )}
    </motion.div>
  )
}

export default function App() {
  const [appState,       setAppState]       = useState<AppState>('idle')
  const [result,         setResult]         = useState<PredictionResult | null>(null)
  const [error,          setError]          = useState<string | null>(null)
  const [processingTime, setProcessingTime] = useState(0)

  const { startRecording, stopRecording, analyserNode } = useAudioRecorder()

  // ── Keep-alive: ping /health on mount + every 4 min to prevent Render cold starts ──
  useEffect(() => {
    const ping = () =>
      fetch(`${API_BASE}/health`, { method: 'GET' }).catch(() => {})
    ping()
    const id = setInterval(ping, 4 * 60 * 1000)
    return () => clearInterval(id)
  }, [])

  // ── Processing timer: count seconds while waiting for prediction ──────────────
  useEffect(() => {
    if (appState !== 'processing') {
      setProcessingTime(0)
      return
    }
    const id = setInterval(() => setProcessingTime(t => t + 1), 1000)
    return () => clearInterval(id)
  }, [appState])

  const handleStart = useCallback(async () => {
    setError(null)
    try {
      await startRecording()
      setAppState('recording')
    } catch {
      setError('Microphone access denied. Please allow microphone permissions and try again.')
      setAppState('idle')
    }
  }, [startRecording])

  const handleStop = useCallback(async () => {
    setAppState('processing')
    try {
      const blob       = await stopRecording()
      const prediction = await predictEmotion(blob)
      setResult(prediction)
      setAppState('result')
    } catch (err) {
      let msg = 'Prediction failed — please try again.'
      if (axios.isAxiosError(err)) {
        if (err.code === 'ECONNABORTED') {
          msg = 'The server is warming up after a period of inactivity. This can take up to 60 seconds on first load — please try again.'
        } else if (!err.response) {
          msg = 'Could not reach the server. Please check your connection and try again.'
        } else if (err.response.status >= 500) {
          msg = `Server error (${err.response.status}). Please try again in a moment.`
        }
      }
      setError(msg)
      setAppState('error')
    }
  }, [stopRecording])

  const handleReset = useCallback(() => {
    setResult(null)
    setError(null)
    setAppState('idle')
  }, [])

  return (
    <div className="relative min-h-screen bg-bg text-white overflow-hidden">
      <ParticleBackground />

      <div className="relative z-10 min-h-screen flex flex-col items-center justify-center px-4">

        {/* ── Header ── */}
        <motion.header
          className="mb-10 text-center"
          initial={{ opacity: 0, y: -18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: 'easeOut' }}
        >
          <h1 className="text-4xl font-bold tracking-tight">
            Voice<span className="text-violet-400">Sense</span>
          </h1>
          <p className="mt-1.5 text-xs text-slate-500 tracking-[0.2em] uppercase">
            Speech Emotion Recognition
          </p>
        </motion.header>

        {/* ── Main card ── */}
        <motion.main
          className="w-full max-w-md bg-surface border border-border rounded-2xl p-8
                     shadow-2xl shadow-black/60"
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.55, ease: 'easeOut', delay: 0.15 }}
        >
          <AnimatePresence mode="wait">
            {appState === 'idle' && (
              <IdleView key="idle" onStart={handleStart} error={error} />
            )}
            {appState === 'recording' && (
              <RecordingView key="recording" analyserNode={analyserNode} onStop={handleStop} />
            )}
            {appState === 'processing' && (
              <ProcessingView key="processing" elapsedSeconds={processingTime} />
            )}
            {appState === 'result' && result && (
              <ResultView key="result" result={result} onReset={handleReset} />
            )}
            {appState === 'error' && (
              <ErrorView key="error" message={error ?? 'Something went wrong.'} onRetry={handleReset} />
            )}
          </AnimatePresence>
        </motion.main>

        {/* ── Footer ── */}
        <motion.footer
          className="mt-8 flex flex-col items-center gap-1"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.9 }}
        >
          <p className="text-xs text-slate-700">
            Detect from 8 emotions · CNN + mel spectrogram model
          </p>
          <p className="text-xs text-slate-800">
            FastAPI · React · Tailwind · Framer Motion
          </p>
        </motion.footer>
      </div>
    </div>
  )
}
