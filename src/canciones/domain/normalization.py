"""Normalize song titles/artists so different versions of the same track group together.

Handles common variations that Last.fm/Spotify/YouTube introduce for the same song:
casing, accents, feat. credits, and suffixes like (Remastered), - Live, (Remix), etc.
"""

import re
import unicodedata

# Suffixes/parentheticals that mark a variation of the *same* song.
# Matched case-insensitively; anything from the keyword to the end of that segment is stripped.
_VERSION_KEYWORDS = (
    "remaster",
    "remastered",
    "remasterizado",
    "remasterizada",
    "remix",
    "mix",
    "radio edit",
    "radio version",
    "single version",
    "album version",
    "extended",
    "deluxe",
    "bonus track",
    "live",
    "en vivo",
    "en directo",
    "acoustic",
    "acustico",
    "unplugged",
    "version",
    "versión",
    "mono",
    "stereo",
    "anniversary",
    "aniversario",
)

# Segments wrapped in () or [] whose content starts with a version keyword get dropped.
_BRACKET_RE = re.compile(r"[\(\[]([^\)\]]*)[\)\]]")

# "feat." / "ft." / "featuring" credits, including a leading dash or bracket.
_FEAT_RE = re.compile(
    r"\s*[\(\[]?\s*(?:feat|ft|featuring|con|with)\.?\s+.*$",
    re.IGNORECASE,
)

# Trailing " - <version keyword> ..." after a dash separator.
_DASH_VERSION_RE = re.compile(
    r"\s*-\s*.*(?:" + "|".join(re.escape(k) for k in _VERSION_KEYWORDS) + r").*$",
    re.IGNORECASE,
)

_WHITESPACE_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^\w\s]")


def _strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _drop_version_brackets(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        inner = match.group(1).strip().lower()
        inner = _strip_accents(inner)
        if any(inner.startswith(kw) or kw in inner for kw in _VERSION_KEYWORDS):
            return " "
        return match.group(0)

    return _BRACKET_RE.sub(repl, text)


def normalize_title(title: str) -> str:
    """Reduce a title to a canonical key shared by its variations.

    Example: "Closer (Remix)", "Closer - Remastered 2011", "closer" -> "closer".
    """
    text = title or ""
    text = _drop_version_brackets(text)
    text = _FEAT_RE.sub("", text)
    text = _DASH_VERSION_RE.sub("", text)
    text = _strip_accents(text).lower()
    text = _PUNCT_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text


def normalize_artist(artist: str) -> str:
    """Canonical key for an artist name (casing/accents/punctuation-insensitive).

    Uses only the primary artist, dropping "feat." collaborators.
    """
    text = artist or ""
    text = _FEAT_RE.sub("", text)
    text = _strip_accents(text).lower()
    text = _PUNCT_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text


def normalized_key(artist: str, title: str) -> str:
    """Combined grouping key for a song across its versions."""
    return f"{normalize_artist(artist)}|{normalize_title(title)}"
