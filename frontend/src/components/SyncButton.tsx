import { useSync } from '../hooks/useCanciones'

interface SyncButtonProps {
  onMessage: (message: string, type: 'success' | 'error') => void
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
      className="sync-button"
      onClick={handleClick}
      disabled={sync.isPending}
    >
      {sync.isPending ? (
        <>
          <span className="spinner" aria-hidden="true" />
          Sincronizando…
        </>
      ) : (
        <>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path
              d="M21 12a9 9 0 0 0-9-9 8.96 8.96 0 0 0-6.36 2.64M3 12a9 9 0 0 0 9 9 8.96 8.96 0 0 0 6.36-2.64M3 3v6h6M21 21v-6h-6"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          Sincronizar Last.fm
        </>
      )}
    </button>
  )
}
