import { useEffect, useRef, type MutableRefObject } from 'react'

interface Props {
  analyserNode: MutableRefObject<AnalyserNode | null>
  isActive: boolean
}

/**
 * Real-time audio waveform rendered on a Canvas element.
 * Reads time-domain data from the Web Audio AnalyserNode at ~60fps via
 * requestAnimationFrame. Draws a violet gradient stroke with a glow effect.
 * When inactive (not recording) the canvas shows a flat idle line.
 */
export function WaveformVisualizer({ analyserNode, isActive }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const rafRef    = useRef<number>(0)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const drawIdleLine = () => {
      const W = canvas.offsetWidth * window.devicePixelRatio
      const H = canvas.offsetHeight * window.devicePixelRatio
      canvas.width  = W
      canvas.height = H
      ctx.clearRect(0, 0, W, H)
      ctx.lineWidth   = 1.5
      ctx.strokeStyle = 'rgba(139,92,246,0.25)'
      ctx.beginPath()
      ctx.moveTo(0, H / 2)
      ctx.lineTo(W, H / 2)
      ctx.stroke()
    }

    if (!isActive) {
      cancelAnimationFrame(rafRef.current)
      drawIdleLine()
      return
    }

    const draw = () => {
      const analyser = analyserNode.current
      if (!analyser) return

      rafRef.current = requestAnimationFrame(draw)

      // Match canvas resolution to display size
      const W = canvas.offsetWidth * window.devicePixelRatio
      const H = canvas.offsetHeight * window.devicePixelRatio
      if (canvas.width !== W || canvas.height !== H) {
        canvas.width  = W
        canvas.height = H
      }

      const bufferLen  = analyser.frequencyBinCount
      const dataArray  = new Uint8Array(bufferLen)
      analyser.getByteTimeDomainData(dataArray)

      ctx.clearRect(0, 0, W, H)

      // Gradient stroke — left violet → center lavender → right violet
      const gradient = ctx.createLinearGradient(0, 0, W, 0)
      gradient.addColorStop(0,    '#6d28d9')
      gradient.addColorStop(0.5,  '#c4b5fd')
      gradient.addColorStop(1,    '#6d28d9')

      ctx.lineWidth    = 2.5 * window.devicePixelRatio
      ctx.strokeStyle  = gradient
      ctx.shadowColor  = '#8b5cf6'
      ctx.shadowBlur   = 12
      ctx.lineJoin     = 'round'
      ctx.lineCap      = 'round'

      ctx.beginPath()
      const sliceW = W / bufferLen
      let x = 0

      for (let i = 0; i < bufferLen; i++) {
        const v = dataArray[i] / 128.0   // [0, 2]; 1.0 = silence
        const y = (v * H) / 2
        if (i === 0) { ctx.moveTo(x, y) } else { ctx.lineTo(x, y) }
        x += sliceW
      }

      ctx.lineTo(W, H / 2)
      ctx.stroke()
    }

    draw()
    return () => cancelAnimationFrame(rafRef.current)
  }, [isActive, analyserNode])

  return (
    <canvas
      ref={canvasRef}
      className="w-full h-20 rounded-xl"
      style={{ background: 'rgba(0,0,0,0.25)' }}
    />
  )
}
