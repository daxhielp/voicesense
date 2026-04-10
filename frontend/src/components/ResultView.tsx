import { motion } from 'framer-motion'
import type { PredictionResult } from '../api/predict'

interface Props {
  result: PredictionResult
  onReset: () => void
}

const DESCRIPTIONS: Record<string, string> = {
  neutral:   'Balanced and composed',
  calm:      'Relaxed and serene',
  happy:     'Joyful and elated',
  sad:       'Melancholic and downcast',
  angry:     'Intense and forceful',
  fearful:   'Anxious and apprehensive',
  disgust:   'Repulsed and averse',
  surprised: 'Astonished and alert',
}

/**
 * Result state — animated emotion hero (emoji + label + confidence badge)
 * followed by staggered probability bars for all 8 emotions.
 * Bar widths are relative to the top prediction so the winner always fills 100%.
 */
export function ResultView({ result, onReset }: Props) {
  const sorted  = Object.entries(result.probabilities)   // already sorted desc from API
  const maxProb = sorted[0][1]

  return (
    <motion.div
      className="flex flex-col gap-5"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.35 }}
    >
      {/* ── Dominant emotion hero ── */}
      <motion.div
        className="text-center py-3"
        initial={{ scale: 0.75, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: 'spring', stiffness: 220, damping: 20 }}
      >
        {/* Emoji */}
        <motion.div
          className="text-5xl mb-2 select-none"
          animate={{ rotate: [0, -6, 6, -3, 3, 0] }}
          transition={{ duration: 0.6, delay: 0.3 }}
        >
          {result.emoji}
        </motion.div>

        {/* Emotion label */}
        <h2
          className="text-3xl font-bold capitalize tracking-tight"
          style={{ color: result.color }}
        >
          {result.emotion}
        </h2>

        {/* Description */}
        <p className="text-slate-500 text-sm mt-1">
          {DESCRIPTIONS[result.emotion] ?? ''}
        </p>

        {/* Confidence badge */}
        <motion.div
          className="inline-flex items-center gap-1.5 mt-3 px-3 py-1 rounded-full
                     text-xs font-mono"
          style={{
            backgroundColor: result.color + '1a',
            color:            result.color,
            border:           `1px solid ${result.color}44`,
          }}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <span
            className="inline-block w-1.5 h-1.5 rounded-full"
            style={{ backgroundColor: result.color }}
          />
          {result.confidence.toFixed(1)}% confidence
        </motion.div>
      </motion.div>

      {/* ── Probability bars ── */}
      <div className="flex flex-col gap-2">
        {sorted.map(([emotion, prob], i) => {
          const isWinner = emotion === result.emotion
          const barWidth = maxProb > 0 ? (prob / maxProb) * 100 : 0

          return (
            <motion.div
              key={emotion}
              className="flex items-center gap-3"
              initial={{ opacity: 0, x: -16 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.065, duration: 0.32, ease: 'easeOut' }}
            >
              {/* Label */}
              <span
                className="w-20 text-xs capitalize text-right shrink-0 select-none"
                style={{
                  color:      isWinner ? result.color : '#64748b',
                  fontWeight: isWinner ? 600 : 400,
                }}
              >
                {emotion}
              </span>

              {/* Bar track */}
              <div className="flex-1 h-1.5 rounded-full overflow-hidden bg-white/5">
                <motion.div
                  className="h-full rounded-full"
                  style={{ backgroundColor: isWinner ? result.color : '#334155' }}
                  initial={{ width: 0 }}
                  animate={{ width: `${barWidth}%` }}
                  transition={{
                    delay:    i * 0.065 + 0.14,
                    duration: 0.55,
                    ease:     'easeOut',
                  }}
                />
              </div>

              {/* Percentage */}
              <span className="w-12 text-xs font-mono text-slate-500 text-right shrink-0">
                {prob.toFixed(1)}%
              </span>
            </motion.div>
          )
        })}
      </div>

      {/* ── Try again ── */}
      <motion.button
        onClick={onReset}
        className="mt-1 w-full py-3 rounded-xl text-sm font-medium
                   bg-violet-600/15 border border-violet-500/30 text-violet-400
                   hover:bg-violet-600/25 transition-colors"
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.65 }}
      >
        Try Again
      </motion.button>
    </motion.div>
  )
}
