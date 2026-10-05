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






def chisquare(obs, exp, error, dof=None, covariance=None, return_points=False, positive=True):
    """Use the validated project chi-square implementation."""
    from dragon_utils.data_processing.statistic_analysis import chisquare as evalchi
    return evalchi(obs, exp, error, dof, covariance, return_points, positive)
   




def solmod(Ek,phi,M):
    return Ek*(Ek+2.0*M)/((Ek+phi)*(Ek+phi+2.0*M))

def SM_output(Elist, Flux, PhiP=0.5, Mass=0.938, output_energies=None,
              allow_extrapolation=False, charge=1, massnum=1):
    """Apply the validated isotope-aware force-field calculation."""
    from dragon_utils.data_processing.physics import SM_output as modulate
    return modulate(Elist, Flux, PhiP, Mass, output_energies,
                    allow_extrapolation, charge, massnum)



def loglog_interp(E_Orig, y_Orig, E_obs, interpolatetype):
    """Interpolate positive spectra in log-log space without extrapolation."""
    from dragon_utils.data_processing.flux import interp as sample
    return sample(E_Orig, y_Orig, interpolatetype, logx=True, logy=True)(E_obs)


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
