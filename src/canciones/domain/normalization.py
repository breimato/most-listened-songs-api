"""Canonical song identity across platform/title variations.

Last.fm scrobbles can carry the same recording under many titles: YouTube-style
suffixes ("Official Video", "TV Size", "Naruto Opening Ver."), Spanish/English
feature credits, channel names ("- Topic", "Official English"), duplicated
title segments, unbalanced brackets, full-width characters, etc.

The helpers here reduce all of that to a stable key. When the key alone is not
enough, :func:`songs_match` adds a conservative fuzzy comparison. Both are used
by the repository to merge existing duplicates and to attach new scrobbles to
the song row they belong to.
"""

import re
import unicodedata
from difflib import SequenceMatcher

# Words that describe a version or platform decoration, not a different song.
# Matched as whole words so "mixed" is not treated as "mix".
_VERSION_WORDS = (
    "remaster",
    "remastered",
    "remasterizada",
    "remasterizado",
    "remix",
    "mix",
    "rework",
    "flip",
    "bootleg",
    "radio",
    "edit",
    "edition",
    "edición",
    "version",
    "versión",
    "ver",
    "single",
    "album",
    "extended",
    "deluxe",
    "bonus",
    "live",
    "vivo",
    "directo",
    "acoustic",
    "acústico",
    "acustico",
    "unplugged",
    "instrumental",
    "karaoke",
    "cover",
    "duet",
    "mono",
    "stereo",
    "anniversary",
    "aniversario",
    "official",
    "oficial",
    "video",
    "vídeo",
    "videoclip",
    "audio",
    "visualizer",
    "lyrics",
    "lyric",
    "letra",
    "explicit",
    "clean",
    "censored",
    "opening",
    "ending",
    "tv",
    "size",
    "short",
    "full",
    "trailer",
    "teaser",
    "promo",
    "preview",
    "demo",
    "maqueta",
    "backyard",
    "director",
    "nightcore",
    "sped",
    "slowed",
    "reverb",
    "8d",
    "ost",
    "theme",
    "soundtrack",
)

_JP_NOISE = (
    "オープニング",
    "エンディング",
    "主題歌",
    "テレビサイズ",
    "TVサイズ",
    "フルサイズ",
    "日本語版",
    "英語版",
    "カバー",
    "ライブ",
    "リミックス",
    "カラオケ",
    "インスト",
    "バージョン",
)

_NOISE_RE = re.compile(
    r"\b(?:" + "|".join(map(re.escape, _VERSION_WORDS)) + r")\b",
    re.IGNORECASE,
)
_JP_NOISE_RE = re.compile("|".join(map(re.escape, _JP_NOISE)))

# Parenthetical/bracketed segments, feat credits, and trailing dash versions.
_SEGMENT_RE = re.compile(r"[\(\[]([^\)\]]*)[\)\]]")
_FEAT_BRACKET_RE = re.compile(
    r"[\(\[]\s*(?:feat|ft|featuring|con|with)\.?\s+[^\)\]]*[\)\]]",
    re.IGNORECASE,
)
_FEAT_BRACKET_CAPTURE_RE = re.compile(
    r"[\(\[]\s*(?:feat|ft|featuring|con|with)\.?\s+([^\)\]]*)[\)\]]",
    re.IGNORECASE,
)
_FEAT_TAIL_RE = re.compile(r"\s+(?:feat|ft|featuring)\.?\s+.+$", re.IGNORECASE)
_FEAT_CAPTURE_RE = re.compile(
    r"\s+(?:feat|ft|featuring)\.?\s+([^\(\[]+)",
    re.IGNORECASE,
)
_ARTIST_FEAT_TAIL_RE = re.compile(
    r"\s+(?:feat|ft|featuring|con|with)\.?\s+.+$",
    re.IGNORECASE,
)
_ARTIST_FEAT_CAPTURE_RE = re.compile(
    r"\s+(?:feat|ft|featuring|con|with)\.?\s+([^\(\[\]]+)",
    re.IGNORECASE,
)

_CHANNEL_SUFFIX_RE = re.compile(
    r"\s*(?:[-–—]\s*)?"
    r"(?:official"
    r"(?:\s+(?:youtube|music|video|audio|channel|artist|english|spanish|español|topic))*"
    r"|vevo|topic)\s*$",
    re.IGNORECASE,
)

_DASH_SPLIT_RE = re.compile(r"\s+[-–—]\s*|\s*[-–—]\s+")
_SLASH_SPLIT_RE = re.compile(r"\s*(?://|/)\s*")
_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^\w\s]")
_LEADING_TRACK_RE = re.compile(r"^\s*\d{1,3}\s*[\.\)\-]\s+")
_TRAILING_TRACK_RE = re.compile(r"\s+(?:no\.?|nº|#)\s*\d+\s*$", re.IGNORECASE)
_YEAR_RE = re.compile(r"\s*[\(\[]\s*(?:19|20)\d{2}\s*[\)\]]\s*")

_PLATFORM_NOISE_RE = re.compile(
    r"\b(?:official|oficial|video|vídeo|videoclip|audio|visualizer|lyrics|lyric|"
    r"letra|hd|4k|upscaled)\b",
    re.IGNORECASE,
)

_FEAT_CREDIT_RE = re.compile(
    r"(?:[\(\[]\s*(?:feat|ft|featuring|con|with)\b|\s(?:feat|ft|featuring)\.?\s)",
    re.IGNORECASE,
)

_STOPWORDS = {
    "the",
    "y",
    "and",
    "feat",
    "ft",
    "featuring",
    "con",
    "with",
    "x",
    "vs",
}


def _fold(text: str) -> str:
    """Compatibility folding: NFKD, no accents, curly quotes, wave dashes."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = (
        text.replace("’", "'")
        .replace("‘", "'")
        .replace("“", '"')
        .replace("”", '"')
    )
    for char in ("〜", "～", "~"):
        text = text.replace(char, " - ")
    return text


def _basic_key(text: str) -> str:
    text = _PUNCT_RE.sub(" ", _fold(text).lower())
    return _WS_RE.sub(" ", text).strip()


def _strip_unbalanced(text: str) -> str:
    """Drop from the first unmatched opening bracket to the end.

    Platform titles often come with broken brackets ("Song (Remix (Tiktok)2020").
    Keeping that tail would prevent matching even though it is pure decoration.
    """
    stack: list[int] = []
    for index, char in enumerate(text):
        if char in "([":
            stack.append(index)
        elif char in ")]" and stack:
            stack.pop()
    if stack:
        return text[: stack[0]].rstrip(" -–—")
    return text


def _noise_segment(inner: str) -> bool:
    if not inner.strip():
        return True
    return bool(_NOISE_RE.search(inner) or _JP_NOISE_RE.search(inner))


def _drop_brackets(text: str) -> str:
    text = _FEAT_BRACKET_RE.sub(" ", text)
    text = _SEGMENT_RE.sub(
        lambda match: " " if _noise_segment(match.group(1)) else match.group(0),
        text,
    )
    return text


def _drop_dash_noise(text: str) -> str:
    parts = [part.strip() for part in _DASH_SPLIT_RE.split(text) if part.strip()]
    if len(parts) <= 1:
        return text

    kept: list[str] = []
    seen: set[str] = set()
    for part in parts:
        if _NOISE_RE.search(part) or _JP_NOISE_RE.search(part):
            continue
        key = _basic_key(part)
        if key in seen:
            continue
        seen.add(key)
        kept.append(part)
    return " - ".join(kept) if kept else parts[0]


def _drop_slash_noise(text: str) -> str:
    parts = [part.strip() for part in _SLASH_SPLIT_RE.split(text) if part.strip()]
    if len(parts) <= 1:
        return text
    kept = [
        part
        for part in parts
        if not (_NOISE_RE.search(part) or _JP_NOISE_RE.search(part))
    ]
    return " ".join(kept) if kept else parts[0]


def _strip_channel_suffix(artist: str) -> str:
    text = artist
    for _ in range(3):
        stripped = _CHANNEL_SUFFIX_RE.sub("", text).strip()
        if stripped == text or not stripped:
            break
        text = stripped
    return text


def _drop_artist_segment(text: str, artist: str) -> str:
    artist_key = _basic_key(canonical_artist(artist))
    if not artist_key:
        return text

    parts = [part.strip() for part in _DASH_SPLIT_RE.split(text) if part.strip()]
    if len(parts) <= 1:
        return text

    filtered = []
    for part in parts:
        part_key = _basic_key(part)
        if (
            part_key == artist_key
            or part_key.startswith(artist_key)
            or artist_key.startswith(part_key)
        ):
            continue
        filtered.append(part)
    return " - ".join(filtered) if filtered else parts[-1]


def canonical_title(artist: str, title: str) -> str:
    """Canonical title key, using the artist to remove "Artist - Song" prefixes."""
    text = _strip_unbalanced(_fold(title))
    text = text.strip()
    text = _LEADING_TRACK_RE.sub("", text)
    text = _TRAILING_TRACK_RE.sub("", text)
    text = _YEAR_RE.sub(" ", text)
    text = _drop_brackets(text)
    text = _FEAT_TAIL_RE.sub("", text)
    text = _drop_slash_noise(text)
    text = _drop_dash_noise(text)
    text = _drop_artist_segment(text, artist)

    result = _basic_key(text)
    return result or _basic_key(title)


def canonical_artist(artist: str) -> str:
    """Canonical artist key, dropping features and channel decorations."""
    text = _strip_unbalanced(_fold(artist)).strip()
    text = _FEAT_BRACKET_RE.sub(" ", text)
    text = _ARTIST_FEAT_TAIL_RE.sub("", text)
    text = _strip_channel_suffix(text)
    text = _SEGMENT_RE.sub(
        lambda match: " " if _noise_segment(match.group(1)) else match.group(0),
        text,
    )

    result = _basic_key(text)
    return result or _basic_key(artist)


def feature_tokens(artist: str, title: str) -> set[str]:
    """Names credited as features in either the artist or the title."""
    features: set[str] = set()
    folded_title = _fold(title)
    folded_artist = _fold(artist)

    for match in _FEAT_BRACKET_CAPTURE_RE.finditer(folded_title):
        features.add(match.group(1))
    match = _FEAT_CAPTURE_RE.search(folded_title)
    if match:
        features.add(match.group(1))
    match = _ARTIST_FEAT_CAPTURE_RE.search(folded_artist)
    if match:
        features.add(match.group(1))

    tokens: set[str] = set()
    for value in features:
        words = _PUNCT_RE.sub(" ", value.lower())
        tokens.update(
            word
            for word in _WS_RE.sub(" ", words).split()
            if word not in _STOPWORDS and word not in _VERSION_WORDS
        )
    return tokens


def feature_signature(artist: str, title: str) -> str:
    return "-".join(sorted(feature_tokens(artist, title)))


def normalize_title(title: str) -> str:
    """Title-only canonical key (kept for callers without artist context)."""
    return canonical_title("", title)


def normalize_artist(artist: str) -> str:
    """Canonical artist key (casing/accents/punctuation/features/channels)."""
    return canonical_artist(artist)


def normalized_key(artist: str, title: str) -> str:
    """Combined grouping key for a song across its versions.

    Feature credits are part of the key when present: "Royalty (con Neoni)" and
    "Royalty (con EKE)" are different recordings even though the base title and
    artist match. Versions with and without a credit are reconciled by the
    repository matcher, which allows an empty feature set.
    """
    base = f"{canonical_artist(artist)}|{canonical_title(artist, title)}"
    signature = feature_signature(artist, title)
    return f"{base}|{signature}" if signature else base


def _numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+", text))


def titles_similar(first: str, second: str) -> bool:
    """Conservative fuzzy comparison for titles after canonicalization."""
    if first == second:
        return True
    if not first or not second:
        return False
    if _numbers(first) != _numbers(second):
        return False
    # Japanese/Korean titles often appear with the original script plus a
    # romanization, or only the romanization. Compare the Latin skeleton.
    first_ascii = re.sub(r"[^a-z0-9]", "", first)
    second_ascii = re.sub(r"[^a-z0-9]", "", second)
    if (
        first_ascii
        and first_ascii == second_ascii
        and first.isascii() != second.isascii()
    ):
        return True
    if first.replace(" ", "") == second.replace(" ", ""):
        return True
    # Opening 2 vs Ending 2 are different songs even when the rest matches.
    if first.split()[0] != second.split()[0]:
        return False
    return SequenceMatcher(None, first, second).ratio() >= 0.92


def songs_match(
    first_artist: str,
    first_title: str,
    second_artist: str,
    second_title: str,
) -> bool:
    """Whether two scrobbles refer to the same song.

    Requires the same canonical artist. Titles must canonicalize to the same
    string or be very similar. Feature credits conflict only when both sides
    list different artists; a solo/feat pair is considered the same recording.
    """
    if canonical_artist(first_artist) != canonical_artist(second_artist):
        return False

    first = canonical_title(first_artist, first_title)
    second = canonical_title(second_artist, second_title)
    if not first or not second:
        return False

    artist_key = canonical_artist(first_artist)
    if not artist_key and first != second:
        return False

    first_features = feature_tokens(first_artist, first_title)
    second_features = feature_tokens(second_artist, second_title)
    if first_features and second_features and not (first_features & second_features):
        return False

    if first != second and min(len(first), len(second)) < 4:
        return False

    return titles_similar(first, second)


def has_platform_noise(title: str) -> bool:
    """True for "Official Video"/"Lyrics"/"Audio" style decorations."""
    return bool(_PLATFORM_NOISE_RE.search(title or ""))


def feature_credit_count(title: str) -> int:
    """Count feature credits, used to prefer titles without duplicated credits."""
    return len(_FEAT_CREDIT_RE.findall(title or ""))
