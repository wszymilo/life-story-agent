import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { RecordingScreen } from './RecordingScreen'

vi.mock('./AudioRecorder', () => ({
  AudioRecorder: vi.fn(({ onRecordingComplete }) => (
    <div data-testid="audio-recorder">
      <button onClick={() => onRecordingComplete?.(new Blob(['test'], { type: 'audio/webm' }))}>
        Start Recording
      </button>
    </div>
  )),
}))

const mockCreateEvent = vi.fn()
const mockAddRecording = vi.fn()
const mockRetryTranscribe = vi.fn()
const mockNavigate = vi.fn()

vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}))

vi.mock('../services/events', () => ({
  createEvent: (...args: unknown[]) => mockCreateEvent(...args),
  addRecording: (...args: unknown[]) => mockAddRecording(...args),
  retryTranscribe: (...args: unknown[]) => mockRetryTranscribe(...args),
}))

describe('RecordingScreen', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders recording screen', () => {
    render(<RecordingScreen />)

    expect(screen.getByText('Tell Your Story')).toBeInTheDocument()
    expect(screen.getByText('Press the button below and share your life story')).toBeInTheDocument()
  })

  it('renders AudioRecorder component', () => {
    render(<RecordingScreen />)

    expect(screen.getByTestId('audio-recorder')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /start recording/i })).toBeInTheDocument()
  })
})