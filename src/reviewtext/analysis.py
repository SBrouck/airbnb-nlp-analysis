"""Score reviews, aggregate per listing, and compare with listing star sub-scores."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr

from .data import SCORES, load_listings, load_reviews
from .scoring import AC_RE, ASPECTS, aspect_flags, legacy_keyword_score, legacy_mentions_ac, vader_compound

INTERIM = Path("data/interim/review_scores.csv.gz")
RESULTS = Path("results")
MIN_REVIEWS = 20
BOTTOM_QUANTILE = 0.10
N_BOOT = 1000


def score_reviews() -> pd.DataFrame:
    if INTERIM.exists():
        return pd.read_csv(INTERIM)
    df = load_reviews()
    en = df[df.english].copy()
    en["vader"] = vader_compound(en.text)
    en["legacy"] = [legacy_keyword_score(t) for t in en.text]
    for k, v in aspect_flags(en.text).items():
        en[f"cmp_{k}"] = v
    en["legacy_ac"] = [legacy_mentions_ac(t) for t in en.text]
    en["ac_word"] = [bool(AC_RE.search(t)) for t in en.text]
    en["n_words"] = en.text.str.split().str.len()
    stats = {"reviews_total": int(len(df)), "reviews_english": int(len(en))}
    INTERIM.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "corpus.json").write_text(json.dumps(stats, indent=2))
    out = en.drop(columns=["text", "english"])
    out.to_csv(INTERIM, index=False)
    return out


def listing_table(rev: pd.DataFrame) -> pd.DataFrame:
    g = rev.groupby("listing_id")
    agg = pd.DataFrame({
        "n_en_reviews": g.size(),
        "vader_mean": g.vader.mean(),
        "vader_neg_share": g.vader.apply(lambda s: (s < -0.05).mean()),
        "legacy_mean": g.legacy.mean(),
        **{f"cmp_{k}": g[f"cmp_{k}"].mean() for k in ASPECTS},
    })
    agg["cmp_any"] = rev.assign(any_=rev[[f"cmp_{k}" for k in ASPECTS]].any(axis=1)).groupby("listing_id").any_.mean()
    lst = load_listings().set_index("id")
    t = agg.join(lst, how="inner")
    return t[(t.n_en_reviews >= MIN_REVIEWS)].dropna(subset=SCORES)


def _partial_spearman(x, y, z) -> float:
    rx, ry, rz = (rankdata(v) for v in (x, y, z))
    res = lambda a: a - np.polyval(np.polyfit(rz, a, 1), rz)
    return float(np.corrcoef(res(rx), res(ry))[0, 1])


def auroc(score: np.ndarray, positive: np.ndarray) -> float:
    r = rankdata(score)
    n1 = positive.sum()
    n0 = len(positive) - n1
    return float((r[positive].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    RESULTS.mkdir(exist_ok=True)
    rev = score_reviews()
    t = listing_table(rev)

    text_metrics = ["vader_mean", "vader_neg_share", "legacy_mean", *[f"cmp_{k}" for k in ASPECTS], "cmp_any"]
    corr, pcorr = {}, {}
    for m in text_metrics:
        corr[m] = {s: spearmanr(t[m], t[s]).statistic for s in SCORES}
        pcorr[m] = {s: _partial_spearman(t[m].to_numpy(), t[s].to_numpy(), t["review_scores_rating"].to_numpy())
                    for s in SCORES if s != "review_scores_rating"}
    pd.DataFrame(corr).T.to_csv(RESULTS / "spearman.csv", float_format="%.3f")
    pd.DataFrame(pcorr).T.to_csv(RESULTS / "partial_spearman_given_rating.csv", float_format="%.3f")

    # Detection of the bottom decile of overall rating. Higher = more likely low-rated.
    thr = t.review_scores_rating.quantile(BOTTOM_QUANTILE)
    pos = (t.review_scores_rating <= thr).to_numpy()
    detectors = {"VADER mean (negated)": -t.vader_mean, "VADER negative share": t.vader_neg_share,
                 "Legacy keyword score (negated)": -t.legacy_mean, "Any aspect complaint": t.cmp_any}
    rng = np.random.default_rng(args.seed)
    boot_idx = [rng.integers(0, len(t), len(t)) for _ in range(N_BOOT)]
    rows = []
    for name, s in detectors.items():
        s = s.to_numpy()
        b = [auroc(s[i], pos[i]) for i in boot_idx]
        rows.append({"detector": name, "auroc": auroc(s, pos), "ci_low": np.percentile(b, 2.5), "ci_high": np.percentile(b, 97.5)})
    pd.DataFrame(rows).to_csv(RESULTS / "auroc_bottom_decile.csv", index=False, float_format="%.3f")

    # Bootstrap CI of each lexicon's partial correlation with its own sub-score.
    diag = []
    z = t["review_scores_rating"].to_numpy()
    for k in ASPECTS:
        x, y = t[f"cmp_{k}"].to_numpy(), t[f"review_scores_{k}"].to_numpy()
        b = [_partial_spearman(x[i], y[i], z[i]) for i in boot_idx]
        diag.append({"aspect": k, "partial_rho": _partial_spearman(x, y, z),
                     "ci_low": np.percentile(b, 2.5), "ci_high": np.percentile(b, 97.5)})
    pd.DataFrame(diag).to_csv(RESULTS / "partial_own_subscore_ci.csv", index=False, float_format="%.3f")

    audit = {
        "listings": int(len(t)),
        "english_reviews_in_listings": int(t.n_en_reviews.sum()),
        "bottom_decile_threshold": float(thr),
        "bottom_decile_listings": int(pos.sum()),
        "legacy_ac_share": float(rev.legacy_ac.mean()),
        "word_boundary_ac_share": float(rev.ac_word.mean()),
        "legacy_score_corr_with_length": float(spearmanr(rev.legacy, rev.n_words).statistic),
        "vader_corr_with_length": float(spearmanr(rev.vader, rev.n_words).statistic),
        "aspect_review_rates": {k: float(rev[f"cmp_{k}"].mean()) for k in ASPECTS},
    }
    (RESULTS / "audit.json").write_text(json.dumps(audit, indent=2))
    print(json.dumps(audit, indent=2))
    print(pd.DataFrame(rows).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
