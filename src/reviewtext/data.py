"""Download and load Inside Airbnb files. Reviewer names and ids are never loaded."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd
import requests

CITY = "united-states/ca/san-francisco"
SNAPSHOT = "2026-09-14"
BASE = f"https://data.insideairbnb.com/{CITY}/{SNAPSHOT}/data"
RAW = Path("data/raw")

SCORES = [
    "review_scores_rating", "review_scores_accuracy", "review_scores_cleanliness",
    "review_scores_checkin", "review_scores_communication", "review_scores_location",
    "review_scores_value",
]

_EN_STOP = set(
    "the and a to was is in it of for with we i you this my our very great place "
    "stay host would again were had at but they there are be as so all from".split()
)
_TOKEN = re.compile(r"[a-z']+")
_TAG = re.compile(r"<[^>]+>")


def download(snapshot: str = SNAPSHOT) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    for name in ("reviews", "listings"):
        out = RAW / f"{name}.csv.gz"
        if out.exists():
            continue
        url = f"{BASE.replace(SNAPSHOT, snapshot)}/{name}.csv.gz"
        with requests.get(url, stream=True, timeout=120,
                          headers={"User-Agent": "review-text-study (research script)"}) as r:
            r.raise_for_status()
            with open(out, "wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
        print(f"{url} -> {out}")


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", _TAG.sub(" ", str(text))).strip()


def is_english(text: str, min_tokens: int = 5, min_stop_share: float = 0.15) -> bool:
    """Cheap language filter: share of tokens that are common English function words."""
    toks = _TOKEN.findall(text.lower())
    if len(toks) < min_tokens:
        return False
    return sum(t in _EN_STOP for t in toks) / len(toks) >= min_stop_share


def load_reviews() -> pd.DataFrame:
    df = pd.read_csv(RAW / "reviews.csv.gz", usecols=["listing_id", "id", "date", "comments"])
    df = df.dropna(subset=["comments"])
    df["text"] = df["comments"].map(clean)
    df = df.drop(columns="comments")
    # system messages posted by Airbnb on cancellation are not guest reviews
    df = df[~df["text"].str.contains("This is an automated posting", regex=False)]
    df["english"] = df["text"].map(is_english)
    return df


def load_listings() -> pd.DataFrame:
    return pd.read_csv(RAW / "listings.csv.gz", usecols=["id", "number_of_reviews", *SCORES])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", default=SNAPSHOT)
    download(ap.parse_args().snapshot)
