import { motion } from 'framer-motion'

/**
 * Full-screen animated background.
 * Three large radial-gradient orbs drift slowly using Framer Motion keyframe
 * animations at different speeds and phases. A subtle CSS grid overlay adds
 * depth without being distracting.
 */
export function ParticleBackground() {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none" aria-hidden>
      {/* Primary orb — violet */}
      <motion.div
        className="absolute rounded-full blur-3xl"
        style={{
          width: 700,
          height: 700,
          background: 'radial-gradient(circle, rgba(124,58,237,0.18) 0%, transparent 70%)',
          top: '-20%',
          left: '-15%',
        }}
        animate={{ x: [0, 70, -30, 0], y: [0, 50, 90, 0] }}
        transition={{ duration: 22, repeat: Infinity, ease: 'easeInOut' }}
      />

      {/* Secondary orb — blue */}
      <motion.div
        className="absolute rounded-full blur-3xl"
        style={{
          width: 550,
          height: 550,
          background: 'radial-gradient(circle, rgba(37,99,235,0.14) 0%, transparent 70%)',
          bottom: '-18%',
          right: '-12%',
        }}
        animate={{ x: [0, -60, 25, 0], y: [0, -70, -20, 0] }}
        transition={{ duration: 28, repeat: Infinity, ease: 'easeInOut', delay: 5 }}
      />

      {/* Tertiary orb — cyan accent */}
      <motion.div
        className="absolute rounded-full blur-3xl"
        style={{
          width: 400,
          height: 400,
          background: 'radial-gradient(circle, rgba(8,145,178,0.10) 0%, transparent 70%)',
          top: '45%',
          left: '55%',
        }}
        animate={{ x: [0, 50, -45, 0], y: [0, -90, 35, 0] }}
        transition={{ duration: 19, repeat: Infinity, ease: 'easeInOut', delay: 10 }}
      />

      {/* Subtle grid overlay */}
      <div
        className="absolute inset-0"
        style={{
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)
          `,
          backgroundSize: '64px 64px',
        }}
      />
    </div>
  )
}
