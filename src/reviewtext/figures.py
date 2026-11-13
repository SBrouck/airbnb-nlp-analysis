"""Paper-style figures from results/*.csv."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams.update({
    "font.family": "STIXGeneral", "mathtext.fontset": "stix", "font.size": 9,
    "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "legend.frameon": False, "svg.fonttype": "none",
})
R, OUT = Path("results"), Path("figures")
ROWS = {"vader_mean": "VADER mean", "cmp_cleanliness": "Cleanliness lexicon", "cmp_checkin": "Check-in lexicon",
        "cmp_communication": "Communication lexicon", "cmp_location": "Location lexicon",
        "cmp_accuracy": "Accuracy lexicon", "cmp_value": "Value lexicon"}
COLS = {"review_scores_rating": "Overall", "review_scores_cleanliness": "Cleanliness", "review_scores_checkin": "Check-in",
        "review_scores_communication": "Communication", "review_scores_location": "Location",
        "review_scores_accuracy": "Accuracy", "review_scores_value": "Value"}


def _heat(ax, M, title, vmax):
    im = ax.imshow(M.to_numpy(), cmap="RdBu", vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(range(M.shape[1]), M.columns, rotation=35, ha="right")
    ax.set_yticks(range(M.shape[0]), M.index)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = M.iat[i, j]
            ax.text(j, i, f"{v:.2f}".replace("-", "−"), ha="center", va="center", fontsize=7,
                    color="white" if abs(v) > 0.6 * vmax else "black")
    ax.set_title(title, fontsize=9, loc="left")
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    return im


def fig_correlations():
    rho = pd.read_csv(R / "spearman.csv", index_col=0).loc[list(ROWS), list(COLS)]
    prho = pd.read_csv(R / "partial_spearman_given_rating.csv", index_col=0).loc[list(ROWS), list(COLS)[1:]]
    rho.index = prho.index = list(ROWS.values())
    rho.columns = list(COLS.values())
    prho.columns = list(COLS.values())[1:]
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.6, 2.9), gridspec_kw={"width_ratios": [7, 6]})
    _heat(a, rho, "(a) Spearman $\\rho$", 0.7)
    _heat(b, prho, "(b) Partial $\\rho$ given overall rating", 0.3)
    b.set_yticklabels([])
    for j in range(prho.shape[1]):  # outline each lexicon's own sub-score
        i = j + 1
        b.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False, lw=1.0, ec="black"))
    fig.tight_layout()
    fig.savefig(OUT / "fig1_correlations.svg")
    plt.close(fig)


def fig_auroc():
    d = pd.read_csv(R / "auroc_bottom_decile.csv").iloc[::-1]
    fig, ax = plt.subplots(figsize=(3.8, 1.8))
    y = np.arange(len(d))
    ax.errorbar(d.auroc, y, xerr=[d.auroc - d.ci_low, d.ci_high - d.auroc], fmt="o", ms=3.5,
                color="#1f4e79", ecolor="#1f4e79", elinewidth=0.9, capsize=2)
    ax.set_yticks(y, d.detector)
    ax.set_xlabel("AUROC, bottom-decile overall rating")
    ax.set_xlim(0.78, 0.94)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "fig2_auroc.svg")
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    fig_correlations()
    fig_auroc()


if __name__ == "__main__":
    main()
