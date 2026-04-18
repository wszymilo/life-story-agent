import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useRecorder } from './useRecorder'

vi.mock('navigator.mediaDevices', () => ({
  getUserMedia: vi.fn().mockResolvedValue({
    getTracks: () => [],
  }),
}))

describe('useRecorder', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('initializes with default state', () => {
    const { result } = renderHook(() => useRecorder())
    
    expect(result.current.isRecording).toBe(false)
    expect(result.current.duration).toBe(0)
    expect(result.current.audioBlob).toBeNull()
    expect(result.current.error).toBeNull()
  })

  it('provides startRecording, stopRecording, reset functions', () => {
    const { result } = renderHook(() => useRecorder())
    
    expect(typeof result.current.startRecording).toBe('function')
    expect(typeof result.current.stopRecording).toBe('function')
    expect(typeof result.current.reset).toBe('function')
  })
})