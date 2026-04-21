import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useRecorder } from './useRecorder'
import { setupMediaMocks, cleanupMediaMocks } from '../test/mediaDevices'

describe('useRecorder', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    setupMediaMocks()
  })
  
  afterEach(() => {
    cleanupMediaMocks()
    vi.useRealTimers()
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

  it('startRecording sets isRecording to true', async () => {
    const { result } = renderHook(() => useRecorder())
    
    await act(async () => {
      await result.current.startRecording()
    })
    
    expect(result.current.isRecording).toBe(true)
  })

  it('stopRecording sets isRecording to false', async () => {
    const { result } = renderHook(() => useRecorder())
    
    await act(async () => {
      await result.current.startRecording()
    })
    
    act(() => {
      result.current.stopRecording()
    })
    
    expect(result.current.isRecording).toBe(false)
  })

  it('stopRecording clears duration interval', async () => {
    const { result } = renderHook(() => useRecorder())
    
    await act(async () => {
      await result.current.startRecording()
    })
    
    act(() => {
      vi.advanceTimersByTime(5000)
    })
    
    expect(result.current.duration).toBeGreaterThan(0)
    
    act(() => {
      result.current.stopRecording()
    })
    
    const durationAfterStop = result.current.duration
    
    act(() => {
      vi.advanceTimersByTime(2000)
    })
    
    expect(result.current.duration).toBe(durationAfterStop)
  })

  it('reset clears all state', async () => {
    const { result } = renderHook(() => useRecorder())
    
    await act(async () => {
      await result.current.startRecording()
    })
    
    act(() => {
      vi.advanceTimersByTime(3000)
    })
    
    act(() => {
      result.current.reset()
    })
    
    expect(result.current.isRecording).toBe(false)
    expect(result.current.duration).toBe(0)
    expect(result.current.audioBlob).toBeNull()
    expect(result.current.error).toBeNull()
  })

  it('increments duration while recording', async () => {
    const { result } = renderHook(() => useRecorder())
    
    await act(async () => {
      await result.current.startRecording()
    })
    
    act(() => {
      vi.advanceTimersByTime(3000)
    })
    
    expect(result.current.duration).toBe(3)
  })
})
