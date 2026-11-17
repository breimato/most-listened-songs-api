import { useEffect } from 'react'

import { IconClose } from './Icons'

interface ToastProps {
  message: string
  type: 'success' | 'error'
  onClose: () => void
}

export function Toast({ message, type, onClose }: ToastProps) {
  useEffect(() => {
    const timer = window.setTimeout(onClose, 5000)
    return () => window.clearTimeout(timer)
  }, [message, onClose])

  return (
    <div className={`toast toast--${type}`} role="status">
      <span className="toast__dot" aria-hidden="true" />
      <p className="toast__message">{message}</p>
      <button type="button" className="toast__close" onClick={onClose} aria-label="Cerrar aviso">
        <IconClose size={15} />
      </button>
    </div>
  )
}
