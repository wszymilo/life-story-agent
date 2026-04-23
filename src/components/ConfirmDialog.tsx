import { useEffect, useRef } from 'react'

interface ConfirmDialogProps {
  open: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  destructive?: boolean
  loading?: boolean
}

export function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  destructive = false,
  loading = false,
}: ConfirmDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return

    if (open && !dialog.open) {
      dialog.showModal()
    } else if (!open && dialog.open) {
      dialog.close()
    }
  }, [open])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && open) {
        e.preventDefault()
        onClose()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [open, onClose])

  const handleOverlayClick = (e: React.MouseEvent<HTMLDialogElement>) => {
    if (e.target === dialogRef.current) {
      onClose()
    }
  }

  return (
    <dialog
      ref={dialogRef}
      onClick={handleOverlayClick}
      className="backdrop:bg-black/50 p-0 m-auto rounded-xl border-0"
      aria-labelledby="dialog-title"
      aria-describedby="dialog-message"
    >
      <div className="bg-white rounded-xl p-6 max-w-md w-full">
        <h2
          id="dialog-title"
          className="text-xl font-semibold text-gray-900 mb-2"
        >
          {title}
        </h2>
        <p
          id="dialog-message"
          className="text-gray-600 mb-6 text-lg"
        >
          {message}
        </p>
        <div className="flex flex-col gap-3">
          <button
            type="button"
            onClick={onConfirm}
            disabled={loading}
            className={`w-full py-3 min-h-12 text-lg rounded-lg font-medium disabled:opacity-50 ${
              destructive
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
          >
            {loading ? 'Processing...' : confirmLabel}
          </button>
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="w-full py-3 min-h-12 text-lg rounded-lg font-medium bg-gray-200 hover:bg-gray-300 text-gray-700 disabled:opacity-50"
          >
            {cancelLabel}
          </button>
        </div>
      </div>
    </dialog>
  )
}