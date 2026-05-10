"""Gaussian peak fit, used by autofocus to estimate best-focus z position.

Pure math — no hardware, no I/O. Given samples of (value, position),
fit a Gaussian and return the position of the peak.
"""
from typing import Optional, Sequence, Tuple

import numpy as np
from scipy.optimize import curve_fit


def gaussian(x, amplitude, mean, std):
    """Standard Gaussian, exposed so callers can re-evaluate the fit for plots."""
    return amplitude * np.exp(-((x - mean) ** 2) / (2 * std ** 2))


def fit_peak(samples: Sequence[Tuple[float, float]]) -> Optional[float]:
    """Fit a Gaussian to (value, position) samples and return the peak position.

    Returns None when:
      - all values are zero (no signal to fit), or
      - curve_fit fails to converge.

    The caller decides how to handle a failed fit (log it, retry, fall back).
    """
    values = np.array([pt[0] for pt in samples], dtype=float)
    positions = np.array([pt[1] for pt in samples], dtype=float)

    if values.max(initial=0) == 0:
        return None

    p0 = [values.max(), positions[np.argmax(values)], 0.05]
    try:
        popt, _ = curve_fit(gaussian, positions, values, p0=p0)
    except Exception:
        return None

    return float(popt[1])
