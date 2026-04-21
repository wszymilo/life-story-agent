import { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'

interface TopBarAction {
  label: string
  onClick: () => void
  loading?: boolean
}

interface TopBarBack {
  href?: string
  action?: () => void
}

interface TopBarProps {
  title?: string
  back?: TopBarBack
  destructive?: TopBarAction
  primary?: TopBarAction
  secondary?: TopBarAction
  tertiaryLeft?: ReactNode
  tertiaryRight?: ReactNode
  children?: ReactNode
}

export function TopBar({
  title,
  back,
  destructive,
  primary,
  secondary,
  tertiaryLeft,
  tertiaryRight,
  children,
}: TopBarProps) {
  const navigate = useNavigate()

  const handleBack = () => {
    if (back?.href) {
      navigate(back.href)
    } else if (back?.action) {
      back.action()
    }
  }

  const hasBack = !!back
  const hasRightButtons = !!destructive || !!primary || !!secondary || !!tertiaryRight
  const hasLeftButtons = hasBack || !!tertiaryLeft

  const centerTitle = hasLeftButtons && hasRightButtons

  return (
    <div className="sticky top-0 z-50 bg-white shadow-sm px-4 py-3">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between min-h-12">
          {/* Left side */}
          <div className="flex items-center gap-2">
            {hasBack && (
              <button
                onClick={handleBack}
                className="flex items-center gap-1 px-4 py-3 min-h-12 bg-gray-200 hover:bg-gray-300 text-gray-700 text-lg rounded-lg font-medium"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 19l-7-7 7-7"
                  />
                </svg>
                Back
              </button>
            )}
            {tertiaryLeft}
          </div>

          {/* Center title */}
          {title && (
            <h1
              className={`text-xl font-semibold text-gray-900 ${
                centerTitle ? 'absolute left-1/2 -translate-x-1/2' : ''
              }`}
            >
              {title}
            </h1>
          )}

          {/* Right side */}
          <div className="flex items-center gap-2">
            {secondary && (
              <button
                onClick={secondary.onClick}
                disabled={secondary.loading}
                className="px-4 py-3 min-h-12 bg-gray-200 hover:bg-gray-300 text-gray-700 text-lg rounded-lg font-medium disabled:opacity-50"
              >
                {secondary.loading ? '...' : secondary.label}
              </button>
            )}
            {primary && (
              <button
                onClick={primary.onClick}
                disabled={primary.loading}
                className="px-4 py-3 min-h-12 bg-blue-600 hover:bg-blue-700 text-white text-lg rounded-lg font-medium disabled:opacity-50"
              >
                {primary.loading ? '...' : primary.label}
              </button>
            )}
            {destructive && (
              <button
                onClick={destructive.onClick}
                disabled={destructive.loading}
                className="px-4 py-3 min-h-12 bg-red-600 hover:bg-red-700 text-white text-lg rounded-lg font-medium disabled:opacity-50"
              >
                {destructive.loading ? '...' : destructive.label}
              </button>
            )}
            {tertiaryRight}
          </div>
        </div>

        {/* Custom content below buttons */}
        {children}
      </div>
    </div>
  )
}