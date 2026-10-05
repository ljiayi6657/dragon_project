import numpy as np
from scipy.interpolate import interp1d



def solmod(Ek,phi,M):
    return Ek*(Ek+2.0*M)/((Ek+phi)*(Ek+phi+2.0*M))



def SM_output(
    Elist,
    Flux,
    PhiP=0.5,
    Mass=0.938,
    output_energies=None,
    allow_extrapolation=False,
    charge=1,
    massnum=1
):
    """
    Apply force-field solar modulation to a LIS spectrum per nucleon.

    The LIS flux is interpolated in log-energy/log-flux space and
    evaluated at the shifted energy E + PhiP. The solar modulation
    factor is calculated by the external ``solmod`` function.

    Parameters
    ----------
    Elist : array-like
        LIS kinetic-energy array in GeV.

    Flux : array-like
        LIS proton flux corresponding to Elist. Flux values must be
        strictly positive for log-log interpolation.

    PhiP : float, optional
        Solar modulation potential in GV. The energy shift is
        abs(charge) * PhiP / massnum in GeV per nucleon.

    Mass : float, optional
        Particle mass in GeV per nucleon.

    output_energies : array-like, optional
        Energy points at which the modulated spectrum is calculated.
        If None, the original energy points are used.

    allow_extrapolation : bool, optional
        Whether to allow LIS extrapolation outside the original
        energy range. Default is False.

    charge, massnum : float, optional
        Nuclear charge and mass number.

    Returns
    -------
    E_mod : np.ndarray
        Output kinetic-energy array in GeV.

    Flux_mod : np.ndarray
        Solar-modulated proton flux.
    """

    # Convert inputs to one-dimensional NumPy arrays
    Elist = np.asarray(Elist, dtype=float)
    Flux = np.asarray(Flux, dtype=float)

    # Check array dimensions
    if Elist.ndim != 1 or Flux.ndim != 1:
        raise ValueError(
            "Elist and Flux must be one-dimensional arrays."
        )

    if Elist.size != Flux.size:
        raise ValueError(
            "Elist and Flux must have the same length."
        )

    if Elist.size < 2:
        raise ValueError(
            "At least two energy points are required for interpolation."
        )

    # Check input values
    if not np.all(np.isfinite(Elist)):
        raise ValueError(
            "Elist contains NaN or infinite values."
        )

    if not np.all(np.isfinite(Flux)):
        raise ValueError(
            "Flux contains NaN or infinite values."
        )

    if np.any(Elist <= 0):
        raise ValueError(
            "All input energies must be strictly positive."
        )

    if np.any(Flux <= 0):
        raise ValueError(
            "All flux values must be strictly positive for "
            "log-log interpolation."
        )

    if not np.isfinite(PhiP) or PhiP < 0:
        raise ValueError(
            "PhiP must be non-negative."
        )

    if not np.isfinite(Mass) or Mass <= 0:
        raise ValueError(
            "Mass must be positive."
        )

    if not np.isfinite(charge) or not np.isfinite(massnum) or massnum <= 0 or charge == 0:
        raise ValueError("charge and massnum must be finite and nonzero.")

    # Sort the LIS spectrum by energy
    sort_indices = np.argsort(Elist)
    Elist_sorted = Elist[sort_indices]
    Flux_sorted = Flux[sort_indices]

    # interp1d requires unique interpolation coordinates
    if np.any(np.diff(Elist_sorted) <= 0):
        raise ValueError(
            "Elist must contain unique energy values."
        )

    # Determine output energy points
    if output_energies is None:
        E_mod = Elist_sorted.copy()
    else:
        E_mod = np.asarray(output_energies, dtype=float)

    if E_mod.ndim != 1:
        raise ValueError(
            "output_energies must be a one-dimensional array."
        )

    if not np.all(np.isfinite(E_mod)):
        raise ValueError(
            "output_energies contains NaN or infinite values."
        )

    if np.any(E_mod <= 0):
        raise ValueError(
            "All output energies must be strictly positive."
        )

    # The LIS must be evaluated at the shifted energy
    phi_eff = abs(charge) * PhiP / massnum
    E_shifted = E_mod + phi_eff

    # Check whether extrapolation is needed
    outside_range = (
        (E_shifted < Elist_sorted[0])
        | (E_shifted > Elist_sorted[-1])
    )

    if not allow_extrapolation and np.any(outside_range):
        raise ValueError(
            "Some shifted energies lie outside the LIS energy range. "
            "Increase the LIS range or set allow_extrapolation=True."
        )

    # Construct the log-log LIS interpolator
    logE = np.log10(Elist_sorted)
    logFlux = np.log10(Flux_sorted)

    fill_value = (
        "extrapolate"
        if allow_extrapolation
        else np.nan
    )

    lis_interpolator = interp1d(
        logE,
        logFlux,
        kind="linear",
        bounds_error=False,
        fill_value=fill_value,
        assume_sorted=True
    )

    # Evaluate the LIS at E + PhiP
    logFlux_LIS_shifted = lis_interpolator(
        np.log10(E_shifted)
    )

    Flux_LIS_shifted = np.power(
        10.0,
        logFlux_LIS_shifted
    )

    # Calculate the modulation factor using the external function
    modulation_factor = solmod(
        E_mod,
        phi_eff,
        Mass
    )

    # Apply solar modulation
    Flux_mod = Flux_LIS_shifted * modulation_factor

    return E_mod, Flux_mod
