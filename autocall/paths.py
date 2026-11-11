# Simulating the two indices: thousands of possible futures, one step at a time.
#
# Each step needs a drift (average growth), a vol (how violently it moves) and
# a random shock from a bell curve. Correlation ties the two indices' shocks
# together, because when one market falls the other usually does too.

import numpy as np


def one_step(S, m, v, dt, z):
    # next level = level x exp((drift - half vol squared) x dt + vol x sqrt(dt) x shock)
    #
    # exp keeps prices positive and makes moves percentage-based.
    # The -0.5*v**2 is the bit that's easy to forget: big up-moves compound
    # more than big down-moves, so randomness on its own inflates the average.
    # Taking it off makes the average path grow at exactly the drift.
    return S * np.exp((m - 0.5 * v**2) * dt + v * np.sqrt(dt) * z)


def correlate(z1, z2, rho):
    # turn two independent shocks into two correlated ones.
    # The second index copies `rho` of the first one's shock and makes up the
    # rest with its own noise. sqrt(1 - rho**2) keeps the shock a normal size.
    #   rho = 1 -> lockstep,  rho = 0 -> unrelated
    w1 = z1
    w2 = rho * z1 + np.sqrt(1 - rho**2) * z2
    return w1, w2


def simulate_paths(rng, n_paths, n_steps, dt, drifts, vols, rho):
    # returns a (n_paths, 2, n_steps + 1) box: every path, both indices, every
    # date, all starting at 1.0. numpy handles all the paths at once, so the
    # only loop is over time.
    paths = np.ones((n_paths, 2, n_steps + 1))

    for t in range(n_steps):
        z1 = rng.standard_normal(n_paths)       # one shock per path
        z2 = rng.standard_normal(n_paths)
        w1, w2 = correlate(z1, z2, rho)         # make them move together

        # each column is built from the one before it
        paths[:, 0, t + 1] = one_step(paths[:, 0, t], drifts[0], vols[0], dt, w1)
        paths[:, 1, t + 1] = one_step(paths[:, 1, t], drifts[1], vols[1], dt, w2)

    return paths
