"""Géneros aproximados a partir de los tags de artista de Last.fm."""

import json
import time
import urllib.parse
import urllib.request
from collections import Counter

from canciones.config import settings

_API_BASE = "https://ws.audioscrobbler.com/2.0/"
_CACHE: dict[str, tuple[float, list[str]]] = {}
_TTL = 60 * 60 * 24 * 7

_GENERIC = {
    "seen live",
    "favorites",
    "favourite",
    "favourites",
    "spotify",
    "love",
    "loved",
    "awesome",
    "beautiful",
    "chill",
    "female vocalists",
    "male vocalists",
    "under 2000 listeners",
    "albums i own",
    "i own",
    "my music",
    "music",
    "all",
    "other",
    "unknown",
}

_TAG_CASE = {
    "idm": "IDM",
    "edm": "EDM",
    "r&b": "R&B",
    "dnb": "DnB",
    "uk garage": "UK Garage",
    "k-pop": "K-Pop",
    "j-pop": "J-Pop",
    "j-rock": "J-Rock",
    "hip-hop": "Hip-Hop",
}


def _normalize_tag(name: str) -> str:
    return name.strip().lower()


def artist_tags(artist: str) -> list[str]:
    key = artist.strip().lower()
    if not key:
        return []

    cached = _CACHE.get(key)
    if cached and time.time() - cached[0] < _TTL:
        return cached[1]

    if not settings.lastfm_api_key:
        return []

    params = {
        "method": "artist.getTopTags",
        "artist": artist,
        "api_key": settings.lastfm_api_key,
        "format": "json",
    }
    try:
        url = _API_BASE + "?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
        tags = data.get("toptags", {}).get("tag", [])
        names: list[str] = []
        for tag in tags:
            name = (tag.get("name") or "").strip()
            if not name or _normalize_tag(name) in _GENERIC:
                continue
            pretty = _TAG_CASE.get(name.lower(), name.title())
            if pretty not in names:
                names.append(pretty)
        _CACHE[key] = (time.time(), names)
        return names
    except Exception:
        _CACHE[key] = (time.time(), [])
        return []


def build_genres(artists: list[tuple[str, int]], limit: int = 6) -> list[dict]:
    weights: Counter[str] = Counter()
    for artist, plays in artists[:6]:
        for index, tag in enumerate(artist_tags(artist)[:3]):
            weights[tag] += max(1, plays) * (3 - index)

    total = sum(weights.values()) or 1
    return [
        {
            "name": name,
            "weight": weight,
            "share": round(weight / total, 3),
        }
        for name, weight in weights.most_common(limit)
    ]
