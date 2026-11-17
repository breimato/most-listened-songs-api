"""Publica la URL del quick tunnel de Youtube en breimato.es/youtube.

Escucha el journal del servicio `youtube-quick-tunnel`, verifica que el backend
responde y permite CORS desde https://breimato.es, y sube `runtime-config.json`
por FTP a SiteGround. Si la URL cambia (cada reinicio del túnel), la vuelve a
publicar automáticamente.
"""

import ftplib
import json
import os
import re
import subprocess
import time
import urllib.request
from io import BytesIO
from pathlib import Path

HOME = Path.home()
PROJECT_DIR = Path(
    os.environ.get(
        "YT_FRONTEND_DIR",
        HOME / "Escritorio" / "Mis Proyectos" / "Canciones Mas Escuchadas Youtube" / "frontend",
    )
)
TUNNEL_SERVICE = os.environ.get("YT_TUNNEL_SERVICE", "youtube-quick-tunnel")
PUBLIC_BASE = os.environ.get("YT_PUBLIC_BASE", "https://breimato.es/youtube")
STATE_FILE = Path(__file__).with_name("published-url.txt")
URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
ORIGIN = "https://breimato.es"


def load_deploy_env() -> dict[str, str]:
    env_path = PROJECT_DIR / ".env.deploy.local"
    if not env_path.exists():
        raise RuntimeError(f"Falta {env_path}")
    config: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        config[key.strip()] = value.strip()
    return config


def http(url: str, method: str = "GET", headers: dict[str, str] | None = None):
    request = urllib.request.Request(url, method=method, headers=headers or {})
    with urllib.request.urlopen(request, timeout=25) as response:
        return response.status, {k.lower(): v for k, v in response.headers.items()}, response.read()


def verify_backend(url: str) -> None:
    status, _, body = http(f"{url}/health")
    assert status == 200, f"/health devolvió {status}"
    assert json.loads(body) == {"status": "ok"}, "/health inesperado"

    status, headers, _ = http(
        f"{url}/api/v1/songs/top?limit=1",
        method="OPTIONS",
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert status == 200, f"preflight devolvió {status}"
    assert headers.get("access-control-allow-origin") == ORIGIN, "CORS no permite breimato.es"

    status, _, _ = http(f"{url}/api/v1/stats")
    assert status == 200, f"/api/v1/stats devolvió {status}"


def publish_runtime_config(url: str, config: dict[str, str]) -> None:
    payload = json.dumps({"apiUrl": url}, indent=2) + "\n"
    remote_dir = config.get("FTP_REMOTE_DIR", "").strip("/")

    client = ftplib.FTP()
    client.connect(config["FTP_HOST"], int(config.get("FTP_PORT", "21")), timeout=60)
    client.login(config["FTP_USER"], config["FTP_PASSWORD"])
    try:
        client.cwd("/")
        for part in filter(None, remote_dir.split("/")):
            try:
                client.cwd(part)
            except ftplib.error_perm:
                client.mkd(part)
                client.cwd(part)
        client.storbinary("STOR runtime-config.json", BytesIO(payload.encode("utf-8")))
    finally:
        try:
            client.quit()
        except ftplib.all_errors:
            client.close()


def verify_published(url: str) -> None:
    status, _, body = http(f"{PUBLIC_BASE}/runtime-config.json?ts={int(time.time())}")
    assert status == 200, f"runtime-config.json devolvió {status}"
    assert json.loads(body).get("apiUrl") == url, "runtime-config.json publicado no coincide"


def latest_tunnel_url() -> str | None:
    output = subprocess.check_output(
        ["journalctl", "--user", "-u", TUNNEL_SERVICE, "-n", "300", "--no-pager", "-o", "cat"],
        text=True,
    )
    urls = URL_RE.findall(output)
    return urls[-1] if urls else None


def main() -> None:
    last = STATE_FILE.read_text(encoding="utf-8").strip() if STATE_FILE.exists() else ""
    while True:
        try:
            url = latest_tunnel_url()
            if not url:
                raise RuntimeError("esperando la URL del túnel")
            if url != last:
                verify_backend(url)
                publish_runtime_config(url, load_deploy_env())
                verify_published(url)
                STATE_FILE.write_text(url, encoding="utf-8")
                last = url
                print(f"Endpoint verificado y publicado: {url}", flush=True)
        except Exception as exc:  # noqa: BLE001 - bucle de reintento
            print(f"Pendiente; reintentando: {type(exc).__name__}: {exc}", flush=True)
        time.sleep(15)


if __name__ == "__main__":
    main()
