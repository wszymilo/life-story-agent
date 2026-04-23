interface ErrorFallbackProps {
  message: string
  onRetry?: () => void
  retryLabel?: string
}

export function ErrorFallback({ message, onRetry, retryLabel = 'Try Again' }: ErrorFallbackProps) {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="text-center max-w-md">
        <p className="text-red-600 text-lg mb-4" role="alert">{message}</p>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="px-6 py-3 min-h-12 bg-blue-600 text-white text-lg rounded-lg font-medium hover:bg-blue-700"
          >
            {retryLabel}
          </button>
        )}
      </div>
    </div>
  )
}
