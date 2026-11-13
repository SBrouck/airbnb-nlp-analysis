from reviewtext.data import clean, is_english
from reviewtext.scoring import AC_RE, aspect_flags, legacy_mentions_ac


def test_aspect_lexicons_match_on_word_boundaries():
    texts = ["The sheets had a stain and the bathroom was dirty.",
             "Lovely stay, the host was very responsive.",  # 'unresponsive' must not match here
             "Host was unresponsive for two days.",
             "Felt unsafe walking back at night."]
    f = aspect_flags(texts)
    assert f["cleanliness"].tolist() == [True, False, False, False]
    assert f["communication"].tolist() == [False, False, True, False]
    assert f["location"].tolist() == [False, False, False, True]


def test_legacy_ac_rule_is_a_substring_match():
    text = "Great place, we came back and would stay again."
    assert legacy_mentions_ac(text)          # matches 'ac' inside 'place' and 'back'
    assert AC_RE.search(text) is None        # the word-boundary rule does not
    assert AC_RE.search("The AC worked well.")


def test_language_filter_and_cleaning():
    assert is_english("We loved the place and the host was great to us")
    assert not is_english("Très bel appartement, hôte très sympathique, je recommande")
    assert clean("Nice<br/>  stay") == "Nice stay"
