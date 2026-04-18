import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AudioRecorder } from './AudioRecorder'

vi.mock('navigator.mediaDevices', () => ({
  getUserMedia: vi.fn().mockResolvedValue({
    getTracks: () => [],
  }),
}))

describe('AudioRecorder', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders record button initially', () => {
    render(<AudioRecorder />)
    expect(screen.getByRole('button', { name: /Start recording/i })).toBeInTheDocument()
  })

  it('shows instruction text', () => {
    render(<AudioRecorder />)
    expect(screen.getByText(/Tap the red circle to start recording/)).toBeInTheDocument()
  })
})