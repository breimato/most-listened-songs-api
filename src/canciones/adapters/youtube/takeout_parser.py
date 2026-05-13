import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from canciones.domain.models import ListeningEvent, Platform, PlatformSong


def _extract_video_id(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        return parse_qs(parsed.query).get("v", [None])[0]
    if parsed.hostname == "youtu.be":
        return parsed.path.lstrip("/")
    return None


# Matches each watch-history entry block in Takeout HTML
_ENTRY_RE = re.compile(
    r'<a href="(https://(?:www\.)?youtube\.com/watch\?[^"]+)">([^<]+)</a>'
    r'(?:.*?<a href="[^"]*">([^<]+)</a>)?'
    r'.*?(\d{1,2}\s+\w+\.?\s+\d{4},?\s+\d{1,2}:\d{2}:\d{2}[^<\n]{0,30})',
    re.DOTALL,
)

# Regex for the content-cell blocks to avoid cross-entry matches
_CELL_RE = re.compile(
    r'<div class="content-cell[^"]*">(.*?)</div>',
    re.DOTALL,
)

# Spanish and English month abbreviation maps
_ES_MONTHS = {
    "ene": "Jan", "feb": "Feb", "mar": "Mar", "abr": "Apr",
    "may": "May", "jun": "Jun", "jul": "Jul", "ago": "Aug",
    "sep": "Sep", "oct": "Oct", "nov": "Nov", "dic": "Dec",
}

_DATE_FMTS = [
    "%d %b %Y, %H:%M:%S",
    "%b %d, %Y, %I:%M:%S %p",
    "%d %b. %Y, %H:%M:%S",
]


def _parse_date(raw: str) -> datetime | None:
    # Strip timezone suffix and non-breaking spaces
    raw = raw.replace("\u00a0", " ").replace("\xa0", " ").strip()
    # Remove timezone label (CET, UTC, GMT+2, etc.)
    raw = re.sub(r"\s+(GMT[+-]\d+|\w{2,5})$", "", raw).strip()
    # Remove AM/PM suffix for 24h formats
    cleaned = re.sub(r"\s*[ap]\.\s*m\.\s*$", "", raw, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"\s*[AP]M$", "", cleaned).strip()

    # Translate Spanish month abbreviations
    for es, en in _ES_MONTHS.items():
        cleaned = re.sub(rf"\b{es}\.?\b", en, cleaned, flags=re.IGNORECASE)

    for fmt in _DATE_FMTS:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
    return None


class YouTubeTakeoutParser:
    """Parses Google Takeout watch history in both JSON and HTML formats."""

    def parse(self, file_path: str) -> list[tuple[PlatformSong, ListeningEvent]]:
        path = Path(file_path)
        content = path.read_text(encoding="utf-8")

        if path.suffix.lower() == ".json":
            return self._parse_json(content)
        return self._parse_html(content)

    def _parse_json(self, content: str) -> list[tuple[PlatformSong, ListeningEvent]]:
        data = json.loads(content)
        results = []

        for entry in data:
            if entry.get("header") != "YouTube":
                continue

            url = entry.get("titleUrl", "")
            video_id = _extract_video_id(url) if url else None
            if not video_id:
                continue

            raw_title = entry.get("title", "")
            title = re.sub(r"^(?:Watched|Has visto)\s+", "", raw_title)

            channel = ""
            subtitles = entry.get("subtitles", [])
            if subtitles:
                channel = subtitles[0].get("name", "")

            time_str = entry.get("time", "")
            try:
                listened_at = datetime.fromisoformat(
                    time_str.replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                continue

            song = PlatformSong(
                platform=Platform.YOUTUBE,
                platform_id=video_id,
                title=title,
                channel=channel,
            )
            event = ListeningEvent(
                listened_at=listened_at,
                platform=Platform.YOUTUBE,
            )
            results.append((song, event))

        return results

    def _parse_html(self, content: str) -> list[tuple[PlatformSong, ListeningEvent]]:
        results = []

        for cell_match in _CELL_RE.finditer(content):
            cell = cell_match.group(1)

            # Must contain a YouTube watch URL
            url_match = re.search(
                r'href="(https://(?:www\.)?youtube\.com/watch\?[^"]+)"', cell
            )
            if not url_match:
                continue

            video_id = _extract_video_id(url_match.group(1))
            if not video_id:
                continue

            # Title is the text of the first link
            title_match = re.search(r'<a href="[^"]+">([^<]+)</a>', cell)
            title = title_match.group(1).strip() if title_match else ""
            title = re.sub(r"^(?:Watched|Has visto)\s+", "", title)

            # Channel is the second link (if any)
            channel = ""
            links = re.findall(r'<a href="[^"]+">([^<]+)</a>', cell)
            if len(links) > 1:
                channel = links[1].strip()

            # Date is the last text node after stripping tags
            text_only = re.sub(r"<[^>]+>", " ", cell)
            text_only = re.sub(r"\s+", " ", text_only).strip()
            # The date is usually at the end
            date_match = re.search(
                r'(\d{1,2}[\s\w]+\d{4}[,\s]+\d{1,2}:\d{2}:\d{2}.{0,20})$',
                text_only
            )
            if not date_match:
                continue

            listened_at = _parse_date(date_match.group(1))
            if not listened_at:
                continue

            song = PlatformSong(
                platform=Platform.YOUTUBE,
                platform_id=video_id,
                title=title,
                channel=channel,
            )
            event = ListeningEvent(
                listened_at=listened_at,
                platform=Platform.YOUTUBE,
            )
            results.append((song, event))

        return results
