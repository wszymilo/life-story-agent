import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../context/AuthContext'
import { generateKey, exportKey, importKey } from '../lib/crypto'
import { getKey, setKey } from '../lib/keyStore'

interface EncryptionState {
  key: CryptoKey | null
  isReady: boolean
  isGenerating: boolean
  error: string | null
}

export function useEncryption(): EncryptionState {
  const { user } = useAuth()
  const [state, setState] = useState<EncryptionState>({
    key: null,
    isReady: false,
    isGenerating: false,
    error: null,
  })

  const initKey = useCallback(async () => {
    if (!user) {
      setState({ key: null, isReady: false, isGenerating: false, error: null })
      return
    }

    setState((s) => ({ ...s, isGenerating: true, error: null }))

    try {
      // Try to load existing key
      const raw = await getKey(user.id)
      if (raw) {
        const key = await importKey(raw)
        setState({ key, isReady: true, isGenerating: false, error: null })
        return
      }

      // Generate new key
      const newKey = await generateKey()
      const exported = await exportKey(newKey)
      await setKey(user.id, exported)
      setState({ key: newKey, isReady: true, isGenerating: false, error: null })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to initialize encryption'
      setState({ key: null, isReady: false, isGenerating: false, error: message })
    }
  }, [user])

  useEffect(() => {
    initKey()
  }, [initKey])

  return state
}
