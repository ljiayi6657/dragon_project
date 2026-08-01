import numpy as np



def chisquare(obs, exp, error, dof = None):
    """
    This function is used to calculate the chi-square value/reduced chi-square value (depends on if dof is given). If dof is given, reduced chi-square value will be returned, otherwise chi-square value will be returned.

    Inputs:
    obs (nparray)      : Observed data.
    exp (nparray)      : Expected data.
    error (nparray)    : Error associated with observed data.
    dof (int, optional): Degree of freedom.

    Outputs:
    chi2 (float): Chi-square value or reduced chi-square value.

    KEYWORDS: chi-square, reduced chi-square
    """
    if len(obs) != len(exp) or len(obs) != len(error):
        print("Error: Length of lists do not match. (chisquare)")
    elif dof is None:
        chi2 = np.sum( ((obs - exp) / error) ** 2 )
        return chi2
    elif isinstance(dof, int):
        chi2 = np.sum( ((obs - exp) / error) ** 2 ) / dof
        return chi2
    else:
        print("Error: dof should be an integer. (chisquare)")
        return None