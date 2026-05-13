import io
import zipfile
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from canciones.adapters.google_drive.auth import get_google_credentials
from canciones.config import settings


class GoogleDriveSync:
    """Detects and downloads Google Takeout exports from Google Drive."""

    def __init__(self):
        self._service = None

    @property
    def service(self):
        if self._service is None:
            creds = get_google_credentials()
            self._service = build("drive", "v3", credentials=creds)
        return self._service

    def find_takeout_files(self) -> list[dict]:
        query = (
            "name contains 'takeout' and ("
            "mimeType = 'application/zip' or mimeType = 'application/x-zip'"
            ")"
        )
        results = (
            self.service.files()
            .list(
                q=query,
                spaces="drive",
                fields="files(id, name, createdTime, size)",
                orderBy="createdTime desc",
                pageSize=20,
            )
            .execute()
        )
        files = results.get("files", [])
        # Sort largest first — the small 001.zip is just the index page
        return sorted(files, key=lambda f: int(f.get("size", 0)), reverse=True)

    def download_and_extract(self, file_id: str, dest_dir: str) -> str | None:
        request = self.service.files().get_media(fileId=file_id)
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        buffer.seek(0)
        dest_path = Path(dest_dir)
        dest_path.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(buffer) as zf:
            # Look for watch/playback history file (English or Spanish locale)
            for name in zf.namelist():
                lower = name.lower()
                is_history = (
                    "watch-history" in lower
                    or "historial-de-reproducciones" in lower
                )
                if is_history and name.endswith((".json", ".html")):
                    zf.extract(name, dest_path)
                    return str(dest_path / name)

        return None
