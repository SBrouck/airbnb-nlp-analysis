"""Per-review text scores: VADER sentiment, aspect complaint lexicons, and the legacy keyword scorer."""
from __future__ import annotations

import re

import numpy as np

# Complaint lexicons, one per Airbnb sub-score. Matched on word boundaries, case-insensitive.
ASPECTS: dict[str, list[str]] = {
    "cleanliness": [
        r"dirty", r"filthy", r"unclean", r"stain(?:s|ed)?", r"dust(?:y)?", r"hairs?", r"mou?ld(?:y)?",
        r"smell(?:s|ed|y)?", r"odou?rs?", r"cockroach(?:es)?", r"roach(?:es)?", r"bed ?bugs?", r"grimy", r"not clean",
    ],
    "checkin": [
        r"locked out", r"lock ?box", r"(?:could ?n[o']t|could not|unable to) (?:get in|find|access)",
        r"wrong code", r"code (?:did ?n[o']t|didnt|did not) work", r"key (?:did ?n[o']t|didnt|did not) work",
        r"waited (?:for )?(?:an hour|hours)",
    ],
    "communication": [
        r"unresponsive", r"never (?:responded|replied|answered)", r"(?:no|zero) (?:response|reply)",
        r"(?:did ?n[o']t|didnt|did not) (?:respond|reply|answer)", r"hard to (?:reach|contact)", r"rude",
    ],
    "location": [
        r"sketchy", r"unsafe", r"(?:not|did ?n[o']t|didnt) feel safe", r"dangerous", r"needles?",
        r"break[- ]?ins?", r"car (?:was )?broken into", r"homeless(?:ness)?", r"drug(?:s| use| dealers?)",
    ],
    "accuracy": [
        r"not as (?:described|pictured|advertised)", r"misleading", r"(?:different|nothing like) (?:from |than )?the (?:photos|pictures)",
        r"photos? (?:were|are) (?:old|outdated)", r"false advertising", r"misrepresent(?:ed|ation)?",
    ],
    "value": [
        r"overpriced", r"over[- ]priced", r"not worth", r"too expensive", r"(?:poor|bad) value", r"rip[- ]?off",
        r"hidden fees?", r"cleaning fee",
    ],
}
ASPECT_RE = {k: re.compile(r"\b(?:" + "|".join(v) + r")\b", re.IGNORECASE) for k, v in ASPECTS.items()}


def aspect_flags(texts) -> dict[str, np.ndarray]:
    return {k: np.fromiter((bool(rx.search(t)) for t in texts), bool) for k, rx in ASPECT_RE.items()}


_analyzer = None


def vader_compound(texts) -> np.ndarray:
    global _analyzer
    if _analyzer is None:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

        _analyzer = SentimentIntensityAnalyzer()
    return np.fromiter((_analyzer.polarity_scores(t)["compound"] for t in texts), float)


# --- Legacy scorer of the first version of this repository, kept verbatim for comparison. ---
_LEGACY_POS = ["great", "excellent", "amazing", "wonderful", "perfect", "fantastic", "love", "enjoy",
               "beautiful", "clean", "comfortable", "convenient", "friendly", "helpful", "responsive",
               "recommend", "stay again"]
_LEGACY_NEG = ["bad", "terrible", "awful", "horrible", "dirty", "noisy", "uncomfortable", "disappointing",
               "problem", "issue", "broken", "rude", "unresponsive", "never", "avoid", "complaint"]


def legacy_keyword_score(text: str) -> float:
    """Substring keyword counts normalised by length (note: 'clean' also matches 'unclean')."""
    t = text.lower()
    pos = sum(w in t for w in _LEGACY_POS)
    neg = sum(w in t for w in _LEGACY_NEG)
    n = len(text.split())
    if n == 0:
        return 0.0
    return float(np.clip((pos - neg) / max(n, 10), -1, 1))


def legacy_mentions_ac(text: str) -> bool:
    """The legacy 'ac' amenity rule: substring match of 'ac', 'cooling', 'heating', 'air conditioning'."""
    t = text.lower()
    return any(k in t for k in ["ac", "air conditioning", "cooling", "heating"])


AC_RE = re.compile(r"\b(?:ac|a/c|air ?con(?:ditioning|ditioner)?|cooling|heating)\b", re.IGNORECASE)
