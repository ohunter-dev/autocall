import numpy as np
import pytest

from autocall.pricing import discount, note_value, fair_coupon

# three hand-worked paths: called yr1, called yr2, breached and ended at 60%
BASE = np.array([1.0, 1.0, 0.60])
YEARS = np.array([1.0, 2.0, 0.0])
LIFE = np.array([1.0, 2.0, 6.0])
R = 0.04


def test_discount():
    assert discount(R, 1.0) == pytest.approx(0.9608, abs=1e-4)


def test_value_and_fair_coupon():
    D = np.exp(-R * LIFE)
    assert note_value(BASE, YEARS, LIFE, 0.08, R) == pytest.approx(np.mean(D * (BASE + 0.08 * YEARS)))
    c = fair_coupon(BASE, YEARS, LIFE, R)
    assert c == pytest.approx((1 - np.mean(D * BASE)) / np.mean(D * YEARS))
    # at the fair coupon the note is worth exactly what the client paid
    assert note_value(BASE, YEARS, LIFE, c, R) == pytest.approx(1.0)
