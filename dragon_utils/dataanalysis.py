from __future__ import print_function
import os, sys, time, math, pickle
import numpy as np
from scipy.interpolate import interp1d
from bisect import bisect_left



def interp(x, y, interpolatetype):
    """
    This function is used to interporlate data in log-log space.

    Inputs:
    x (nparray)          : x data.
    y (nparray)          : y data.
    interpolatetype (str): Type of interpolation method, e.g., 'linear', 'cubic', etc.

    Outputs:
    f (function): Interpolation function.
    KEYWORDS: interpolation
    """
        
    if len(x) < 2:
        print("Error: Not enough valid data points for interpolation. (interp)")
        return lambda x: np.zeros_like(x) if hasattr(x, 'shape') else 0.0
    
    if interpolatetype == 'linear':
        f = interp1d(x, y, kind='linear', fill_value="extrapolate")
    elif interpolatetype == 'cubic':
        f = interp1d(x, y, kind='cubic', fill_value="extrapolate")
    else:
        print("Error: Unsupported interpolation type. (interp)")
    
    return f
 




def interBCratio(DRAGON_output, BCratio_obs, interpolatetype):
    """
    This function is used to interporlate the BC ratio from DRAGON output to match the observed BC ratio. Which can be helpful for chi-square analysis... etc.

    Inputs:
    DRAGON_output (dict) : A dictionary of DRAGON output data read by readDRAGON.
    BCratio_obs (dict)   : Observed BCratio read by datareader.
    interpolatetype (str): Type of interpolation method, e.g., 'linear', 'cubic', etc.

    Outputs:
    BCratio_interp (nparray): Interpolated BC ratio matching the observed value.
    BCratio_Orig (nparray)  : Original BC ratio from DRAGON output.
    Elist_Orig (nparray)    : Original Elist from DRAGON output.

    KEYWORDS: BCratio, interpolation, chi-sqaure
    """

    # Extract original BC ratio and Elist from DRAGON output
    NUC_5010 = np.array([value[14] for value in DRAGON_output.values()])
    NUC_5011 = np.array([value[15] for value in DRAGON_output.values()])
    NUC_6012 = np.array([value[16] for value in DRAGON_output.values()])
    NUC_6013_= np.array([value[17] for value in DRAGON_output.values()])

    BCratio_Orig = (NUC_5010 + NUC_5011) / (NUC_6012 + NUC_6013_)
    Elist_Orig   = list(DRAGON_output.keys())

    # Extract observed BC ratio and Elist
    #BCrat_obs= np.array([value[0] for value in BCratio_obs.values()])
    Elist_obs  = list(BCratio_obs.keys())

    # Transfer to log-space
    logElist_Orig= np.log10(Elist_Orig)
    logElist_obs = np.log10(Elist_obs)

    if interpolatetype == 'linear':
        f = interp1d(logElist_Orig, BCratio_Orig, kind='linear', fill_value="extrapolate")
    elif interpolatetype == 'cubic':
        f = interp1d(logElist_Orig, BCratio_Orig, kind='cubic', fill_value="extrapolate")
    else:
        print("Error: Unsupported interpolation type. (interBCratio)")

    BCratio_interp = f(logElist_obs)



    return BCratio_interp, BCratio_Orig, Elist_Orig






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
   




def solmod(Ek,phi,M):
    return Ek*(Ek+2.0*M)/((Ek+phi)*(Ek+phi+2.0*M))

def SM_output(Elist, Flux, PhiP=0.5, Mass = 0.938, output_energies=None):
    """
    Apply solar modulation to DRAGON output proton flux spectrum.
    
    This function takes a DRAGON output dictionary (as read by readDRAGON),
    applies solar modulation using the force-field approximation, and returns
    the modulated spectrum.
    
    Inputs:
    Flux (nparray): Proton flux array from DRAGON output
    Elist (nparray): Energy array from DRAGON output
                         and values are lists with proton flux as the first element [0]
    PhiP (float): Solar modulation potential in GV (default: 0.5)
    Mass (float): Particle mass in GeV (default: 0.938 for portons)
    output_energies (array, optional): Energy array for output. If None, uses input energies.
    
    Outputs:
    E_mod (nparray): Energy array (GeV)
    Flux_mod (nparray): Modulated proton flux array
    
    Keywords: solar modulation, DRAGON, proton flux
    """
    
    # Ensure positive flux values for interpolation
    Flux = np.maximum(Flux, 1e-30)
    
    # Proton mass (GeV)
    M = Mass
    
    # Create interpolator for LIS (Local Interstellar Spectrum)
    # Use log-log interpolation for better accuracy with power-law spectra
    logE = np.log10(Elist)
    logFlux = np.log10(Flux)
    
    # Create interpolator with extrapolation
    # Use linear extrapolation for values outside the original range
    f_lis = interp1d(logE, logFlux, kind='linear', 
                     fill_value='extrapolate', 
                     bounds_error=False)
    
    # Determine output energy array
    if output_energies is None:
        E_mod = Elist
    else:
        E_mod = np.array(output_energies)
    
    # Apply solar modulation to each energy point
    Flux_mod = np.zeros_like(E_mod, dtype=float)
    
    for i, E in enumerate(E_mod):
        # Skip non-positive energies
        if E <= 0:
            Flux_mod[i] = 0.0
            continue
            
        # Calculate LIS at shifted energy (E + PhiP)
        E_shifted = E + PhiP
        
        # Interpolate LIS at shifted energy (in log space)
        if E_shifted > 0:
            logE_shifted = np.log10(E_shifted)
            logFlux_LIS = f_lis(logE_shifted)
            Flux_LIS = 10**logFlux_LIS
            # Ensure non-negative flux
            Flux_LIS = max(Flux_LIS, 0.0)
        else:
            Flux_LIS = 0.0
        
        # Calculate solar modulation factor
        solmodfact = solmod(E, PhiP, M)
        
        # Apply modulation: J_mod(E) = J_LIS(E + PhiP) * solmod(E, PhiP, M)
        Flux_mod[i] = Flux_LIS * solmodfact
    
    return E_mod, Flux_mod



def loglog_interp(E_Orig, y_Orig, E_obs, interpolatetype):
    """
    This function is used to interporlate data in log-log space.

    Inputs:
    E_Orig (nparray)          : Original energy data.
    y_Orig (nparray)          : Original y data.
    E_obs (nparray)           : Energy data to interpolate to.
    interpolatetype (str): Type of interpolation method, e.g., 'linear', 'cubic', etc.

    Outputs:
    y_interp (nparray): Interpolated y data at E_obs.
    """

    # Transfer to log-space
    logE_Orig= np.log10(E_Orig)
    logE_obs = np.log10(E_obs)
    logy_Orig= np.log10(y_Orig)


    if interpolatetype == 'linear':
        f = interp1d(logE_Orig, logy_Orig, kind='linear', fill_value="extrapolate")
    elif interpolatetype == 'cubic':
        f = interp1d(logE_Orig, logy_Orig, kind='cubic', fill_value="extrapolate")
    else:
        print("Error: Unsupported interpolation type. (loglog_interp)")

    logy_interp = f(logE_obs)
    y_interp = 10**logy_interp

    return y_interp


def makesecflx(flx):
    e=[]
    normflx=[]
    for i in range(5000):
        e=10**(i*0.001)
        edr=sorted(flx.keys())
        dragp=0.0
        for j in range(len(edr)):
            if edr[j]>e:
                x1=edr[j-1]
                x2=edr[j]
                y1=flx[edr[j-1]]
                y2=flx[edr[j]]
                f=(e-x1)/(x2-x1)
                dragp=pow(y1,1.0-f)*pow(y2,f)
                break
        normflx.append(dragp)
        #print("%e  %e"%(e,normflx[i]))
    print(len(normflx))
    return normflx

def saveresults(rfn,results):
    sfile=open(rfn,'wb')
    pickle.dump(results, sfile,protocol=2)
    sfile.close()