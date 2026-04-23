import { ReactNode } from 'react'
import { TopBar } from './TopBar'

interface ScreenLayoutProps {
  children: ReactNode
  title?: string
  back?: { href: string }
  primary?: { label: string; onClick: () => void; loading?: boolean }
  secondary?: { label: string; onClick: () => void }
  destructive?: { label: string; onClick: () => void; loading?: boolean }
  tertiaryLeft?: ReactNode
}

export function ScreenLayout({
  children,
  title,
  back,
  primary,
  secondary,
  destructive,
  tertiaryLeft,
}: ScreenLayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <TopBar
        title={title ?? ''}
        back={back}
        primary={primary}
        secondary={secondary}
        destructive={destructive}
        tertiaryLeft={tertiaryLeft}
      />
      <div className="max-w-2xl mx-auto p-4">{children}</div>
    </div>
  )
}
