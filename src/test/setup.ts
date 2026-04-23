import '@testing-library/jest-dom'
import './mocks'
import { webcrypto } from 'node:crypto'

// Expose Web Crypto API globally for tests.
// jsdom may provide a global crypto object without subtle, or with a subtle
// implementation that rejects ArrayBuffers from a different realm. We always
// replace it with Node.js webcrypto to guarantee compatibility.
Object.defineProperty(globalThis, 'crypto', {
  value: webcrypto,
  writable: true,
  configurable: true,
})
