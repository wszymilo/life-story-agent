import { useEffect, useState } from 'react'
import { fetchAuthSession, signOut } from 'aws-amplify/auth'

export function DebugScreen() {
  const [token, setToken] = useState<string | null>(null)
  const [inputToken, setInputToken] = useState('')
  const [status, setStatus] = useState<string>('')

  useEffect(() => {
    const loadToken = async () => {
      try {
        const session = await fetchAuthSession()
        const tokenStr = session.tokens?.idToken?.toString()
        setToken(tokenStr ?? null)
      } catch {
        setToken(null)
      }
    }
    loadToken()
  }, [])

  const handleRestore = async () => {
    if (!inputToken.trim()) {
      setStatus('Please enter a token')
      return
    }
    setStatus('Token restore not implemented - use manual localStorage paste')
  }

  const handleCopy = () => {
    if (token) {
      navigator.clipboard.writeText(token)
      setStatus('Copied to clipboard!')
      setTimeout(() => setStatus(''), 2000)
    }
  }

  const handleClear = async () => {
    await signOut()
    setToken(null)
    setStatus('Signed out')
  }

  return (
    <div className="min-h-screen p-8 bg-gray-50">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Debug Token Page</h1>

        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h2 className="text-lg font-semibold mb-2">Current Token</h2>
          {token ? (
            <div className="space-y-2">
              <p className="text-green-600 font-medium">Token present</p>
              <button
                type="button"
                onClick={handleCopy}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Copy Token
              </button>
            </div>
          ) : (
            <p className="text-red-500">No token found</p>
          )}
        </div>

        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h2 className="text-lg font-semibold mb-2">Restore Token</h2>
          <p className="text-sm text-gray-600 mb-4">
            Token restore functionality note here
          </p>
          <textarea
            id="token-input"
            name="token"
            value={inputToken}
            onChange={(e) => setInputToken(e.target.value)}
            placeholder="Paste token here..."
            className="w-full p-3 border rounded mb-2 font-mono text-xs"
            rows={4}
          />
          <button
            type="button"
            onClick={handleRestore}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
          >
            Show How to Restore
          </button>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-2">Actions</h2>
          <button
            type="button"
            onClick={handleClear}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Sign Out
          </button>
        </div>

        {status && (
          <p className="mt-4 p-3 bg-blue-100 text-blue-800 rounded">{status}</p>
        )}
      </div>
    </div>
  )
}