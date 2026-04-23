/**
 * Client-side encryption utilities using Web Crypto API (AES-256-GCM).
 *
 * The encryption key never leaves the browser. Ciphertext format:
 *   base64(iv + ciphertext + authTag)
 * where iv = 12 bytes, authTag = 16 bytes (appended by AES-GCM).
 */

const IV_LENGTH = 12

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  if (typeof Buffer !== 'undefined') {
    return Buffer.from(buffer).toString('base64')
  }
  const bytes = new Uint8Array(buffer)
  let binary = ''
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i])
  }
  return btoa(binary)
}

function base64ToArrayBuffer(base64: string): ArrayBuffer {
  if (typeof Buffer !== 'undefined') {
    // Validate base64 strictly using atob (throws on invalid input),
    // then use Buffer for realm-safe ArrayBuffer creation.
    const binary = atob(base64)
    const buf = Buffer.from(binary, 'binary')
    return buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength)
  }
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i)
  }
  return bytes.buffer
}

export async function generateKey(): Promise<CryptoKey> {
  return crypto.subtle.generateKey(
    { name: 'AES-GCM', length: 256 },
    true,
    ['encrypt', 'decrypt']
  )
}

export async function encrypt(plaintext: string, key: CryptoKey): Promise<string> {
  const iv = crypto.getRandomValues(new Uint8Array(IV_LENGTH))
  const encoded = new TextEncoder().encode(plaintext)

  const ciphertext = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    key,
    encoded
  )

  const combined = new Uint8Array(iv.byteLength + ciphertext.byteLength)
  combined.set(iv, 0)
  combined.set(new Uint8Array(ciphertext), iv.byteLength)

  return arrayBufferToBase64(combined.buffer)
}

export async function decrypt(ciphertext: string, key: CryptoKey): Promise<string> {
  try {
    const combined = new Uint8Array(base64ToArrayBuffer(ciphertext))

    if (combined.byteLength < IV_LENGTH) {
      return ciphertext
    }

    const iv = combined.slice(0, IV_LENGTH)
    const data = combined.slice(IV_LENGTH)

    const decrypted = await crypto.subtle.decrypt(
      { name: 'AES-GCM', iv },
      key,
      data
    )

    return new TextDecoder().decode(decrypted)
  } catch {
    return ciphertext
  }
}

export async function exportKey(key: CryptoKey): Promise<string> {
  const raw = await crypto.subtle.exportKey('raw', key)
  return arrayBufferToBase64(raw)
}

export async function importKey(raw: string): Promise<CryptoKey> {
  const buffer = base64ToArrayBuffer(raw)
  return crypto.subtle.importKey(
    'raw',
    buffer,
    { name: 'AES-GCM', length: 256 },
    true,
    ['encrypt', 'decrypt']
  )
}
