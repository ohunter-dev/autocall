# Every expected value here was worked out by hand from the term sheet.
import numpy as np
import pytest

from autocall.payoff import Autocall, evaluate_path, MATURED_ABOVE, MATURED_BELOW

OBS = [1, 2, 3, 4, 5, 6]
EURO = Autocall()
AMER = Autocall(barrier_style="american")


def path_from(weak, strong=None):
    # weak index follows `weak`; the strong one sits 30 points above unless given
    a = np.ones((2, 7))
    a[0, 1:] = weak
    a[1, 1:] = strong if strong is not None else [x + 0.30 for x in weak]
    return a


CASES = [
    # name, product, path, state, base, years
    ("clears 100% at year 1", EURO, path_from([1.05] * 6), 0, 1.0, 1.0),
    ("misses yr1, clears 95% at yr2", EURO, path_from([0.92, 0.97, 1, 1, 1, 1]), 1, 1.0, 2.0),
    ("flat 80% clears the year-5 trigger", EURO, path_from([0.80] * 6), 4, 1.0, 5.0),
    ("never called, ends 70%: capital back", EURO, path_from([0.70] * 6), MATURED_ABOVE, 1.0, 0.0),
    ("never called, ends 50%: index loss", EURO, path_from([0.50] * 6), MATURED_BELOW, 0.50, 0.0),
    ("0.1% above the barrier", EURO, path_from([0.651] * 6), MATURED_ABOVE, 1.0, 0.0),
    ("0.1% below the barrier: the cliff", EURO, path_from([0.649] * 6), MATURED_BELOW, 0.649, 0.0),
    ("worst-of, not average", EURO, path_from([0.60] * 6, [1.30] * 6), MATURED_BELOW, 0.60, 0.0),
    ("american knocks in, recovers, still called", AMER,
     path_from([0.60] * 5 + [0.95], [1.30] * 6), 5, 1.0, 6.0),
    ("american knocks in where european wouldn't", AMER,
     path_from([0.60] * 5 + [0.70], [1.30] * 6), MATURED_BELOW, 0.70, 0.0),
    ("european on the same path holds", EURO,
     path_from([0.60] * 5 + [0.70], [1.30] * 6), MATURED_ABOVE, 1.0, 0.0),
]


@pytest.mark.parametrize("name,product,path,state,base,years", CASES, ids=[c[0] for c in CASES])
def test_payoff(name, product, path, state, base, years):
    got = evaluate_path(product, path, OBS)
    assert got["state"] == state
    assert got["base"] == pytest.approx(base)
    assert got["years"] == pytest.approx(years)
