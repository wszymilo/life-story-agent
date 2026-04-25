import { Component, ReactNode } from 'react'
import i18n from '../i18n'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-red-600 mb-4">{i18n.t('common.error')}</h1>
            <p className="text-gray-600 mb-4">{this.state.error?.message}</p>
            <p className="text-gray-500 text-sm">Please reload the page to try again.</p>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}