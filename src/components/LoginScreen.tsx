import { useState, FormEvent } from 'react'
import { signInWithMagicLink } from '../services/auth'

type LoginState = 'idle' | 'loading' | 'success' | 'error'

export function LoginScreen() {
  const [email, setEmail] = useState('')
  const [loginState, setLoginState] = useState<LoginState>('idle')
  const [errorMessage, setErrorMessage] = useState('')

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLoginState('loading')
    setErrorMessage('')

    const result = await signInWithMagicLink(email)

    if (result.success) {
      setLoginState('success')
    } else {
      setLoginState('error')
      setErrorMessage(result.error || 'Failed to send magic link')
    }
  }

  if (loginState === 'success') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8 text-center">
          <div className="text-green-600 text-5xl mb-4">✓</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Check your email
          </h1>
          <p className="text-gray-600">
            We sent a magic link to <strong>{email}</strong>. Click the link
            in the email to sign in.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Life Story Agent
          </h1>
          <p className="text-gray-600 mt-2">
            Preserve your precious memories
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">
            Sign in with Email
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Email address
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
                disabled={loginState === 'loading'}
              />
            </div>

            {loginState === 'error' && (
              <div className="text-red-600 text-sm">{errorMessage}</div>
            )}

            <button
              type="submit"
              disabled={loginState === 'loading'}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium text-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loginState === 'loading' ? 'Sending...' : 'Send Magic Link'}
            </button>
          </form>
        </div>

        <p className="text-center text-gray-500 text-sm mt-6">
          We'll email you a magic link. Click it to sign in instantly.
        </p>
      </div>
    </div>
  )
}