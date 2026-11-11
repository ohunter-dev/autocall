# Desk risk: move one input, re-price, compare.
#
# Same random numbers every run (same seed), so the only thing that changes
# is the input I moved, not the luck of the draw.
#
# My rule for reading the table: the client sells the bank a put on the worst
# index, and the coupon is what the bank pays for it. So if the fair coupon
# rises when X goes up, the bank is long X. If it rises when X goes down, the
# bank is short X. The client is always the opposite.

import numpy as np

from .paths import simulate_paths
from .pricing import score_paths, fair_coupon
from .payoff import Autocall

# market inputs. Placeholders that look like a high-dividend index (FTSE 100
# style) and a low-dividend one (S&P 500 style), not live quotes.
MARKET = dict(vols=(0.16, 0.17), rho=0.75, q=(0.036, 0.013), r=0.04)


def fair_coupon_for(product, vols, rho, q, r, steps_per_year=1, n_paths=50_000, seed=11):
    # the time grid: annual steps are enough for a european barrier, but an
    # american one has to be checked monthly, not just on the yearly dates
    n_years = int(product.n_years)
    n_steps = n_years * steps_per_year
    dt = 1.0 / steps_per_year
    obs_idx = [steps_per_year * (k + 1) for k in range(n_years)]
    rng = np.random.default_rng(seed)

    # pricing uses risk-neutral growth: rate minus dividends. That's the cost
    # of hedging, not anyone's forecast.
    drifts = (r - q[0], r - q[1])
    paths = simulate_paths(rng, n_paths, n_steps, dt, drifts, vols, rho)
    base, years, life, state = score_paths(product, paths, obs_idx)
    return fair_coupon(base, years, life, r)


def risk_table(n_paths=50_000):
    def fc(product=None, **changes):
        return fair_coupon_for(product or Autocall(), **{**MARKET, **changes}, n_paths=n_paths)

    base = fc()
    rows = [
        ("correlation 0.75 -> 0.95", fc(rho=0.95), base),
        ("correlation 0.75 -> 0.30", fc(rho=0.30), base),
        ("volatility +5 points", fc(vols=(0.21, 0.22)), base),
        ("dividends +1% a year", fc(q=(0.046, 0.023)), base),
        ("barrier 65% -> 55%", fc(Autocall(barrier=0.55)), base),
        ("barrier 65% -> 75%", fc(Autocall(barrier=0.75)), base),
    ]
    rows.append(("barrier 75% -> 85%", fc(Autocall(barrier=0.85)), rows[-1][1]))
    euro_m = fc(steps_per_year=12)
    rows.append(("american barrier (vs european, monthly)",
                 fc(Autocall(barrier_style="american"), steps_per_year=12), euro_m))
    return base, rows
