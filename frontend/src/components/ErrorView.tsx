import { motion } from 'framer-motion'

interface Props {
  message: string
  onRetry: () => void
}

export function ErrorView({ message, onRetry }: Props) {
  return (
    <motion.div
      className="flex flex-col items-center gap-6 py-10 text-center"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.3 }}
    >
      <p className="text-slate-300 text-sm leading-relaxed max-w-xs">{message}</p>
      <motion.button
        className="px-6 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500
                   text-white text-sm font-medium transition-colors"
        whileHover={{ scale: 1.04 }}
        whileTap={{ scale: 0.96 }}
        onClick={onRetry}
      >
        Start again
      </motion.button>
    </motion.div>
  )
}
