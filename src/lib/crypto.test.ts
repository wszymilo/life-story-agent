import { describe, it, expect } from 'vitest'
import { generateKey, encrypt, decrypt, exportKey, importKey } from './crypto'

describe('crypto utilities', () => {
  it('roundtrip encrypt and decrypt', async () => {
    const key = await generateKey()
    const plaintext = 'Hello, this is a secret message for my mother!'

    const ciphertext = await encrypt(plaintext, key)
    const decrypted = await decrypt(ciphertext, key)

    expect(decrypted).toBe(plaintext)
  })

  it('produces different ciphertext for same plaintext (random IV)', async () => {
    const key = await generateKey()
    const plaintext = 'Same text'

    const ciphertext1 = await encrypt(plaintext, key)
    const ciphertext2 = await encrypt(plaintext, key)

    expect(ciphertext1).not.toBe(ciphertext2)
  })

  it('roundtrip key export and import', async () => {
    const key = await generateKey()
    const raw = await exportKey(key)
    const imported = await importKey(raw)

    const plaintext = 'Test with imported key'
    const ciphertext = await encrypt(plaintext, key)
    const decrypted = await decrypt(ciphertext, imported)

    expect(decrypted).toBe(plaintext)
  })

  it('handles empty string', async () => {
    const key = await generateKey()
    const plaintext = ''

    const ciphertext = await encrypt(plaintext, key)
    const decrypted = await decrypt(ciphertext, key)

    expect(decrypted).toBe(plaintext)
  })

  it('handles unicode and polish characters', async () => {
    const key = await generateKey()
    const plaintext = 'Moja mama mieszkała w Warszawie podczas wojny. Żółć!'

    const ciphertext = await encrypt(plaintext, key)
    const decrypted = await decrypt(ciphertext, key)

    expect(decrypted).toBe(plaintext)
  })

  it('throws on invalid ciphertext', async () => {
    const key = await generateKey()
    await expect(decrypt('invalid', key)).rejects.toThrow()
  })

  it('throws on tampered ciphertext', async () => {
    const key = await generateKey()
    const ciphertext = await encrypt('secret', key)

    // Tamper with the last character
    const tampered = ciphertext.slice(0, -1) + 'X'

    await expect(decrypt(tampered, key)).rejects.toThrow()
  })
})
