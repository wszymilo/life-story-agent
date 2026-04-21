import { MockMediaRecorder, MockMediaStream, MockMediaTrack } from './mediaRecorder'

export function setupMediaMocks() {
  const mockStream = new MockMediaStream([new MockMediaTrack()])
  
  const mockMediaDevices = {
    getUserMedia: async () => mockStream,
  }
  
  ;(global as any).MediaRecorder = MockMediaRecorder
  ;(global as any).navigator = {
    mediaDevices: mockMediaDevices
  }
  
  return mockStream
}

export function cleanupMediaMocks() {
  delete (global as any).MediaRecorder
  delete (global as any).navigator
}
