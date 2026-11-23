import { useState } from 'react'
import type { FormEvent } from 'react'

import { checkAccess } from '../services/api'
import { IconEye, IconEyeOff, IconKey, IconLock } from './Icons'

interface AccessGateProps {
  onUnlock: (key: string, remember: boolean) => void
}

export function AccessGate({ onUnlock }: AccessGateProps) {
  const [value, setValue] = useState('')
  const [remember, setRemember] = useState(true)
  const [show, setShow] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const key = value.trim()
    if (!key) {
      setError('Escribe la llave de acceso.')
      return
    }

    setLoading(true)
    setError('')
    try {
      const valid = await checkAccess(key)
      if (!valid) {
        setError('Llave incorrecta. Inténtalo de nuevo.')
        return
      }
      onUnlock(key, remember)
    } catch {
      setError('No se pudo conectar con el servidor. Revisa tu conexión.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="gate">
      <div className="gate__glow" aria-hidden="true" />

      <main className="gate__card">
        <div className="gate__brand">
          <span className="gate__mark" aria-hidden="true">
            <i />
            <i />
            <i />
            <i />
          </span>
          <span className="gate__name">GroBeats FM</span>
          <span className="gate__sub">Tu historial musical</span>
        </div>

        <span className="gate__lock" aria-hidden="true">
          <IconLock size={22} />
        </span>

        <h1 className="gate__title">Tu música, para tus ojos</h1>
        <p className="gate__lead">
          Introduce la llave de acceso para entrar en tu historial.
        </p>

        <form className="gate__form" onSubmit={handleSubmit}>
          <label className="gate__field">
            <IconKey size={17} className="gate__field-icon" />
            <span className="visually-hidden">Llave de acceso</span>
            <input
              type={show ? 'text' : 'password'}
              value={value}
              onChange={(event) => setValue(event.target.value)}
              placeholder="Llave de acceso"
              autoFocus
              autoComplete="current-password"
              autoCapitalize="none"
              spellCheck={false}
            />
            <button
              type="button"
              className="gate__reveal"
              onClick={() => setShow((visible) => !visible)}
              aria-label={show ? 'Ocultar llave' : 'Mostrar llave'}
            >
              {show ? <IconEyeOff size={17} /> : <IconEye size={17} />}
            </button>
          </label>

          <label className="gate__remember">
            <input
              type="checkbox"
              checked={remember}
              onChange={(event) => setRemember(event.target.checked)}
            />
            Mantener la sesión en este dispositivo
          </label>

          {error ? (
            <p className="gate__error" role="alert">
              {error}
            </p>
          ) : null}

          <button type="submit" className="btn btn--primary gate__submit" disabled={loading}>
            {loading ? 'Comprobando…' : 'Entrar'}
          </button>
        </form>

        <p className="gate__foot">
          La llave se guarda solo en este navegador. Tus datos siguen en tu cluster.
        </p>
      </main>
    </div>
  )
}
