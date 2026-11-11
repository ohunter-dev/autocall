# python -m autocall.plots  ->  docs/autocall_panels.png
#
# Panel 1 is the client's picture: where the money actually lands (real-world
# view, labelled as such). Panels 2-4 are the structurer's picture: what drives
# the fair coupon. Each sweep reuses one seed for every point, so the curves
# show the real sensitivity rather than simulation noise.

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .payoff import Autocall
from .paths import simulate_paths
from .pricing import score_paths, outcomes
from .risk import MARKET, fair_coupon_for

GAIN, HOLD, LOSS, ACCENT = "#0A7C4A", "#C08109", "#B5332A", "#1F6FD0"
SURFACE, INK, SECOND, GRID = "#FCFCFB", "#1A1A19", "#5A6570", "#E3E6E4"
SWEEP_PATHS = 30_000

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "text.color": INK, "axes.labelcolor": SECOND, "xtick.color": SECOND, "ytick.color": SECOND,
    "axes.edgecolor": GRID, "grid.color": GRID, "grid.linewidth": 0.8,
    "font.size": 9.5, "axes.titlesize": 11, "axes.titleweight": "bold",
    "axes.titlelocation": "left", "axes.titlepad": 26, "figure.dpi": 130,
})


def tidy(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="y")
    ax.set_axisbelow(True)


def panel_outcomes(ax):
    # real-world view: 4.5% a year growth. A scenario, not a promise
    rng = np.random.default_rng(101)
    paths = simulate_paths(rng, 100_000, 6, 1.0, (0.045, 0.045), MARKET["vols"], MARKET["rho"])
    _, _, _, state = score_paths(Autocall(), paths, [1, 2, 3, 4, 5, 6])
    called, back, lost = outcomes(state, 6)
    probs = called + [back, lost]
    labels = [f"Yr {k + 1}" for k in range(6)] + ["Capital\nback", "Barrier\nbreached"]
    bars = ax.bar(range(8), [p * 100 for p in probs], color=[GAIN] * 6 + [HOLD, LOSS], width=0.62, zorder=3)
    for bar, p in zip(bars, probs):
        ax.annotate(f"{p:.1%}", (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    textcoords="offset points", xytext=(0, 3), ha="center", fontsize=8.5)
    tidy(ax)
    ax.set_xticks(range(8))
    ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylabel("share of paths (%)")
    ax.set_ylim(0, max(probs) * 118)
    ax.set_title("Where the money lands")
    ax.text(0, 1.02, "real-world scenario: assumes 4.5% a year growth (a view, not a price)",
            transform=ax.transAxes, fontsize=8, color=SECOND)


def sweep(ax, xs, coupons, base_x, base_c, title, xlabel, note):
    ax.plot(xs, [c * 100 for c in coupons], lw=2, color=ACCENT, zorder=3)
    ax.plot([base_x], [base_c * 100], "o", ms=8, color=ACCENT, mec=SURFACE, mew=2, zorder=4)
    ax.annotate(f"today\n{base_c:.2%}", (base_x, base_c * 100), textcoords="offset points",
                xytext=(8, -18), fontsize=8.5)
    tidy(ax)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("fair coupon (% a year)")
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.text(0, 1.02, note, transform=ax.transAxes, fontsize=8, color=SECOND)


def fc(product=None, **changes):
    return fair_coupon_for(product or Autocall(), **{**MARKET, **changes}, n_paths=SWEEP_PATHS)


def make(outdir=None):
    outdir = outdir or os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")
    os.makedirs(outdir, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(12.6, 8.4))
    fig.subplots_adjust(hspace=0.42, wspace=0.26, left=0.07, right=0.97, top=0.88, bottom=0.11)
    fig.suptitle("6y step-down defensive autocall  ·  worst of two indices  ·  8% a year  ·  65% european barrier",
                 x=0.07, ha="left", fontsize=13, fontweight="bold")

    panel_outcomes(axes[0][0])
    today = fc()   # the base case, so every "today" dot is the same number

    xs = np.linspace(0.10, 0.95, 9)
    sweep(axes[0][1], xs, [fc(rho=float(c)) for c in xs], MARKET["rho"], today,
          "Correlation: the worst-of premium", "correlation of the two indices",
          "indices drift apart -> the worst one is worse -> bigger coupon (bank is short correlation)")

    xs = np.linspace(0.40, 0.90, 11)
    sweep(axes[1][0], xs, [fc(Autocall(barrier=float(b))) for b in xs], 0.65, today,
          "Barrier: the price of protection", "capital barrier (% of start level)",
          "flat above 75%: any path not called at year 6 ended below the 75% trigger")

    xs = np.linspace(0.08, 0.34, 10)
    sweep(axes[1][1], xs, [fc(vols=(float(v), float(v) + 0.01)) for v in xs], MARKET["vols"][0], today,
          "Volatility: what the client's put is worth", "index volatility",
          "more vol -> richer put -> bigger coupon (bank is long vol)")

    fig.text(0.07, 0.005, "Flat vol, no skew: every fair coupon here is biased LOW. "
             "Panel 1 is a real-world scenario; panels 2-4 are risk-neutral prices. Same seed across each sweep.",
             fontsize=7.8, color=SECOND)
    path = os.path.join(outdir, "autocall_panels.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


if __name__ == "__main__":
    print(f"figure -> {make()}")
