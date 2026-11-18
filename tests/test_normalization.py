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


def test_real_world_closer_variants():
    base = normalized_key("Joe Inoue", "Closer")
    assert normalized_key(
        "Joe Inoue", "CLOSER　-NARUTO オープニング ver.-"
    ) == base
    assert normalized_key(
        "Joe Inoue",
        "CLOSER　-NARUTO オープニング ver.- - Closer (Naruto Opening Ver.)",
    ) == base
    assert normalized_key("Joe Inoue Official English", "Closer") == base


def test_strips_platform_noise():
    base = normalize_title("Closer")
    for variant in (
        "Closer (Official Music Video)",
        "Closer (Official 4K Video)",
        "Closer [Official Audio]",
        "Closer (Lyrics)",
        "Closer // lyrics",
        "Closer (TV Size)",
        "Closer - Naruto Opening Ver.",
        "Closer (Backyard Sessions)",
    ):
        assert normalize_title(variant) == base, variant


def test_keeps_spanish_con_titles():
    # "Con" at the start is a preposition, not a feature credit.
    assert normalize_title("Con La Luna Llena") == "con la luna llena"
    assert normalize_title("Con Sólo Una Sonrisa") == "con solo una sonrisa"
    assert normalize_title("Nada Con Nadie") == "nada con nadie"
    assert normalize_title("With or Without You") == "with or without you"


def test_strips_channel_suffixes():
    assert normalize_artist("Joe Inoue Official English") == "joe inoue"
    assert normalize_artist("Joe Inoue - Topic") == "joe inoue"
    assert normalize_artist("NICO Touches the Walls Official YouTube Channel") == (
        "nico touches the walls"
    )
    assert normalize_artist("Akon - Topic") == "akon"


def test_features_are_part_of_the_key_only_when_present():
    first = normalized_key("Justin Bieber", "Holy (con Chance The Rapper)")
    second = normalized_key("Justin Bieber", "Holy (Acoustic) ft. Chance The Rapper")
    assert first == second
    assert normalized_key("Justin Bieber", "Holy") != first

    neoni = normalized_key("EGZOD", "Royalty (con Neoni)")
    eke = normalized_key("EGZOD", "Royalty (con EKE)")
    assert neoni != eke


def test_unbalanced_brackets_are_ignored():
    assert normalize_title("Into Your Arms (Remix (Tiktok)2020") == (
        "into your arms"
    )
    assert normalize_title("Song (Live") == "song"


def test_different_episodes_stay_apart():
    assert normalize_title("Capítulo 1. El niño que vivió") != normalize_title(
        "Capítulo 2. El vidrio que se desvaneció"
    )
    assert normalize_title("Ending 2 (Castellano) 4K") != normalize_title(
        "Opening 2 (Castellano) 4K"
    )
    assert normalize_title(
        "Quevedo: Bzrp Music Sessions, Vol. 52/66"
    ) != normalize_title("Daddy Yankee: Bzrp Music Sessions, Vol. 0/66")
