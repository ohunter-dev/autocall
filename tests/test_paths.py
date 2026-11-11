import numpy as np
import pytest

from autocall.paths import one_step, correlate, simulate_paths


def test_one_step_by_hand():
    # 5% drift, 20% vol, one year: drift part = 0.05 - 0.5*0.04 = 0.03
    assert one_step(1.0, 0.05, 0.20, 1.0, 0.0) == pytest.approx(np.exp(0.03))
    assert one_step(1.0, 0.05, 0.20, 1.0, 1.0) == pytest.approx(np.exp(0.23))
    assert one_step(100.0, 0.05, 0.20, 0.25, -1.0) == pytest.approx(100 * np.exp(0.0075 - 0.10))


def test_correlate():
    rng = np.random.default_rng(0)
    z1, z2 = rng.standard_normal(200_000), rng.standard_normal(200_000)
    assert np.allclose(correlate(z1, z2, 1.0)[1], z1)
    assert np.allclose(correlate(z1, z2, 0.0)[1], z2)
    w1, w2 = correlate(z1, z2, 0.75)
    assert np.corrcoef(w1, w2)[0, 1] == pytest.approx(0.75, abs=0.01)
    assert w2.std() == pytest.approx(1.0, abs=0.01)


def test_simulated_paths_behave():
    P = simulate_paths(np.random.default_rng(1), 200_000, 6, 1.0, (0.03, 0.03), (0.16, 0.20), 0.75)
    assert P.shape == (200_000, 2, 7)
    assert np.all(P[:, :, 0] == 1.0)
    # the average grows at the drift: this fails if the -0.5*v**2 is missing
    assert P[:, 0, -1].mean() == pytest.approx(np.exp(0.18), rel=0.01)
    lr = np.log(P[:, :, -1])
    assert lr[:, 0].std() == pytest.approx(0.16 * np.sqrt(6), abs=0.01)
    assert lr[:, 1].std() == pytest.approx(0.20 * np.sqrt(6), abs=0.01)
    assert np.corrcoef(lr[:, 0], lr[:, 1])[0, 1] == pytest.approx(0.75, abs=0.01)
