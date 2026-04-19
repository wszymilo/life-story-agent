import { vi } from 'vitest'

export type MockResponseOptions = {
  ok?: boolean
  status?: number
  statusText?: string
  json?: () => Promise<unknown>
  blob?: () => Promise<Blob>
}

export function createFetchMock(options?: MockResponseOptions) : ReturnType<typeof fetch> {
  const {
    ok = true,
    status = 200,
    statusText = 'OK',
    json = () => Promise.resolve({}),
    blob = () => Promise.resolve(new Blob()),
  } = options || {}

  return {
    ok,
    status,
    statusText,
    json: vi.fn(json),
    blob: vi.fn(blob),
  }
}

export function createErrorResponse(message: string, status = 400) {
  return createFetchMock({
    ok: false,
    status,
    statusText: 'Error',
    json: () => Promise.resolve({ detail: message }),
  })
}

export const mockFetch = vi.fn()

export function setupFetchMock() {
  mockFetch.mockReset()
  return mockFetch
}

export function mockFetchResponse(response: MockResponseOptions | Error) {
  if (response instanceof Error) {
    mockFetch.mockRejectedOnce(response)
  } else {
    mockFetch.mockResolvedOnce(response)
  }
}