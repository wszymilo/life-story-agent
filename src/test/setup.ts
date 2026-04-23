import '@testing-library/jest-dom'
import './mocks'
import { webcrypto } from 'node:crypto'

// Expose Web Crypto API globally for tests.
if (!globalThis.crypto) {
  // @ts-expect-error jsdom doesn't have crypto.subtle
  globalThis.crypto = webcrypto
}
