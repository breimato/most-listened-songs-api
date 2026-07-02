from canciones.domain.normalization import (
    normalize_artist,
    normalize_title,
    normalized_key,
)


def test_casing_and_accents():
    assert normalize_title("Corazón") == normalize_title("corazon")
    assert normalize_artist("Beyoncé") == normalize_artist("beyonce")


def test_strips_remaster_and_remix_suffixes():
    base = normalize_title("Closer")
    assert normalize_title("Closer (Remix)") == base
    assert normalize_title("Closer - Remastered 2011") == base
    assert normalize_title("Closer [Radio Edit]") == base
    assert normalize_title("Closer - Live") == base


def test_strips_feat_credits():
    assert normalize_title("Song (feat. Someone)") == normalize_title("Song")
    assert normalize_artist("Drake feat. Rihanna") == normalize_artist("Drake")


def test_keeps_genuinely_different_titles_apart():
    assert normalize_title("Closer") != normalize_title("Farther")


def test_normalized_key_groups_versions():
    key_a = normalized_key("Joe Inoue", "Closer")
    key_b = normalized_key("Joe Inoue", "Closer (Remix)")
    key_c = normalized_key("joe inoue", "CLOSER - Remastered")
    assert key_a == key_b == key_c
