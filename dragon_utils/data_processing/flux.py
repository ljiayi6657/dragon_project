import numpy as np
import os, sys, time, math, pickle
from scipy.interpolate import interp1d



import numpy as np
from scipy.interpolate import interp1d


def interp(x, y, interpolatetype, logx=False, logy=False):
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

    x = np.asarray(x)
    y = np.asarray(y)

    if len(x) < 2:
        print("Error: Not enough valid data points for interpolation. (interp)")
        return lambda x_new: (
            np.zeros_like(x_new)
            if hasattr(x_new, "shape")
            else 0.0
        )

    # Transfer original data to log-space if needed
    x_interp = np.log10(x) if logx else x
    y_interp = np.log10(y) if logy else y

    if interpolatetype == "linear":
        base_f = interp1d(
            x_interp,
            y_interp,
            kind="linear",
            fill_value="extrapolate"
        )

    elif interpolatetype == "cubic":
        base_f = interp1d(
            x_interp,
            y_interp,
            kind="cubic",
            fill_value="extrapolate"
        )

    else:
        print("Error: Unsupported interpolation type. (interp)")
        return None

    def f(x_new):
        x_new_interp = np.log10(x_new) if logx else x_new
        y_new_interp = base_f(x_new_interp)

        return 10**y_new_interp if logy else y_new_interp

    return f