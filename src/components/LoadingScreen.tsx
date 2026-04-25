import { useTranslation } from 'react-i18next'

interface LoadingScreenProps {
  message?: string
}

export function LoadingScreen({ message: messageProp = '' }: LoadingScreenProps) {
  const { t } = useTranslation()
  const message = messageProp || t('common.loading')
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center" role="status" aria-live="polite">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" aria-hidden="true" />
        <p className="text-gray-600 text-lg">{message}</p>
      </div>
    </div>
  )
}
