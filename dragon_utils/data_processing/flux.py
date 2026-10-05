import numpy as np
import os, sys, time, math, pickle
from scipy.interpolate import interp1d



import numpy as np
from scipy.interpolate import interp1d


def interp(x, y, interpolatetype, logx=False, logy=False, allow_extrapolation=False):
    """
    This function is used to interpolate data.

    Inputs:
    x (nparray)          : x data.
    y (nparray)          : y data.
    interpolatetype (str): Type of interpolation method,
                           e.g., 'linear', 'cubic'.
    logx (bool)          : Whether to interpolate x in log10 space.
    logy (bool)          : Whether to interpolate y in log10 space.

    Outputs:
    f (function): Interpolation function.
    KEYWORDS: interpolation
    """

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    if x.ndim != 1 or y.shape != x.shape or x.size < 2:
        raise ValueError("x and y must be matching one-dimensional arrays with at least two points")
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)) or np.any(np.diff(x) <= 0):
        raise ValueError("x and y must be finite, and x strictly increasing")
    if (logx and np.any(x <= 0)) or (logy and np.any(y <= 0)):
        raise ValueError("log interpolation requires positive values")

    # Transfer original data to log-space if needed
    x_interp = np.log10(x) if logx else x
    y_interp = np.log10(y) if logy else y

    if interpolatetype == "linear":
        base_f = interp1d(
            x_interp,
            y_interp,
            kind="linear",
            bounds_error=not allow_extrapolation,
            fill_value="extrapolate" if allow_extrapolation else np.nan
        )

    elif interpolatetype == "cubic":
        base_f = interp1d(
            x_interp,
            y_interp,
            kind="cubic",
            bounds_error=not allow_extrapolation,
            fill_value="extrapolate" if allow_extrapolation else np.nan
        )

    else:
        raise ValueError("unsupported interpolation type")

    def f(x_new):
        x_new = np.asarray(x_new, dtype=float)
        if not np.all(np.isfinite(x_new)) or (logx and np.any(x_new <= 0)):
            raise ValueError("interpolation energies must be finite and positive")
        x_new_interp = np.log10(x_new) if logx else x_new
        y_new_interp = base_f(x_new_interp)

        return 10**y_new_interp if logy else y_new_interp

    return f
