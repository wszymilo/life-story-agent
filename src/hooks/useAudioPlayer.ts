import { useState, useRef, useCallback, useEffect } from 'react'

interface PlayOptions {
  onEnded?: () => void
  onError?: () => void
}

export function useAudioPlayer() {
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentSrc, setCurrentSrc] = useState<string | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const optionsRef = useRef<PlayOptions | null>(null)

  const cleanupAudio = useCallback(() => {
    const audio = audioRef.current
    if (!audio) return
    audio.pause()
    audio.src = ''
    audio.onended = null
    audio.onerror = null
    audioRef.current = null
  }, [])

  const play = useCallback(async (src: string, options?: PlayOptions): Promise<void> => {
    // Pause any existing playback
    if (audioRef.current) {
      audioRef.current.pause()
    }

    optionsRef.current = options || null

    const audio = new Audio(src)
    audioRef.current = audio
    setCurrentSrc(src)

    return new Promise((resolve, reject) => {
      audio.onended = () => {
        setIsPlaying(false)
        setCurrentSrc(null)
        optionsRef.current?.onEnded?.()
        resolve()
      }

      audio.onerror = () => {
        setIsPlaying(false)
        optionsRef.current?.onError?.()
        reject(new Error('Audio playback failed'))
      }

      audio.play().then(() => {
        setIsPlaying(true)
      }).catch((err) => {
        setIsPlaying(false)
        optionsRef.current?.onError?.()
        reject(err)
      })
    })
  }, [])

  const pause = useCallback(() => {
    audioRef.current?.pause()
    setIsPlaying(false)
  }, [])

  useEffect(() => {
    return () => {
      cleanupAudio()
    }
  }, [cleanupAudio])

  return { play, pause, isPlaying, currentSrc }
}
