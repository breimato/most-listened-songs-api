import { useSync } from '../hooks/useCanciones'
import { IconSync } from './Icons'

interface SyncButtonProps {
  onMessage: (message: string, type: 'success' | 'error') => void
  compact?: boolean
}

export function SyncButton({ onMessage }: SyncButtonProps) {
  const sync = useSync()

  const handleClick = () => {
    sync.mutate(undefined, {
      onSuccess: (data) => onMessage(data.message, 'success'),
      onError: (error) =>
        onMessage(
          error instanceof Error ? error.message : 'Error al sincronizar',
          'error',
        ),
    })
  }

  return (
    <button
      type="button"
      className={`sync-btn${sync.isPending ? ' is-pending' : ''}`}
      onClick={handleClick}
      disabled={sync.isPending}
    >
      {sync.isPending ? <span className="spinner" aria-hidden="true" /> : <IconSync size={17} />}
      <span>{sync.isPending ? 'Sincronizando' : 'Sincronizar'}</span>
    </button>
  )
}
