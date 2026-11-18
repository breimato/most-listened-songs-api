"""Búsqueda de carátulas en Deezer desde el servidor (sin CORS ni scripts de terceros)."""

import json
import re
import time
import unicodedata
import urllib.parse
import urllib.request

from canciones.config import settings

_API = "https://api.deezer.com/search"
_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/130 Safari/537.36"
_CACHE: dict[str, tuple[float, str | None]] = {}
_DURATION_CACHE: dict[str, tuple[float, int | None]] = {}
_TTL = 60 * 60 * 24 * 30
_MAX_ENTRIES = 2000


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFD", (value or "").lower())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^a-z0-9 ]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _overlap(left: str, right: str) -> float:
    a = set(_normalize(left).split())
    b = set(_normalize(right).split())
    if not a or not b:
        return 0
    return len(a & b) / max(len(a), len(b))


def _match(candidate_artist, candidate_title, artist, title) -> bool:
    artist_ok = (
        _overlap(candidate_artist, artist) >= 0.6
        or _normalize(artist) in _normalize(candidate_artist)
        or _normalize(candidate_artist) in _normalize(artist)
    )
    title_ok = (
        _overlap(candidate_title, title) >= 0.6
        or _normalize(candidate_title) == _normalize(title)
        or _normalize(candidate_title).startswith(_normalize(title))
    )
    return bool(artist_ok and title_ok)


def find_cover(artist: str, title: str) -> str | None:
    key = f"{_normalize(artist)}|{_normalize(title)}"
    if not key.strip("|"):
        return None

    cached = _CACHE.get(key)
    if cached:
        ttl = _TTL if cached[1] else 60 * 60 * 6
        if time.time() - cached[0] < ttl:
            return cached[1]

    url = None
    try:
        query = urllib.parse.urlencode({"q": f"{artist} {title}", "limit": 5})
        request = urllib.request.Request(
            f"{_API}?{query}", headers={"User-Agent": _UA}
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
        for item in data.get("data", []):
            if _match(
                item.get("artist", {}).get("name", ""),
                item.get("title", ""),
                artist,
                title,
            ):
                album = item.get("album", {})
                url = (
                    album.get("cover_xl")
                    or album.get("cover_big")
                    or album.get("cover_medium")
                )
                if url:
                    break
    except Exception:
        url = None

    if len(_CACHE) > _MAX_ENTRIES:
        _CACHE.clear()
    _CACHE[key] = (time.time(), url)
    return url


def find_duration(artist: str, title: str) -> int | None:
    """Duración en segundos: Deezer y, si falla, Last.fm track.getInfo."""
    key = f"{_normalize(artist)}|{_normalize(title)}"
    if not key.strip("|"):
        return None

    cached = _DURATION_CACHE.get(key)
    if cached:
        ttl = _TTL if cached[1] else 60 * 60 * 6
        if time.time() - cached[0] < ttl:
            return cached[1]

    seconds = None
    try:
        query = urllib.parse.urlencode({"q": f"{artist} {title}", "limit": 5})
        request = urllib.request.Request(
            f"{_API}?{query}", headers={"User-Agent": _UA}
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
        for item in data.get("data", []):
            if _match(
                item.get("artist", {}).get("name", ""),
                item.get("title", ""),
                artist,
                title,
            ):
                duration = item.get("duration")
                if duration:
                    seconds = int(duration)
                    break
    except Exception:
        seconds = None

    if not seconds and settings.lastfm_api_key:
        try:
            params = {
                "method": "track.getInfo",
                "artist": artist,
                "track": title,
                "api_key": settings.lastfm_api_key,
                "format": "json",
            }
            url = "https://ws.audioscrobbler.com/2.0/?" + urllib.parse.urlencode(params)
            with urllib.request.urlopen(url, timeout=8) as response:
                data = json.loads(response.read().decode("utf-8"))
            millis = data.get("track", {}).get("duration")
            if millis:
                seconds = int(millis) // 1000
        except Exception:
            seconds = None

    if len(_DURATION_CACHE) > _MAX_ENTRIES:
        _DURATION_CACHE.clear()
    _DURATION_CACHE[key] = (time.time(), seconds)
    return seconds
