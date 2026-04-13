import axios from 'axios'

export interface PredictionResult {
  emotion: string
  confidence: number
  probabilities: Record<string, number>
  color: string
  emoji: string
}

/**
 * In production VITE_API_URL is set to the Render backend URL.
 * In local dev it falls back to '/api', which Vite proxies to localhost:8000.
 */
export const API_BASE = import.meta.env.VITE_API_URL ?? '/api'

export async function predictEmotion(audioBlob: Blob): Promise<PredictionResult> {
  const formData = new FormData()
  // Field name 'audio' must match the FastAPI parameter name
  formData.append('audio', audioBlob, 'recording.webm')

  const response = await axios.post<PredictionResult>(
    `${API_BASE}/predict`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 180_000, // 3 min — Render free tier shared CPU can be slow
    },
  )
  return response.data
}
