import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { handleMagicLink } from '../services/auth'
import { LoadingScreen } from '../components/LoadingScreen'

export function AuthCallbackScreen() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const processEmailLink = async () => {
      try {
        const result = await handleMagicLink()
        if (result.success) {
          navigate('/', { replace: true })
        } else {
          setError(result.error || t('auth.callbackError'))
        }
      } catch (e) {
        setError(t('auth.callbackError'))
      }
    }

    processEmailLink()
  }, [navigate, t])

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8 text-center">
          <div className="text-red-600 text-5xl mb-4">✕</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            {t('auth.callbackFailedTitle')}
          </h1>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => navigate('/login')}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium text-lg hover:bg-blue-700"
          >
            {t('auth.backToLogin')}
          </button>
        </div>
      </div>
    )
  }

  return <LoadingScreen message={t('auth.processingLink')} />
}