# The term sheet, and what the note pays on one price path.
#
# No randomness lives here. Give it a path and the answer is fixed, which is
# why I built and tested this first, by hand, before simulating anything.
#
# The product: 6 years, worst of two indices, checked once a year.
#   - worst index at or above that year's trigger -> called: capital + all coupons so far
#   - never called, barrier held at the end      -> capital back, no coupon
#   - never called, barrier breached             -> you get the worst index's final level
#
# That last line is the whole risk. Written as 1 + min(W - 1, 0), it's a put
# struck at 100% that the client has sold to the bank. The barrier doesn't cap
# the loss, it's an on/off switch: end at 65.0% and you get 100 back, end at
# 64.9% and you get 64.9. A 0.1% move in the index, a 35% swing in the payout.

from dataclasses import dataclass

import numpy as np

# outcome codes for paths that were never called (called paths use 0..5,
# i.e. which yearly check called them)
MATURED_ABOVE = -1   # barrier held: capital back, no coupon
MATURED_BELOW = -2   # barrier breached: client takes the index loss


@dataclass(frozen=True)
class Autocall:
    notional: float = 100_000.0
    n_years: float = 6.0
    # the triggers step down each year, so it gets easier to be called as
    # time goes on. That's what makes it "defensive"
    triggers: tuple = (1.00, 0.95, 0.90, 0.85, 0.80, 0.75)
    coupon_pa: float = 0.08          # paid in full on the call date ("snowball")
    barrier: float = 0.65
    barrier_style: str = "european"  # european = checked at maturity only
                                     # american = checked every step, one touch counts

    @property
    def n_obs(self) -> int:
        return len(self.triggers)

    @property
    def years_per_obs(self) -> float:
        return self.n_years / self.n_obs


def evaluate_path(product: Autocall, path: np.ndarray, obs_idx) -> dict:
    # path is a (2 indices x time) grid, both indices starting at 1.0.
    # obs_idx says which columns are the yearly check dates.

    # the note only cares about the weaker index on each date
    worst = path.min(axis=0)

    # trigger first: walk the check dates in order and stop at the first call.
    # This has to come before the barrier, because a path can knock in and
    # still recover above the final trigger, and then it's called, not lost.
    for k, t in enumerate(obs_idx):
        if worst[t] >= product.triggers[k]:
            years = (k + 1) * product.years_per_obs
            return dict(state=k, base=1.0, years=years, life=years)

    # only reached if nothing called. Now the barrier decides.
    final = worst[-1]
    if product.barrier_style == "american":
        breached = worst.min() < product.barrier   # any touch over the whole life
    else:
        breached = final < product.barrier         # last day only

    # I keep `base` (the capital part) and `years` (coupon years earned)
    # separate on purpose: payout = base + coupon * years. Whether and when a
    # path is called never depends on the coupon, so the price is a straight
    # line in the coupon, and the fair coupon solves in one line (pricing.py).
    if breached:
        # the loss runs from the START level (100%), not from the barrier
        return dict(state=MATURED_BELOW, base=min(final, 1.0), years=0.0, life=product.n_years)
    return dict(state=MATURED_ABOVE, base=1.0, years=0.0, life=product.n_years)
