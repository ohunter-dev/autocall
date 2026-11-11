# Directions only: these are fixed by the product, not by the model's detail.
import pytest

from autocall.payoff import Autocall
from autocall.risk import MARKET, fair_coupon_for

N = 20_000


def fc(product=None, **changes):
    return fair_coupon_for(product or Autocall(), **{**MARKET, **changes}, n_paths=N)


@pytest.fixture(scope="module")
def base():
    return fc()


def test_bank_is_short_correlation(base):
    assert fc(rho=0.30) > base > fc(rho=0.95)


def test_bank_is_long_vol(base):
    assert fc(vols=(0.21, 0.22)) > base


def test_bank_is_long_dividends(base):
    assert fc(q=(0.046, 0.023)) > base


def test_more_protection_costs_coupon(base):
    assert fc(Autocall(barrier=0.55)) < base < fc(Autocall(barrier=0.75))


def test_barrier_above_final_trigger_does_nothing():
    assert fc(Autocall(barrier=0.85)) == pytest.approx(fc(Autocall(barrier=0.75)))


def test_american_pays_more_than_european():
    euro = fc(steps_per_year=12)
    assert fc(Autocall(barrier_style="american"), steps_per_year=12) > euro
