"""Explora la carpeta Takeout en Drive y lista su contenido."""
from canciones.adapters.google_drive.auth import get_google_credentials
from googleapiclient.discovery import build

creds = get_google_credentials()
service = build("drive", "v3", credentials=creds)

# Encontrar la carpeta Takeout
folders = service.files().list(
    q="name = 'Takeout' and mimeType = 'application/vnd.google-apps.folder'",
    fields="files(id, name, parents)",
).execute().get("files", [])

print(f"Carpetas 'Takeout' encontradas: {len(folders)}")
for folder in folders:
    print(f"  ID: {folder['id']}  Nombre: {folder['name']}")

    # Listar contenido primer nivel
    children = service.files().list(
        q=f"'{folder['id']}' in parents",
        fields="files(id, name, mimeType, size)",
        pageSize=50,
    ).execute().get("files", [])

    print(f"  Contenido ({len(children)} items):")
    for f in children:
        size = int(f.get("size", 0))
        print(f"    [{size:>12,} bytes] {f['name']}  ({f['mimeType']})")

        # Si es subcarpeta, listar también
        if f["mimeType"] == "application/vnd.google-apps.folder":
            sub = service.files().list(
                q=f"'{f['id']}' in parents",
                fields="files(id, name, mimeType, size)",
                pageSize=50,
            ).execute().get("files", [])
            for sf in sub:
                ssize = int(sf.get("size", 0))
                print(f"      [{ssize:>12,} bytes] {sf['name']}  ({sf['mimeType']})")
