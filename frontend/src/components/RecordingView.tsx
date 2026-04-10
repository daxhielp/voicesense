import { useEffect, useState, type MutableRefObject } from 'react'
import { motion } from 'framer-motion'
import { WaveformVisualizer } from './WaveformVisualizer'

interface Props {
  analyserNode: MutableRefObject<AnalyserNode | null>
  onStop: () => void
}

const MAX_SECONDS = 10

/**
 * Recording state — shows a REC indicator with elapsed/remaining time,
 * a live waveform visualizer, and a stop button.
 * Auto-stops after MAX_SECONDS.
 */
export function RecordingView({ analyserNode, onStop }: Props) {
  const [seconds, setSeconds] = useState(0)

  // Tick up every second
  useEffect(() => {
    const id = setInterval(() => setSeconds((s) => s + 1), 1000)
    return () => clearInterval(id)
  }, [])

  // Auto-stop at MAX_SECONDS
  useEffect(() => {
    if (seconds >= MAX_SECONDS) onStop()
  }, [seconds, onStop])

  const timeLeft  = MAX_SECONDS - seconds
  const progress  = seconds / MAX_SECONDS  // 0 → 1

  const mm = String(Math.floor(seconds / 60)).padStart(2, '0')
  const ss = String(seconds % 60).padStart(2, '0')

  return (
    <motion.div
      className="flex flex-col items-center gap-6 py-4"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
    >
      {/* Header row: REC dot + timer + countdown */}
      <div className="flex items-center justify-between w-full">
        <div className="flex items-center gap-2">
          <motion.div
            className="w-2.5 h-2.5 rounded-full bg-red-500"
            animate={{ opacity: [1, 0.15, 1] }}
            transition={{ duration: 1, repeat: Infinity }}
          />
          <span className="font-mono text-sm text-slate-300 tracking-widest">
            REC {mm}:{ss}
          </span>
        </div>
        <span className="text-xs text-slate-500 font-mono">{timeLeft}s left</span>
      </div>

      {/* Progress bar */}
      <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden">
        <motion.div
          className="h-full rounded-full bg-gradient-to-r from-violet-600 to-violet-400"
          initial={{ width: 0 }}
          animate={{ width: `${progress * 100}%` }}
          transition={{ duration: 0.5, ease: 'linear' }}
        />
      </div>

      {/* Live waveform */}
      <WaveformVisualizer analyserNode={analyserNode} isActive={true} />

      {/* Stop button */}
      <motion.button
        onClick={onStop}
        className="px-10 py-3 rounded-xl text-sm font-medium
                   bg-red-500/15 border border-red-500/35 text-red-400
                   hover:bg-red-500/25 transition-colors"
        whileHover={{ scale: 1.03 }}
        whileTap={{ scale: 0.97 }}
      >
        Stop &amp; Analyze
      </motion.button>
    </motion.div>
  )
}
