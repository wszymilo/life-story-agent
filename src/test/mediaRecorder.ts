export class MockMediaTrack {
  stopped = false
  
  stop() {
    this.stopped = true
  }
}

export class MockMediaStream {
  tracks: MockMediaTrack[] = []
  active = true
  
  constructor(tracks: MockMediaTrack[] = []) {
    this.tracks = tracks
  }
  
  getTracks(): MockMediaTrack[] {
    return this.tracks
  }
}

export class MockMediaRecorder {
  static isTypeSupported(type: string): boolean {
    return type === 'audio/webm' || type === 'audio/wav' || type === 'audio/mp4'
  }
  
  state: 'inactive' | 'recording' = 'inactive'
  ondataavailable: ((event: BlobEvent) => void) | null = null
  onstop: (() => void) | null = null
  onerror: ((event: Event) => void) | null = null

  constructor(stream: MockMediaStream, _options?: { mimeType?: string }) {
    void stream
  }
  
  start(timeslice?: number) {
    this.state = 'recording'
    
    if (timeslice) {
      setTimeout(() => {
        if (this.state === 'recording') {
          this.ondataavailable?.({
            data: new Blob(['fake-audio-data'], { type: 'audio/webm' })
          } as BlobEvent)
        }
      }, timeslice)
    }
  }
  
  stop() {
    this.state = 'inactive'
    
    this.ondataavailable?.({
      data: new Blob(['final-chunk'], { type: 'audio/webm' })
    } as BlobEvent)
    
    this.onstop?.()
  }
}

/* eslint-disable @typescript-eslint/no-explicit-any */
export function createMockStream(): MockMediaStream {
  return new MockMediaStream([new MockMediaTrack()])
}

export function setupMediaRecorderGlobal() {
  ;(global as any).MediaRecorder = MockMediaRecorder
  ;(global as any).navigator = {
    mediaDevices: {
      getUserMedia: async () => createMockStream()
    }
  }
}
