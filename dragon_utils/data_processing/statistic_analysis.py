import numpy as np



def chisquare(obs, exp, error, dof=None, covariance=None, return_points=False, positive=True):
    """
    Calculate an auditable chi-square from observed and model values.

    Inputs:
    obs (nparray)      : Observed data.
    exp (nparray)      : Expected data.
    error (nparray)    : Symmetric errors, or [lower, upper] errors per row.
    dof (int, optional): Positive degrees of freedom for a reduced value.
    covariance         : Optional full covariance; error must be symmetric.
    return_points      : Return raw residuals and point contributions.
    positive           : Require positive observed and model values.

    Outputs:
    chi2 (float or dict): Raw or reduced chi-square, or point details.

    KEYWORDS: chi-square, reduced chi-square
    """
    obs = np.asarray(obs, dtype=float)
    exp = np.asarray(exp, dtype=float)
    if obs.ndim != 1 or exp.shape != obs.shape or obs.size == 0:
        raise ValueError("obs and exp must be nonempty, matching one-dimensional arrays")
    if not np.all(np.isfinite(obs)) or not np.all(np.isfinite(exp)):
        raise ValueError("obs and exp must be finite")
    if positive and (np.any(obs <= 0) or np.any(exp <= 0)):
        raise ValueError("obs and exp must be positive")
    if dof is not None and (not isinstance(dof, int) or dof <= 0):
        raise ValueError("dof must be a positive integer")

    residual = obs - exp
    if covariance is None:
        error = np.asarray(error, dtype=float)
        if error.shape == obs.shape:
            sigma = error
        elif error.shape == (obs.size, 2):
            sigma = np.where(exp > obs, error[:, 1], error[:, 0])
        else:
            raise ValueError("error must have shape (n,) or (n, 2)")
        if not np.all(np.isfinite(sigma)) or np.any(sigma <= 0):
            raise ValueError("selected errors must be finite and positive")
        if error.shape == (obs.size, 2) and (not np.all(np.isfinite(error)) or np.any(error <= 0)):
            raise ValueError("both asymmetric errors must be finite and positive")
        contribution = np.square(residual / sigma)
    else:
        covariance = np.asarray(covariance, dtype=float)
        if covariance.shape != (obs.size, obs.size) or not np.all(np.isfinite(covariance)):
            raise ValueError("covariance must be a finite n by n matrix")
        if not np.allclose(covariance, covariance.T, rtol=1e-12, atol=0):
            raise ValueError("covariance must be symmetric")
        try:
            np.linalg.cholesky(covariance)
        except np.linalg.LinAlgError as exc:
            raise ValueError("covariance must be positive definite") from exc
        sigma = np.sqrt(np.diag(covariance))
        if error is not None:
            error = np.asarray(error, dtype=float)
            if error.shape != obs.shape or not np.allclose(error, sigma, rtol=1e-8, atol=0):
                raise ValueError("error must match covariance diagonal")
        contribution = residual * np.linalg.solve(covariance, residual)

    chi2 = float(np.sum(contribution))
    if not np.isfinite(chi2):
        raise ValueError("chi-square is non-finite")
    if return_points:
        return {"chi2": chi2, "residual": residual, "sigma": sigma,
                "contribution": contribution, "dof": dof,
                "reduced": chi2 / dof if dof is not None else None}
    return chi2 if dof is None else chi2 / dof


def fit_constant(obs, model, error, scales=None):
    """Fit one positive multiplicative model constant and verify nearby values."""
    obs = np.asarray(obs, dtype=float)
    model = np.asarray(model, dtype=float)
    error = np.asarray(error, dtype=float)
    if obs.ndim != 1 or model.shape != obs.shape or error.shape != obs.shape:
        raise ValueError("obs, model, and error must be matching one-dimensional arrays")
    if obs.size == 0:
        raise ValueError("constant fit requires at least one point")
    if (not np.all(np.isfinite(obs)) or not np.all(np.isfinite(model)) or
            not np.all(np.isfinite(error))):
        raise ValueError("constant fit inputs must be finite")
    if np.any(obs <= 0) or np.any(model <= 0) or np.any(error <= 0):
        raise ValueError("constant fit inputs must be positive")
    denom = float(np.sum(np.square(model / error)))
    if not np.isfinite(denom) or denom <= 0:
        raise ValueError("constant fit denominator must be finite and positive")
    analytic = float(np.sum(model * obs / np.square(error)) / denom)
    if not np.isfinite(analytic) or analytic <= 0:
        raise ValueError("analytic constant must be finite and positive")
    anachi = chisquare(obs, analytic * model, error)
    scan = []
    if scales is not None:
        factors = np.asarray(scales, dtype=float)
        if factors.ndim != 1 or factors.size == 0:
            raise ValueError("scales must be a nonempty one-dimensional array")
        if not np.all(np.isfinite(factors)) or np.any(factors <= 0):
            raise ValueError("scales must be finite and positive")
        for factor in factors:
            candidate = analytic * factor
            value = chisquare(obs, candidate * model, error)
            scan.append((float(candidate), value))
    best = min(scan, key=lambda item: item[1]) if scan else (analytic, anachi)
    if best[1] < anachi:
        constant, chi2, source = best[0], best[1], "grid"
    else:
        constant, chi2, source = analytic, anachi, "analytic"
    return {"constant": constant, "chi2": chi2, "source": source,
            "analytic": analytic, "anachi": anachi, "scan": scan}
