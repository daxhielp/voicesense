import { motion } from 'framer-motion'

interface Props {
  onStart: () => void
  error: string | null
}

/**
 * Idle state — large mic button with two concentric pulsing rings.
 * Shows an error banner below if the previous attempt failed (mic denied, API error, etc).
 */
export function IdleView({ onStart, error }: Props) {
  return (
    <motion.div
      className="flex flex-col items-center gap-8 py-4"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
    >
      {/* Mic button with animated rings */}
      <div className="relative flex items-center justify-center" style={{ width: 140, height: 140 }}>
        {/* Outermost ring */}
        <motion.div
          className="absolute rounded-full border border-violet-500/15"
          style={{ width: 140, height: 140 }}
          animate={{ scale: [1, 1.18, 1], opacity: [0.25, 0, 0.25] }}
          transition={{ duration: 2.8, repeat: Infinity, ease: 'easeInOut' }}
        />
        {/* Inner ring */}
        <motion.div
          className="absolute rounded-full border border-violet-500/25"
          style={{ width: 110, height: 110 }}
          animate={{ scale: [1, 1.14, 1], opacity: [0.5, 0.05, 0.5] }}
          transition={{ duration: 2.8, repeat: Infinity, ease: 'easeInOut', delay: 0.35 }}
        />

        {/* Button */}
        <motion.button
          onClick={onStart}
          className="relative flex items-center justify-center rounded-full bg-violet-600
                     shadow-lg shadow-violet-900/60 cursor-pointer select-none"
          style={{ width: 80, height: 80 }}
          whileHover={{ scale: 1.07, backgroundColor: '#7c3aed' }}
          whileTap={{ scale: 0.93 }}
          transition={{ type: 'spring', stiffness: 300, damping: 22 }}
          aria-label="Start recording"
        >
          {/* Microphone icon */}
          <svg
            width="34"
            height="34"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <rect x="9" y="1" width="6" height="11" rx="3" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
            <line x1="12" y1="19" x2="12" y2="23" />
            <line x1="8"  y1="23" x2="16" y2="23" />
          </svg>
        </motion.button>
      </div>

      {/* Instructions */}
      <div className="text-center space-y-1">
        <p className="text-slate-400 text-sm font-medium">
          Tap to start recording
        </p>
        <p className="text-slate-600 text-xs">
          Speak naturally for up to 10 seconds
        </p>
        <p className="text-slate-700 text-xs">
          Detects neutral · calm · happy · sad · angry · fearful · disgust · surprised
        </p>
      </div>

      {/* Error banner */}
      {error && (
        <motion.div
          className="w-full px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/25
                     text-red-400 text-sm text-center"
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
        >
          {error}
        </motion.div>
      )}
    </motion.div>
  )
}
