import { useState } from 'react'
import { signOut } from '../services/auth'

export function DebugScreen() {
  const [status, setStatus] = useState<string>('')

  const handleClear = async () => {
    await signOut()
    setStatus('Signed out')
  }

  return (
    <div className="min-h-screen p-8 bg-gray-50">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Debug Page</h1>

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
