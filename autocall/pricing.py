# Turning simulated paths into a price, and solving for the fair coupon.
#
# Price = average of the discounted payouts over every simulated path.
# Values are per 1.0 of notional: 0.97 means "worth 97% of what the client paid".

import numpy as np

from .payoff import evaluate_path


def score_paths(product, paths, obs_idx):
    # run every path through the payoff and collect the four answers as arrays
    results = [evaluate_path(product, p, obs_idx) for p in paths]
    base = np.array([r["base"] for r in results])
    years = np.array([r["years"] for r in results])
    life = np.array([r["life"] for r in results])
    state = np.array([r["state"] for r in results])
    return base, years, life, state


def discount(r, life):
    # 1.0 paid in `life` years is worth exp(-r x life) today.
    # It's life (when the cash arrives), not years (coupon years earned):
    # a path that runs to maturity with no coupon still pays out in year 6.
    return np.exp(-r * life)


def note_value(base, years, life, coupon, r):
    # average discounted payout, at a given coupon
    return np.mean(discount(r, life) * (base + coupon * years))


def fair_coupon(base, years, life, r):
    # value(c) = A + c x B, a straight line in the coupon:
    #   A = what the capital part is worth today
    #   B = what 1.0 a year of coupon is worth today, given it stops when called
    # Set value = 1 (what the client pays) and rearrange: c = (1 - A) / B.
    # No trial and error, because the coupon never changes which paths get called.
    D = discount(r, life)
    A = np.mean(D * base)
    B = np.mean(D * years)
    return (1 - A) / B


def outcomes(state, n_obs):
    # share of paths called in each year, then capital back, then loss
    called = [np.mean(state == k) for k in range(n_obs)]
    return called, np.mean(state == -1), np.mean(state == -2)
