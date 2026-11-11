# python -m autocall.run
#
# Prices the note, shows where the money lands under both measures, then the
# desk risk table.

import numpy as np

from .payoff import Autocall
from .paths import simulate_paths
from .pricing import score_paths, fair_coupon, note_value, outcomes
from .risk import MARKET, risk_table

N_PATHS = 100_000
OBS = [1, 2, 3, 4, 5, 6]


def simulate(drifts, seed=11):
    rng = np.random.default_rng(seed)
    return simulate_paths(rng, N_PATHS, 6, 1.0, drifts, MARKET["vols"], MARKET["rho"])


def show_outcomes(label, state):
    called, back, lost = outcomes(state, 6)
    years = "  ".join(f"yr{k + 1} {p:4.1%}" for k, p in enumerate(called))
    print(f"  {label}")
    print(f"    called: {years}")
    print(f"    capital back {back:5.1%}   loss {lost:5.1%}")


if __name__ == "__main__":
    product = Autocall()
    r, q = MARKET["r"], MARKET["q"]

    # pricing world: growth = rate minus dividends
    b, y, l, s = score_paths(product, simulate((r - q[0], r - q[1])), OBS)
    fc = fair_coupon(b, y, l, r)
    v8 = note_value(b, y, l, product.coupon_pa, r)

    print("\n6y step-down worst-of autocall, 65% european barrier, 8% a year")
    print("=" * 72)
    print(f"  fair coupon            {fc:6.2%} a year")
    print(f"  value at 8% coupon     {v8:6.4f} per 1.00 paid  "
          f"(gap of {1 - v8:.1%}: margin, distribution, funding)")
    print("-" * 72)
    show_outcomes("RISK-NEUTRAL (pricing only, not a forecast)", s)
    # a real-world view: 4.5% a year growth. An opinion, and here the rosier one
    _, _, _, sw = score_paths(product, simulate((0.045, 0.045)), OBS)
    show_outcomes("REAL-WORLD (assumes 4.5% a year growth)", sw)

    print("-" * 72)
    print("  desk risk: move one input, re-price")
    base, rows = risk_table()
    print(f"    {'base case':<42} {base:6.2%}")
    for name, value, ref in rows:
        print(f"    {name:<42} {value:6.2%}  {(value - ref) * 1e4:+5.0f}bp")
    print("=" * 72)
