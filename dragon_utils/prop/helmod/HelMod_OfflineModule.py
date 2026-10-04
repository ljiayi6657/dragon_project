#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
--------------- Modulation Module for HelMod-4 -------------------
This module read GALPROP or TXT files containing LIS spectra and 
evaluate Solar modulation according to HelMod-4 output files.
The module can be used as stand-alone python script or as a library.

Documentation: http://www.helmod.org/
for Citing please refer to 
- HelMod calculator (version 4.1)
- M J Boschini, S Della Torre, M Gervasi, G La Vacca and P G Rancoita. The HelMod Model in the Works for Inner and Outer Heliosphere: from AMS to Voyager Probes Observations. Adv. Space Res. 64(12):2459 - 2476, 2019, doi:10.1016/j.asr.2019.04.007 ArXiv:1903.07501.
------------------------------------------------------------------

"""
__author__ = "Stefano Della Torre"
__copyright__ = "Copyright 2020, INFN Milano-Bicocca"
__credits__ = ["Nicolò Masi","Giuseppe La Vacca"]           #includes people who reported bug fixes, made suggestions, etc. but did not actually write the code.
__license__ = "GPL"
__version__ = "version 4.1 - subBranch 1.1.05 (Nov 2021)"
__maintainer__ = "Stefano Della Torre"          #should be the person who will fix bugs and make improvements if imported.
__email__ = "stefano.dellatorre@mib.infn.it"
__status__ = "Development"                  #"Prototype", "Development", or "Production".
#---------------------------------------------------------------
#---------------- Developer comment line (for DEBUG only) ------
# last error flag #1115#
DEBUG = False
#---------------------------------------------------------------
#---------------- Library --------------------------------------
import numpy as np
from scipy.interpolate import interp1d
import astropy.io.fits as pyfits
import os.path
import glob
#---------------------------------------------------------------
#---------------- Generic purpose functions --------------------
# ========= convert to np.array =============
def To_np_array(v):
    if not isinstance(v,(np.ndarray,)):
        v = np.asarray(v)
    return v
# ========= Beta Evaluation from Tkin ==========
def beta_(T,T0):
    #if DEBUG:
      #print "BETA %f %f" %(T,T0)
    tt = T + T0
    t2 = tt + T0
    beta = np.sqrt(T*t2)/tt
    return beta

# ========= Rigidity Evaluation from Tkin ==========
def Rigidity(T,MassNumber=1.,Z=1.):
    MassNumber=float(MassNumber)
    Z=float(Z)
    T0=0.931494061
    if np.fabs(Z)==1.:
        T0 = 0.938272046
    if MassNumber==0.:
        T0 = 5.11e-4
        MassNumber = 1.
    return MassNumber/np.fabs(Z)*np.sqrt(T*(T+2.*T0))

# ========= Tkin Evaluation from Rigidity ==========
def Energy(R,MassNumber=1.,Z=1.):
    MassNumber=float(MassNumber)
    Z=float(Z)
    T0=0.931494061
    if np.fabs(Z)==1.:
        T0 = 0.938272046
    if MassNumber==0.:
        T0 = 5.11e-4
        MassNumber = 1.
    return np.sqrt((Z*Z)/(MassNumber*MassNumber)*(R*R)+(T0*T0))-T0;

# ========= Flux conversion factor from Rigidity to Tkin ==========
def dT_dR(T=1,R=1,MassNumber=1.,Z=1.):
    MassNumber=float(MassNumber)
    Z=float(Z)
    T0=0.931494061
    if np.fabs(Z)==1.:
        T0 = 0.938272046
    if MassNumber==0.:
        T0 = 5.11e-4
        MassNumber = 1.
    return Z*Z/(MassNumber*MassNumber)*R/(T+T0)

# ========= Flux conversion factor from Tkin to Rigidity ==========
def dR_dT(T=1,R=1,MassNumber=1.,Z=1.):
    MassNumber=float(MassNumber)
    Z=float(Z)
    T0=0.931494061
    if np.fabs(Z)==1.:
        T0 = 0.938272046
    if MassNumber==0.:
        T0 = 5.11e-4
        MassNumber = 1.
    return MassNumber/np.fabs(Z)*(T+T0)/np.sqrt(T*(T+2.*T0))

# ========= Flux Conversion from Tkin --> Rigi ===================
def Tkin2Rigi_FluxConversione(Xval,Spectra,MassNumber=1.,Z=1.):
    Rigi = np.array([ Rigidity(T,MassNumber=MassNumber,Z=Z) for T in Xval ])
    Flux = np.array([ Flux*dT_dR(T=T,R=R,MassNumber=MassNumber,Z=Z) for T,R,Flux in zip(Xval,Rigi,Spectra) ])
    return (Rigi,Flux)

# ========= Find Nearest value/index in a np.array ============
def find_nearest_idx(array, value):
    array = To_np_array(array)
    return (np.abs(array - value)).argmin()

def find_nearest_value(array, value):
    array = To_np_array(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]

# ======== Create a Directory ===================================
def mkdir_p(path):
    import os       # OS directory manager
    import errno    # error names
    # --- this function create a folder and check if this already exist ( like mkdir -p comand)
    try:
       os.makedirs(path)
    except OSError as exc: # Python >2.5
       if exc.errno == errno.EEXIST and os.path.isdir(path):
          pass
# ======= Check If Dir Exist ===================================
def CheckDirExist(FilePath):
    """Check if a Dir Exist
        return True  if OK
        return False if errors occours
    """
    if FilePath=='' : # controlla se FilePath contiente caratteri
        print ("CheckDirExist:: ERROR:: path string is empty")
        return False;                 
    # if not FilePath.endswith('/'): #verifica se il nome finisce con '/'' altrimenti aggiungilo
    #     FilePath+='/' 
    if not os.path.isdir(FilePath):
        print ("CheckDirExist:: ERROR:: dir %s not found"%(FilePath))
        return False
    if DEBUG:
        print("DEBUGLINE::CheckDirExist Path--> %s found"%(FilePath))
    return True

# ======= Linear Interpolation in log scale of vx,vy array using Newvx bins ======
def LinLogInterpolation(vx,vy,Newvx):
    vx = To_np_array(vx)
    vy = To_np_array(vy)
    Newvx = To_np_array(Newvx)
    # convert all in LogLogscale for linear interpolation
    Lvx,Lvy = np.log10(vx),np.log10(vy)
    LNewvx  = np.log10(Newvx)
    # Linear Interpolation 
    ILvy = interp1d(Lvx,Lvy,bounds_error=False,fill_value='extrapolate')(LNewvx)
    # return array in nominal scale
    return 10**ILvy
    
#---------------------------------------------------------------

# --------------------- Get Particle Information ---------------
def particleProperty(ExpNameKey):
    """ From the ExpNameKey extract the information about the particle  
        to simplify the reading of simulations name we follow this notation
        isotopes evaluated along with other with same Z --> 4 letter name + A OR full isotpes name
        isotopes evaluated standalone                   --> Chemical Symbol + A

    """
    if ExpNameKey.startswith("Electron"):      
        Z= -1.
        T0=5.109989e-04
        Isotopes_Name=['Electron',]
        Isotopes_A   =[   0.     ,]
    elif ExpNameKey.startswith("Positron"):         #
        Z= 1.
        T0=5.109989e-04
        Isotopes_Name=['Positron',]
        Isotopes_A   =[   0.     ,]
    #-------------------------------------------#
    elif ExpNameKey.startswith("Proton"):
        Z= 1.
        T0=0.938272
        Isotopes_Name=['Proton','Deuteron']#,'Tritium']
        Isotopes_A   =[   1.   ,  2.       ]#,    3.   ]
    elif ExpNameKey.startswith("Deuterium"):        
        Z= 1.
        T0=0.938272
        Isotopes_Name=['Deuterium',]
        Isotopes_A   =[    2.     ,]
    elif ExpNameKey.startswith("H2"):        
        Z= 1.
        T0=0.938272
        Isotopes_Name=['H2',]
        Isotopes_A   =[ 2. ,]
    elif ExpNameKey.startswith("H1"):        
        Z= 1.
        T0=0.938272
        Isotopes_Name=['H1',]
        Isotopes_A   =[ 1. ,]        
    #-------------------------------------------#
    elif ExpNameKey.startswith("Antiproton"):   
        Z= -1.
        T0=0.938272
        Isotopes_Name=['Antiproton',]
        Isotopes_A   =[    1.     ,]
    #-------------------------------------------#
    elif ExpNameKey.startswith("Helium"):       
        Z= 2.
        T0=0.931494061
        Isotopes_Name=['Helium','He-3']
        Isotopes_A   =[   4.   ,  3.  ]
    #-------------------------------------------#
    elif ExpNameKey.startswith("He4"):
        Z= 2.
        T0=0.931494061
        Isotopes_Name=['He4']
        Isotopes_A   =[  4. ]        
    #-------------------------------------------#
    elif ExpNameKey.startswith("He3") or ExpNameKey.startswith("He-3"):
        Z= 2.
        T0=0.931494061
        Isotopes_Name=['He3']
        Isotopes_A   =[  3. ]
    #-------------------------------------------#
    elif ExpNameKey.startswith("Lithium"):      
        Z= 3.
        T0=0.931494061
        Isotopes_Name=['Lithium','Lith6']
        Isotopes_A   =[   7.    ,  6.  ]
    #-------------------------------------------#
    elif ExpNameKey.startswith("Li6"):      
        Z= 3.
        T0=0.931494061
        Isotopes_Name=['Li6',]
        Isotopes_A   =[  6.   ,]
    #-------------------------------------------#
    elif ExpNameKey.startswith("Li7"):      
        Z= 3.
        T0=0.931494061
        Isotopes_Name=['Li7',]
        Isotopes_A   =[  7. ,]   
    #-------------------------------------------#
    elif ExpNameKey.startswith("Beryllium"): 
        Z= 4.
        T0=0.931494061
        Isotopes_Name=['Beryllium','Beryl10','Beryl7']
        Isotopes_A   =[9.         ,   10.   ,    7   ] 
    #-------------------------------------------#
    elif ExpNameKey.startswith("Be7"): 
        Z= 4.
        T0=0.931494061
        Isotopes_Name=['Be7']
        Isotopes_A   =[   7. ]            
    #-------------------------------------------#
    elif ExpNameKey.startswith("Be9"): 
        Z= 4.
        T0=0.931494061
        Isotopes_Name=['Be9']
        Isotopes_A   =[   9. ]      
    #-------------------------------------------#
    elif ExpNameKey.startswith("Be10"): 
        Z= 4.
        T0=0.931494061
        Isotopes_Name=['Be10']
        Isotopes_A   =[   10. ]                
    #-------------------------------------------# 
    elif ExpNameKey.startswith("Boron"): 
        Z= 5.
        T0=0.931494061
        Isotopes_Name=['Boron','Bor10']
        Isotopes_A   =[  11.  ,   10. ]     
    #-------------------------------------------# 
    elif ExpNameKey.startswith("B10"): 
        Z= 5.
        T0=0.931494061
        Isotopes_Name=['B10']
        Isotopes_A   =[  10.]                              
    #-------------------------------------------# 
    elif ExpNameKey.startswith("Carbon"):
        Z= 6.
        T0=0.931494061
        Isotopes_Name=['Carbon','Carb13']
        Isotopes_A   =[  12.   ,   13.  ] 
    #-------------------------------------------# 
    elif ExpNameKey.startswith("Nitrogen"):
        Z= 7.
        T0=0.931494061
        Isotopes_Name=['Nitrogen','Nitro15']
        Isotopes_A   =[    14.   ,   15.   ]
    #-------------------------------------------# 
    elif ExpNameKey.startswith("Oxygen"):      
        Z= 8.
        T0=0.931494061
        Isotopes_Name=['Oxygen','Oxyg18','Oxyg17']
        Isotopes_A   =[  16.   ,   18.  ,   17   ]  
    #-------------------------------------------# 
    elif ExpNameKey.startswith("Fluorine"):      
        Z= 9.
        T0=0.931494061
        Isotopes_Name=['Fluorine'] #,'Fluo18']
        Isotopes_A   =[  19.     ] #,   18.  ]  
    #-------------------------------------------# 
    elif ExpNameKey.startswith("Neon"):      
        Z= 10.
        T0=0.931494061
        Isotopes_Name=['Neon','Ne21','Ne22']
        Isotopes_A   =[  20. ,  21. ,  22. ]  
    #-------------------------------------------# 
    elif ExpNameKey.startswith("Sodium"):      
        Z= 11.
        T0=0.931494061
        Isotopes_Name=['Sodium']#,'Sodi22']
        Isotopes_A   =[  23.   ]#,  22.   ]  
    #-------------------------------------------#     
    elif ExpNameKey.startswith("Magnesium"):      
        Z= 12.
        T0=0.931494061
        Isotopes_Name=['Magnesium','Magn25','Magn26']
        Isotopes_A   =[  24.      ,  25.   ,  26.   ]  
    #-------------------------------------------#  
    elif ExpNameKey.startswith("Aluminum"):      
        Z= 13.
        T0=0.931494061
        Isotopes_Name=['Aluminum','Alum26']
        Isotopes_A   =[    27.    ,  26.   ]  
    #-------------------------------------------#               
    elif ExpNameKey.startswith("Silicon"):
        Z= 14.
        T0=0.931494061
        Isotopes_Name=['Silicon','Silic29','Silic30']
        Isotopes_A   =[  28.   ,   29.    ,    30.   ]    
    #-------------------------------------------#               
    elif ExpNameKey.startswith("Phosphorus"):
        Z= 15.
        T0=0.931494061
        Isotopes_Name=['Phosphorus']#,'Phos32','Phos33']
        Isotopes_A   =[  31.       ]#,   32.  ,  33.   ]   
    #-------------------------------------------#               
    elif ExpNameKey.startswith("Sulfur"):
        Z= 16.
        T0=0.931494061
        Isotopes_Name=['Sulfur','Sulf33','Sulf34','Sulf36']#,'Sulf35']
        Isotopes_A   =[  32.   ,   33.  ,  34.   ,  36.   ]# ,   35. ] 
    #-------------------------------------------#               
    elif ExpNameKey.startswith("S32"):
        Z= 16.
        T0=0.931494061
        Isotopes_Name=['S32']
        Isotopes_A   =[  32.    ]         
    #-------------------------------------------#               
    elif ExpNameKey.startswith("S33"):
        Z= 16.
        T0=0.931494061
        Isotopes_Name=['S33']
        Isotopes_A   =[  33.    ]           
    #-------------------------------------------#               
    elif ExpNameKey.startswith("S34"):
        Z= 16.
        T0=0.931494061
        Isotopes_Name=['S34']
        Isotopes_A   =[  34.    ]   
    #-------------------------------------------#               
    elif ExpNameKey.startswith("S36"):
        Z= 16.
        T0=0.931494061
        Isotopes_Name=['S36']
        Isotopes_A   =[  36.    ]           
    #-------------------------------------------#               
    elif ExpNameKey.startswith("Chlorine"):
        Z= 17.
        T0=0.931494061
        Isotopes_Name=['Chlorine','Chlo36','Chlo37']
        Isotopes_A   =[  35.     ,   36.  ,  37.   ]
    #-------------------------------------------#               
    elif ExpNameKey.startswith("Argon"):
        Z= 18.
        T0=0.931494061
        Isotopes_Name=['Argon','Argo36','Argo37','Argo38']#,'Argo39']#,'Argo42']
        Isotopes_A   =[  40.  ,     36.,     37.,     38.]#,     39.]#,     42.]
    #-------------------------------------------#               
    elif ExpNameKey.startswith("Ar40"):
        Z= 18.
        T0=0.931494061
        Isotopes_Name=['Ar40']
        Isotopes_A   =[  40.    ] 
    #-------------------------------------------#               
    elif ExpNameKey.startswith("Ar36"):
        Z= 18.
        T0=0.931494061
        Isotopes_Name=['Ar36']
        Isotopes_A   =[  36.    ]    
    #-------------------------------------------#               
    elif ExpNameKey.startswith("Ar37"):
        Z= 18.
        T0=0.931494061
        Isotopes_Name=['Ar37']
        Isotopes_A   =[  37.    ]    
    #-------------------------------------------#               
    elif ExpNameKey.startswith("Ar38"):
        Z= 18.
        T0=0.931494061
        Isotopes_Name=['Ar38']
        Isotopes_A   =[  38.    ]            
    #-------------------------------------------#               
    elif ExpNameKey.startswith("Potassium"):
        Z= 19.
        T0=0.931494061
        Isotopes_Name=['Potassium','Pota40','Pota41']
        Isotopes_A   =[  39.      ,   40.  ,     41.]
    #-------------------------------------------#    
    elif ExpNameKey.startswith("Calcium"):           
        Z= 20.
        T0=0.931494061
        Isotopes_Name=['Calcium','Calc41','Calc42','Calc43','Calc44','Calc46','Calc48']
        Isotopes_A   =[  40.    ,     41.,     42.,     43.,     44.,     46.,     48.] 
    #-------------------------------------------#    
    elif ExpNameKey.startswith("Ca40"):           
        Z= 20.
        T0=0.931494061
        Isotopes_Name=['Ca40']
        Isotopes_A   =[  40.    ]
    #-------------------------------------------#    
    elif ExpNameKey.startswith("Ca41"):           
        Z= 20.
        T0=0.931494061
        Isotopes_Name=['Ca41']
        Isotopes_A   =[  41.    ]
    #-------------------------------------------#    
    elif ExpNameKey.startswith("Ca42"):           
        Z= 20.
        T0=0.931494061
        Isotopes_Name=['Ca42']
        Isotopes_A   =[  42.    ]
    #-------------------------------------------#    
    elif ExpNameKey.startswith("Ca43"):           
        Z= 20.
        T0=0.931494061
        Isotopes_Name=['Ca43']
        Isotopes_A   =[  43.    ]
    #-------------------------------------------#    
    elif ExpNameKey.startswith("Ca44"):           
        Z= 20.
        T0=0.931494061
        Isotopes_Name=['Ca44']
        Isotopes_A   =[  44.    ]        
    #-------------------------------------------#    
    elif ExpNameKey.startswith("Scandium"):           
        Z= 21.
        T0=0.931494061
        Isotopes_Name=['Scandium']#,'Scan46']
        Isotopes_A   =[  45.     ]#,     46.] 
    #-------------------------------------------#       
    elif ExpNameKey.startswith("Titanium"):           
        Z= 22.
        T0=0.931494061
        Isotopes_Name=['Titanium','Tita44','Tita46','Tita47','Tita49','Tita50']
        Isotopes_A   =[  48.     ,     44.,     46.,     47.,     49.,     50.] 
    #-------------------------------------------#        
    elif ExpNameKey.startswith("Vanadium"):           
        Z= 23.
        T0=0.931494061
        Isotopes_Name=['Vanadium','Vana49','Vana50']
        Isotopes_A   =[  51.     ,     49.,     50.] 
    #-------------------------------------------#   
    elif ExpNameKey.startswith("Chromium"):           
        Z= 24.
        T0=0.931494061
        Isotopes_Name=['Chromium','Chro50','Chro51','Chro53','Chro54']#,'Chro48'
        Isotopes_A   =[  52.     ,     50.,     51.,     53.,     54.]#,     48.
    #-------------------------------------------#   
    elif ExpNameKey.startswith("Manganese"):           
        Z= 25.
        T0=0.931494061
        Isotopes_Name=['Manganese','Mang53','Mang54']#,'Mang52']
        Isotopes_A   =[  55.      ,     53.,     54.]#,     52.]
    #-------------------------------------------#
    elif ExpNameKey.startswith("Iron"):           
        Z= 26.
        T0=0.931494061
        Isotopes_Name=['Iron','Iro54','Iro55','Iro57','Iro58','Iro60']
        Isotopes_A   =[  56. ,   54. ,   55.  ,   57. ,  58.  ,  60   ]
    #-------------------------------------------#
    elif ExpNameKey.startswith("Fe60"):           
        Z= 26.
        T0=0.931494061
        Isotopes_Name=['Fe60']
        Isotopes_A   =[  60. ]    
    #-------------------------------------------#
    elif ExpNameKey.startswith("Fe56"):           
        Z= 26.
        T0=0.931494061
        Isotopes_Name=['Fe56']
        Isotopes_A   =[  56. ]          
    #-------------------------------------------#
    elif ExpNameKey.startswith("Cobalt"):
        Z= 27.
        T0=0.931494061
        Isotopes_Name=['Cobalt','Coba57']#,'Coba58','Coba56','Coba60']
        Isotopes_A   =[  59.   ,  57.   ]#,   58.  ,   56.,   60.  ]
    #-------------------------------------------#
    elif ExpNameKey.startswith("Co59"):
        Z= 27.
        T0=0.931494061
        Isotopes_Name=['Co59']
        Isotopes_A   =[  59.    ]
    #-------------------------------------------#
    elif ExpNameKey.startswith("Co57"):
        Z= 27.
        T0=0.931494061
        Isotopes_Name=['Co57']
        Isotopes_A   =[  57.    ]
    #-------------------------------------------#
    elif ExpNameKey.startswith("Nickel"):
        Z= 28.
        T0=0.931494061
        Isotopes_Name=['Nickel','Nick56','Nick59','Nick60','Nick61','Nick62','Nick64']
        Isotopes_A   =[  58.   ,   56.  ,   59.  ,    60. ,    61. ,   62.  ,   64.  ]
    #-------------------------------------------#
    elif ExpNameKey.startswith("Ni60"):
        Z= 28.
        T0=0.931494061
        Isotopes_Name=['Ni60']
        Isotopes_A   =[  60. ]
    else:
          print("ERROR::#1110#::cannot recognize the type of particle to modulate.")
          exit(1)


    return {"T0":T0,"Z":Z,"Isotopes_A":Isotopes_A,"Isotopes_Name":Isotopes_Name}



# --------------------- Module Class main core -----------------
# this class aim to load and manage modulation for input LIS file
class SolarModulation:
    # =================
    def __init__(self,InputLISFile, GALPROPInput=True, ERsun=8.33):
        """Open Fits File and Store particle flux in a dictionary 'ParticleFlux'
        We store it as a dictionary containing a dictionary, containing an array, where the first key is Z, the second key is A and then we have primaries, secondaries in an array
        - The option GALPROPInput select if LIS is a galprop fits file or a generic txt file
        """ 
        # ===
        # init local variables
        self.HelMOD_RAW_FILES=""  # path of HelMod Archive
        self.ParametersSet=""     # Name of HelMod Simulation Configuration
        # ===
        # check the input type, if True=Galprop fits file, if False=TXT
        # note that with TXT file no istotopic mix can be provided
        self.GFTXT=GALPROPInput
        if DEBUG:
            if self.GFTXT:
                print("DEBUG::LIS is a GALPROP File")
            else:
                print("DEBUG::LIS is a TXT File ")
            print("Input LIS File=%s"%(InputLISFile))
        # === 

        # ===
        # .. Load LIs from GALPROP File
        if self.GFTXT:
            galdefid=InputLISFile
            hdulist = pyfits.open(galdefid)         # open fits file
            if DEBUG:
                hdulist.info()
            data = hdulist[0].data                  # assign data structure di data
            #Find out which indices to interpolate over for Rsun
            self.Rsun=ERsun     # Earth position in the Galaxy
            R = (np.arange(int(hdulist[0].header["NAXIS1"]))) * hdulist[0].header["CDELT1"] + hdulist[0].header["CRVAL1"]
            inds = []
            weights = []
            if (R[0] > self.Rsun):
                inds.append(0)
                weights.append(1)
            elif (R[-1] <= self.Rsun):
                inds.append(-1)
                weights.append(1)
            else:
                for i in range(len(R)-1):
                    if (R[i] <= self.Rsun and self.Rsun < R[i+1]):
                        inds.append(i)
                        inds.append(i+1)
                        weights.append((R[i+1]-self.Rsun)/(R[i+1]-R[i]))
                        weights.append((self.Rsun-R[i])/(R[i+1]-R[i]))
                        break
            if DEBUG:
                    print("DEBUGLINE:: R=",R)
                    print("DEBUGLINE:: weights=",weights)
                    print("DEBUGLINE:: inds=",inds)

            # --------------------------------------------
            # Calculate the energy for the spectral points.. note that Energy is in MeV
            self.energy = 10**(float(hdulist[0].header["CRVAL3"]) + np.arange(int(hdulist[0].header["NAXIS3"]))*float(hdulist[0].header["CDELT3"]))

            # --------------------------------------------
            #Parse the header, looking for Nuclei definitions
            self.ParticleFlux = {}

            Nnuclei = hdulist[0].header["NAXIS4"]
            for i in range(1, Nnuclei+1):
                    id = "%03d" % i
                    Z = int(hdulist[0].header["NUCZ"+id])
                    A = int(hdulist[0].header["NUCA"+id])
                    K = int(hdulist[0].header["NUCK"+id])
                    if DEBUG:
                            print("id=%s Z=%d A=%d K=%d"%(id,Z,A,K))
                    #Add the data to the ParticleFlux dictionary
                    if Z not in self.ParticleFlux:
                            self.ParticleFlux[Z] = {}
                    if A not in self.ParticleFlux[Z]:
                            self.ParticleFlux[Z][A] = {}
                    if K not in self.ParticleFlux[Z][A]:
                            self.ParticleFlux[Z][A][K] = []
                            # data structure
                            #    - Particle type, identified by "id", the header allows to identify which particle is
                            #    |  - Energy Axis, ":" takes all elements
                            #    |  | - not used
                            #    |  | |  - distance from Galaxy center: inds is a list of position nearest to Earth position (Rsun)
                            #    |  | |  |
                    d = ( (data[i-1,:,0,inds].swapaxes(0,1)) * np.array(weights) ).sum(axis=1) # real solution is interpolation between the nearest solution to Earh position in the Galaxy (inds)
                    self.ParticleFlux[Z][A][K].append(1e7*d/self.energy**2) #1e7 is conversion from [cm^2 MeV]^-1 --> [m^2 GeV]^-1
                    #print (Z,A,K)
                    #print self.ParticleFlux[Z][A][K]

            ## self.ParticleFlux[Z][A][K] contains the particle flux for all considered species  galprop convention wants that for same combiantion of Z,A,K firsts are secondaries, latter Primary
            self.energy = self.energy/1e3 # convert energy scale from MeV to GeV
            #if A>1:
            #  self.energy = self.energy/float(A)
            hdulist.close()

        # ===
        # ... Load LIS From TXT File
        else:
            self.energy,self.ParticleFlux=np.loadtxt(InputLISFile, unpack=True, usecols=(0,1))
        # ===

    # =================
    def addExtraSource(self,FileExtraSource, units='GeV'):
        """ open a two column txt file that contain the value of additional source to be added to considered lepton LISs
        + read extra source file (ES)
        + for each energy in LIS
            - read energy
            - find if in ES energy range
                - if not: skip
                - if yes: find ES  fluxvalue (interpolation) and add to LIS primary value
        """
        # open external file
        ExtraSource=np.loadtxt(FileExtraSource,unpack=True,usecols=(0,1))
        #order the spectra
        ExtraSource[:,ExtraSource[0,:].argsort()]
        LISExtra_Interp1d = interp1d(ExtraSource[0],ExtraSource[1],kind='cubic',bounds_error=False )
        # select lepton LIS
        A=0
        LIS_energy = self.energy
        
        if DEBUG and self.GFTXT:
            print(len(self.ParticleFlux[-1][A][0]))

        for iener in range(len(LIS_energy)):
            EnerLIS=LIS_energy[iener]
            if EnerLIS>=ExtraSource[0][0] and EnerLIS<=ExtraSource[0][-1]:
                ES=LISExtra_Interp1d(EnerLIS)
                if DEBUG:
                    print("EXTRALIS::",EnerLIS," ",ES)
                if self.GFTXT:
                    self.ParticleFlux[-1][A][0][0][iener]=self.ParticleFlux[-1][A][0][0][iener]+ES
                    self.ParticleFlux[1][A][0][0][iener] =self.ParticleFlux[1][A][0][0][iener]+ES
                else:
                    self.ParticleFlux[iener]=self.ParticleFlux[iener]+ES

    # =================
    def GetLIS(self,Z, A, K=0, Mode=0, IncludeSecondaries=True):
        """Return the LIS for species,
            mode define the kind of LIS are interested to get according to
            0: specific Z,A LIS in Kinetic Energy per nucleon
            1: specific Z,A LIS in Rigidity
            2: Summing all isotopes with same Z and same Kinetic Energy per nucleon
            3: Summing all isotopes with same Z and same Rigidity
                   return (Xbin, LIS)
                   ---------- error return status ---------
                  -1: Z does not exist in Galprop Fits
                  -2: A does not exist in Galprop Fits
                  -3: unrecognized Mode
        """
        # -------- init variables
        LISSpectra = [ 0 for T in self.energy]

        # -------- for GALPROP FILE ONLY, Check if Z is available
        if self.GFTXT:
            if (Z not in self.ParticleFlux):     # Return -1 if Z does not exist in GALPROP file
                return (-1.*np.ones(1),-1.*np.ones(1))

        # -------- load LIS Flux
        if not self.GFTXT and Mode>1: # check if TXT input or galprop: with TXT file is not possible to get mode 2 or 3
            if DEBUG: print("DEBUGLINE:: WARNING GetLIS Mode %d cannot be applied"%(Mode))
            if Mode==2: Mode=0
            if Mode==3: Mode=1
            print("WARNING:: GetLIS Mode cannot be applied as selected since you have provided TXT LIS, used Mode %d instead (0: LIS in Kinetic Energy per nucleon, 1:LIS in Rigidity)"%(Mode))
        
        # === deal Mode 0 ad 1 --> Single Isotopes case
        # in this case the LIS is composed by all primary and secondaty particles with same Z,A values
        if Mode<=1: 
            TK_bin=self.energy
            if self.GFTXT:
                # == check of A is available
                if (A not in self.ParticleFlux[Z]):     # Return -2 if A does not exist for selected Z
                            return (-2.*np.ones(1),-2.*np.ones(1))
                # ==
                TK_LISSpectra= (self.ParticleFlux[Z][A][K])[-1]   # the primary spectrum is always the last one (if exist)
                if IncludeSecondaries:                            # include secondary spectra
                    for SecInd in range(len(self.ParticleFlux[Z][A][K])-1):
                        TK_LISSpectra= TK_LISSpectra+(self.ParticleFlux[Z][A][K])[SecInd] # Sum All secondaries
            else:
                # with TXT File there is only one LIS
                TK_LISSpectra=self.ParticleFlux
                
            # == Output
            # ... mode 0: get Z,A LIS in Kinetic Energy per nucleon
            if Mode==0: 
                return (TK_bin, TK_LISSpectra) 
            # ... mode 1: get Z,A LIS in Rigidity
            elif Mode==1:
                LISRigi= np.array([ Rigidity(T,MassNumber=A,Z=Z) for T in TK_bin ])
                LISFlux= np.array([ Flux*dT_dR( T=T,R=R,MassNumber=A,Z=Z) for T,R,Flux in zip(self.energy,LISRigi,TK_LISSpectra)])
                return (LISRigi, LISFlux)
        # ==
        # .. Summing all isotopes with same Z and same Kinetic Energy per nucleon
        elif Mode==2:
            TK_LISSpectra = np.zeros_like(self.energy)
            for Aval in self.ParticleFlux[Z].keys():
                if DEBUG :
                    print("DEBUGLINE:: Aval=",Aval)
                    print("DEBUGLINE:: GETLIS combinations of Z,A,K -->",len(self.ParticleFlux[Z][Aval][K]))
                if Aval==0 and A!=0: # A=0 are positrons, these do not have to be summed with protons
                    continue
                if Aval!=0 and A==0:
                    continue
                TK_LISSpectra= TK_LISSpectra+(self.ParticleFlux[Z][Aval][K])[-1]
                if IncludeSecondaries:  # include secondary spectra
                    for SecInd in range(len(self.ParticleFlux[Z][Aval][K])-1):
                        TK_LISSpectra= TK_LISSpectra+(self.ParticleFlux[Z][Aval][K])[SecInd]        
            return (self.energy, TK_LISSpectra)

        # ==
        # .. Summing all isotopes with same Z and same Rigidity
        elif Mode==3:
            if A not in self.ParticleFlux[Z]: 
                print ("WARNING:: GETLIS, selected A=%d does not avalable..."%(A))
                if Z==1.: A=1
                else    : A=self.ParticleFlux[Z].keys()[-1]
                print ("WARNING:: GETLIS, ... used A=%d instead."%(A))
            print("WARNING Rigidity Binning Evalauted using A=",A," Z=",Z)

            Xbin= np.array([ Rigidity(T,MassNumber=A,Z=Z) for T in self.energy ])
            if DEBUG : print("LIS XBin = ",Xbin)


                    
            OutputFlux=np.zeros_like(Xbin)
            for Aval in self.ParticleFlux[Z].keys():
                if DEBUG : print ("DEBUGLINE:: Aval=",Aval)
                if Aval==0 and A!=0: # A=0 are positrons, these do not have to be summed with protons
                    continue
                if Aval!=0 and A==0:
                    continue
                if DEBUG : print ("DEBUGLINE:: Summed Aval=",Aval)

                RigiBin= np.array([ Rigidity(T,MassNumber=Aval,Z=Z) for T in self.energy ])             
                TempLisEnK=self.ParticleFlux[Z][Aval][K][-1]
                if IncludeSecondaries:  # include secondary spectra
                    for SecInd in range(len(self.ParticleFlux[Z][Aval][K])-1):
                        TempLisEnK=TempLisEnK+(self.ParticleFlux[Z][Aval][K])[SecInd]
                TempLisRigi=np.array([ Flux*dT_dR( T=T,R=R,MassNumber=Aval,Z=Z) for T,R,Flux in zip(self.energy,RigiBin,TempLisEnK) ])
                TempLisRigi_rebin = LinLogInterpolation(RigiBin,TempLisRigi,Xbin)
                OutputFlux= OutputFlux+TempLisRigi_rebin
            return (Xbin,OutputFlux)
        #---------- Unknow Mode -----------------
        return (-3.*np.ones(1),-3.*np.ones(1))

    # =================
    def SET_ArchivePath(self,FilePath):
        """Set the path where the archive is stored and simulaton can be found
            return True  if OK
            return False if errors occours
        """
        if CheckDirExist(FilePath):
            self.HelMOD_RAW_FILES=FilePath
            return True
        else:
            return False
    # =================
    def SET_ParametersSet(self,ParSet):
        """Set the simulation paremeters name
            return True  if OK
            return False if errors occours
        """
        if CheckDirExist(self.HelMOD_RAW_FILES+"/"+ParSet):
            self.ParametersSet=ParSet
            return True
        else:
            return False

    # =================
    def InfoSim(self,ExpNameKey):
        """ Check if Simulation is based on historical (P=Past) or forecast (F=Forecast) and give the proper path append
            note that archive that allow to identify this has at least 4  column in ExpList.list file
             return the name of subfolder for uncertanties 
             if old archive return empty string
        """
        for line in open(self.HelMOD_RAW_FILES+"/ExpList.list").readlines():
            if not(line.startswith("#")):
                Cols=line.split();
                if len(Cols)<4:
                    return ("",-1)
                if DEBUG: print ("DEBUGLINE::InfoSim ",Cols);
                if Cols[0] == ExpNameKey:
                    if Cols[3]=='F':
                        return "FrcstPar"
                    if Cols[3]=='P':
                        return "MeasPar"
                    return ""
                    #return ("MeasPar",Cols[3])
                    break
        return ""

    # =================
    def Spectra(self, LIS_Tkin,LIS_Flux, HelModSimPath ):
        """Return the mdulated spectra according to simualtion in HelModSimPath given the LIS in (LIS_Tkin,LIS_Flux)
           ---------- error status ---------
          -1: HelModSimPath file not exist
          -2: something wrong while opening the file (maybe empty file or corrupted)
        """ 
        RAWFilePART=HelModSimPath+"/RawMatrixFile.npz" 

        # -------------------------- Check is Simulation actually exist in the archive
        if not os.path.isfile(RAWFilePART):
            print("ERROR::Spectra() %s file not found"%(RAWFilePART))
            return (-1.*np.ones(1),-1.*np.ones(1))

        # ------------------------------
        # get the probability distribution function
        # ------------------------------
        try:
            data=np.load(RAWFilePART)
            OuterEnergy_low         = data['OuterEnergy_low']
            BounduaryDistribution   = data['BounduaryDistribution']
            InputEnergy             = data['InputEnergy']
            NGeneratedPartcle       = data['NGeneratedPartcle']
            OuterEnergy             = data['OuterEnergy']
        except:
            print("ERROR::Spectra() something wrong while opening the file ",RAWFilePART," empty file or corrupted")
            return (-2.*np.ones(1),-2.*np.ones(1))
        
        # ------------------------------
        # Interpolate LIS
        # ------------------------------
        ILIS = LinLogInterpolation(LIS_Tkin,LIS_Flux,InputEnergy)
        OLIS = LinLogInterpolation(LIS_Tkin,LIS_Flux,OuterEnergy)

        # ------------------------------
        # Evalaute Flux
        # ------------------------------
        UnNormFlux = np.zeros(len(InputEnergy))
        for indexTDet in range(len(InputEnergy)):
            #EnergyDetector = InputEnergy[indexTDet]
            Nbind = []     # number of bin used to compute flux. 
            for indexTLIS in range(len(OuterEnergy)):
                EnergyLIS = OuterEnergy[indexTLIS]
                UnNormFlux[indexTDet]+=BounduaryDistribution[indexTDet][indexTLIS]*OLIS[indexTLIS] /beta_(EnergyLIS,self.T0)
                if BounduaryDistribution[indexTDet][indexTLIS]>0: Nbind.append(indexTLIS)
            if len(Nbind)<=3:  #If the number of bin used to compute flux is 1, it means that it is a delta function. and the flux estimation could be not accurate             
                BDist=0
                for iBD in Nbind:
                    BDist+=  BounduaryDistribution[indexTDet][iBD]
                UnNormFlux[indexTDet]=BDist*ILIS[indexTDet] /beta_(InputEnergy[indexTDet],self.T0) #this trick center the LIS estimation on the output energy since the energey distribution is smaller than Bin resolution of the matrix
        J_Mod = [ UnFlux/Npart *beta_(T,self.T0) for T,UnFlux,Npart in zip(InputEnergy,UnNormFlux,NGeneratedPartcle)]
        # print J_Mod
        # -- Reverse order in the List
        EnergyBinning = np.array(InputEnergy[::-1])
        J_Mod         = np.array(J_Mod[::-1]) 
        # ------------------------------
        # DEBUG PLOT
        # ------------------------------
        if DEBUG:
            import matplotlib.pyplot as plt
            plt.plot(LIS_Tkin,LIS_Flux,"-")
            plt.plot(OuterEnergy,ILIS,"-")
            plt.plot(np.array(EnergyBinning), np.array(J_Mod),".")
            plt.xscale('log')
            plt.yscale('log')
            plt.show()
        # ------------------------------
        return (EnergyBinning,J_Mod)  

    # =================
    def ExecuteModulation(self, Z,A,HelModSimPath,OutputX ):
        """ Macro for executing Modulation including the uncertanties. """

        # ... init Array with first (main) isotope
        LIS_Tkin,LIS_Flux   = self.GetLIS(Z, A, Mode=0)
        OutputBinning,J_Mod = self.Spectra(LIS_Tkin,LIS_Flux, HelModSimPath )
        if OutputBinning[0]<0:
            return (OutputBinning,J_Mod,J_Mod,J_Mod,J_Mod,J_Mod)
        J_LIS = LinLogInterpolation(LIS_Tkin,LIS_Flux,OutputBinning)
        # ... Convert in the unit of the ouput -- this should be done olny if OutputX='Rigi'
        if OutputX=='Rigi': 
            ROutputBinning,J_Mod=Tkin2Rigi_FluxConversione(OutputBinning,J_Mod,MassNumber=A,Z=Z)
            ROutputBinning,J_LIS=Tkin2Rigi_FluxConversione(OutputBinning,J_LIS,MassNumber=A,Z=Z)
            OutputBinning=ROutputBinning
        if DEBUG: 
            print("DEBUGLINE:: ExecuteModulation --> J_LIS(1GV)",J_LIS[find_nearest_idx(OutputBinning,1.)])

        return (OutputBinning,J_Mod,J_LIS)


    # =================
    def CRSpectra(self, ExpNameKey,OutputX='Tkin',SumIsotope=True):
        """interface to Spectra Function, form the File pathname and evaluate the kind of output
            input:
                - ExpNameKey : Simulation Name Key
                - OutputX    : 'Tkin' Output in Kinetic Energy per nucleon [GeV/n]
                               'Rigi' Output in Rigidity [GV]
                - SumIsotope : Sum over all isotopes with same Z
            Return
                - Simulated Energy/Rigidity
                - Modulated Spectra
                - LIS
                - Simulation Uncertanties (if available) Average,Max,Min
           ---------- error status ---------
          -1: Simulation Directory associated with ExpNameKey not found
          -2:
        """ 

        # ------------------------------
        # Extract all useful parameter from ExpNameKey
        # ------------------------------


        # ... Check if the original binning was in TKin or Rigi (this is important if SumIsotope==True)
        TKO=False
        if 'TKO' in ExpNameKey:
            TKO = True
        # ... Get Particle Informations
        PP= particleProperty(ExpNameKey)
        self.T0 = PP['T0']
        Z       = PP['Z']
        Ions    = PP['Isotopes_A']
        IonsN   = PP['Isotopes_Name']
        if not SumIsotope: 
            Ions  = Ions[0:1]
            IonsN = IonsN[0:1]

        # ------------------------------
        # Create the HelModSimPath and Check if folder exist
        # ------------------------------
        HelModSimPath=self.HelMOD_RAW_FILES+"/"+self.ParametersSet+"/"+ExpNameKey+"/"
        if DEBUG: print("DEBUGLINE::CRSpectra Testing Directory  ",HelModSimPath)
        if not CheckDirExist(HelModSimPath):
            print("Directory ",HelModSimPath," not found, \n --> do you set ParametersSet (-p) and ArchivePATH (-a) ?")
            return (-3,-3,-3)

        
        # ------------------------------
        # Compute Modulated Spectra in proper format
        # ------------------------------  


        MI_OutputBinning,MI_J_Mod,MI_J_LIS=self.ExecuteModulation( Z,Ions[0],HelModSimPath,OutputX )
        if MI_OutputBinning[0]<0:
            if DEBUG: print(f"DEBUGLINE::CRSpectra Error Found on Main ion={Ions[0]}")
            return (MI_OutputBinning, MI_J_Mod, MI_J_LIS)
        
        for idxIons in range(1,len(Ions)): # sum over all Isotopes 
            IO_HelModSimPath = HelModSimPath.replace(IonsN[0],IonsN[idxIons])
            IO_OutputBinning,IO_J_Mod,IO_J_LIS=self.ExecuteModulation( Z,Ions[idxIons],IO_HelModSimPath,OutputX )
            if IO_OutputBinning[0]<0: 
                print(f"WARNING:: Error Found on ion={IonsN[idxIons]}")
                continue
            if np.any(np.fabs(MI_OutputBinning-IO_OutputBinning)/MI_OutputBinning>0.01):
                if DEBUG: 
                    print("WARNING:: X Binning not coherent for %s"%(IonsN[idxIons]))
                    print("WARNING:: Best_X=%s"%MI_OutputBinning)
                    print("WARNING:: IO_Best_X =%s"%IO_OutputBinning)
                    print("\n")
                IO_J_Mod = LinLogInterpolation(IO_OutputBinning,IO_J_Mod,MI_OutputBinning)
                IO_J_LIS = LinLogInterpolation(IO_OutputBinning,IO_J_LIS,MI_OutputBinning)
            # -- Somma
            MI_J_Mod        = MI_J_Mod + IO_J_Mod    
            MI_J_LIS        = MI_J_LIS + IO_J_LIS
        return (MI_OutputBinning, MI_J_Mod, MI_J_LIS)

    #============
    def PrintLIS(self, ExpNameKey,OutputX='Tkin',SumIsotope=True):
        # ... Get Particle Informations
        PP= particleProperty(ExpNameKey)
        self.T0 = PP['T0']
        Z       = PP['Z']
        A       = PP['Isotopes_A'][0]
        if   OutputX=='Tkin'  and SumIsotope==False: Mode=0
        elif OutputX=='Rigi' and SumIsotope==False: Mode=1
        elif OutputX=='Tkin'  and SumIsotope==True:  Mode=2
        elif OutputX=='Rigi' and SumIsotope==True:  Mode=3
        if DEBUG: 
            print("DEBUGLINE:: GetLIS will be called for Z=%d A=%d and Mode=%s"%(Z,A,Mode) )
        LIS_Tkin,LIS_Flux = self.GetLIS(Z, A, Mode=Mode)
        return (LIS_Tkin,LIS_Flux)


# --------------------- Stand-Alone module functions ----------------------

def GetExpFileNameAndLabel(ArchivePATH,ExpNameKey,TKO):
    import re
    # find the file name and Label used for ExpNameKey
    ExperDataFile = ""
    DataLabel = ''
    for line in open(ArchivePATH+"/ExpList_Plot.list").readlines():
        if not(line.startswith("#")):
            Name,FileName,Visualized,Other=line.split('|',3);
            Name=re.sub('[\s+]', '', Name)
            if Name == ExpNameKey:
                    ExperDataFile = re.sub('[\s+]', '', FileName)
                    DataLabel     = Visualized.strip(' \t\n\r')
                    break
    if ExperDataFile=="":
        print("ERROR::#1113#::ExpNameKey=%s not valid  in %s"%(ExpNameKey,ArchivePATH+"/ExpList_Plot.list"))
        exit(1)
    if TKO:
        ExperDataFile=ArchivePATH+"/DataTXT/"+ExperDataFile
    else:
        ExperDataFile=ArchivePATH+"/DataTXT/"+'Rigidity_'+ExperDataFile
    if not os.path.exists(ExperDataFile):
                print("ERROR::#1114#:: File Not Found %s"%(ExperDataFile))
                exit(1)
    return (ExperDataFile,DataLabel)



def HelpManual():
    print(__doc__)
    print(__version__)
    print(__copyright__)
    print("For info please address to",__email__)
    print("""
Thanks for using HelMod Modulation Module for GALPROP !

Requirements : np.>=1.10, scipy>=0.17.0, python >2.7 / >3.0

The minimal usage of the module via command inline is
> python SolarModulation_Galprop.py --ArchivePATH <PATH>  [-p <PAR_SET_NAME>] [--SumAllIsotpes] --LIS <GALPROPFits.gz> --SimName <ExpNameKey>

-a (--ArchivePATH) <PATH> Location of archive
-p (--ParametersSet) <PAR_SET_NAME> Define the name of not default parameter Sets available in HelMod Archive
--SumAllIsotpes     The result is the sum of modulation over all available Isotopes
--LIS <GALPROPFits.gz/txt> LIS file in GALPROP fits format
--SimName <ExpNameKey>  simulation Key (see -l option for the list of available simulations)

other available options:
-h                  Help (this message)
--DEBUG             Active debugging message (for developer only, it is very verbose)
-l (--ListKey)      List simulation (ExpNameKey) available in HelMod Archive
-t (--txtFile)      Indicates that LIS is a TXT File
--PrintLIS          Print Complete LIS used for Modulation (note that if --joinIsotope is Activeted output LIS is the sum in Rigidity of all isotopes
--ExtraSource_GeV <FILE_NAME> specify an extrasource to be added to LIS. File must be two column and expressend in GeV/nuc (now availabel only for electron an positron LIS)
--SimUnit           Output Unit of the module (Tkin: Kinetic Energy per Nucleon [GeV/n] Rigi: Rigidity [GV])
-o (--output) <FILE_NAME> use custom name for outputfile
--MakePlot          Create a Plot in png format
----------------------------------------------------------------

""")

    exit()
# --------------------- Stand-Alone interface -----------------------------
# This is an example on how to use the module and create modualted spectra.
if (__name__ == "__main__"):
    import re
    ArchivePATH=''                          # path of HelMod Archive
    LISFile=''                              # LIS File
    PrintLIS=False                          # Extract LIS
    GALPROPFile=True                        # if True use galprop file format, if False use txt
    ExpNameKey=''                           # Simulation Name, it must begin with Ions Name
    ParametersSet=''                        # Choise of parameter Set
    OutputFileName="HelModOutput"           # Output File Name
    FileExtraSource_GeV=''                  # use extrasource to be added to LIS (for Electron an positron Only)
    SimUnit       = 'auto'                  # Simulation unit of the output
    UnitVal       =['Tkin','Rigi','auto']   # possible values of SimUnit
    SumAllIsotpes = False                   # Output is summed over all available isotopes
    DoModulation  = False                   # If True al parameter are proper setted to perform Modulation Procedure
    MakePlot      = False                   # create a Plot
    # ----------------------------------------------------------------
    #------------------------ Read Program arguments -----------------
    import sys, getopt
    arguments=sys.argv[1:]
    try:
        opts, args = getopt.getopt(arguments,"hla:to:p:",["DEBUG",   #hiltp:o:a:E:
                             "ArchivePATH=",
                             "ParametersSet=",
                             "SumAllIsotpes",
                             "ListKey",
                             "LIS=",
                             "SimName=",
                             "txtFile",
                             "ExtraSource_GeV=",
                             "PrintLIS",
                             "SimUnit=",
                             "output=",
                             "MakePlot",
                             ])
        if DEBUG:
            print("DEBUGLINE::-> opts=",opts," args=",args)
    except getopt.GetoptError:
        HelpManual()
        sys.exit(2)
    # ----------------------------------------------------------------
    #--------------- Check arguments ---------------------------------
    for opt, arg in opts:
        if opt == '-h': # Read Manual
            HelpManual()
            sys.exit()
        elif opt in ("--DEBUG"): # Show Debug lines
            DEBUG=True
        elif opt in ("-a","--ArchivePATH"): # set local path where is the HelMod Archive 
            ArchivePATH=arg
            if DEBUG: print("Archive PATH is ",ArchivePATH)
        elif opt in ("-p","--ParametersSet"):   # Set Modulation Parameters
            ParametersSet=arg
            if DEBUG: print("Parameter Set Name ",ParametersSet)
        elif opt in ("--LIS"):  
            LISFile=arg
            if DEBUG: print("LISFile is ",LISFile)
        elif opt in ("--SimName"):  
            ExpNameKey=arg
            if DEBUG: print("ExpNameKey is ",ExpNameKey)
        elif opt in ("--SumAllIsotpes"):      # The result is the sum of modulation over all available Isotopes
            SumAllIsotpes=True
            if DEBUG: print("The result is the sum of modulation over all available Isotopes ")
        elif opt in ("--ListKey",'-l'):
            if DEBUG: print("List simulation (ExpNameKey) available in HelMod Archive ")
            try:
                for line in open(ArchivePATH+"/ExpList_Plot.list").readlines():
                    if not(line.startswith("#")):
                        Name,Other=line.split('|',1);
                        Name=re.sub('[\s+]', '', Name)
                        print("Experiment NameKey: %s"%(Name))                        
            except IOError:
                print('Missing Index File',ArchivePATH+"/ExpList_Plot.list")
            exit(0)
        elif opt in ('-t',"--txtFile"):     # Ask for a TXT LIS File
            GALPROPFile=False
            if DEBUG: print("LIS File is in TXT Format ")
        elif opt in ("--ExtraSource_GeV"):     # Ask for a TXT LIS File
            FileExtraSource_GeV=arg
            if DEBUG: print("LIS will be corrected using this extra Source ")
        elif opt in ("--PrintLIS"):     # Ask for a TXT LIS File
            PrintLIS=True
            if DEBUG: print("LIS will be saved in the outputfile ")
        elif opt in ("--SimUnit",):    
            SimUnit=arg
            if SimUnit not in UnitVal:
                print("ERROR::--SimUnit accept only value in ",UnitVal)
                exit(2)
        elif opt in ("-o","--output"):      # specify the output file name
            OutputFileName=arg
            if DEBUG: print("the outputFile will contain --> ",OutputFileName)
        elif opt in ("--MakePlot"):     # Create a Plot wth data comparison
            MakePlot=True
            if DEBUG: print("the outputFile will contain --> ",OutputFileName)
    # ----------------------------------------------------------------
    # ------------------- Modulation part  ---------------------------

    if LISFile=='': 
        print("ERROR: Please specify a LIS file after option --LIS ")
        print("I cannot proceed, bye!")
        exit(1)
    if not os.path.isfile(LISFile):
        print("ERROR: LIS File does not exist ",LISFile)
        print("I cannot proceed, bye!")
        exit(1)
    # ----------------------------------------------------------------
    # Step 1 - initialize the Modulation Class, this load the LISs in memory and initialize the archive variables
    # ----------------------------------------------------------------
    gdsp = SolarModulation(LISFile,GALPROPInput=GALPROPFile)  

    # ----------------------------------------------------------------
    # Step 2 - make correction to LIS
    # ----------------------------------------------------------------    
    # --- Extra Source not in the LIS File
    if FileExtraSource_GeV!='':
        if DEBUG: print("Adding ExtraSource to LIS...")
        gdsp.addExtraSource(FileExtraSource_GeV,units='GeV')


    # ----------------------------------------------------------------
    # Step 3 - Check ExpNameKey and Print LIS file
    # ----------------------------------------------------------------  
    if ExpNameKey=='': 
        print("ERROR: Please specify a SimulationKey file after option --SimName ")
        print("I cannot proceed, bye!")
        exit(1)
    if SimUnit=='auto':
        if 'TKO' in ExpNameKey: 
            OutputX='Tkin'
        else:
            OutputX='Rigi'
    else:
        OutputX=SimUnit
    if PrintLIS:
        xLIS,yLIS = gdsp.PrintLIS(ExpNameKey,OutputX=OutputX,SumIsotope=SumAllIsotpes)
        if OutputX=='Tkin': 
            header="Kinetic Energy/nuc [GeV/nuc], LIS [(m^2 s sr GeV/n)^{-1}]"
        else:
            header="Rigidity [GV], [(m^2 s sr GV)^{-1}]"
        np.savetxt("LIS_"+OutputFileName+"_"+ExpNameKey+"_"+OutputX+".dat",np.column_stack((xLIS,yLIS)),
                    header=header,
                    footer="Created with HelMod Module %s"%(__version__))

    # ----------------------------------------------------------------
    # Step 4 - Set Sim Parameters
    # ----------------------------------------------------------------    
    if ArchivePATH!='' : 
        # the path to HelMod Archive is mandatory to compute the modulation
        if gdsp.SET_ArchivePath(ArchivePATH): #<---------------------------- step 4 Key point (mandatory), Set the ArchivePath variable
            if ParametersSet=='': 
                # in case variable ParametersSet was not setted we can evaluate the _default_ set there is three ways to be checked in this order:
                # a) looking for file ParameterSimulated.list and look for the value starting with '+' character
                # b) looking for file ParameterSimulated.list and took the first in the list (usually the fist is always the _default_)
                # c) list the folders in archive directory and took the first in alphabetic order 
                ParameterFile=ArchivePATH+"/ParameterSimulated.list"
                if os.path.isfile(ParameterFile):
                    try:
                        found=False
                        BestParSet=''
                        ListOfParDir = []
                        for line in open(ParameterFile).readlines():
                            if not(line.startswith("#")):
                                if DEBUG: 
                                    print("parameter found:",line.strip())
                                if (line.startswith("+")):                  # case a)
                                    UserParSet=line.strip().strip("+")
                                    found=True
                                    if DEBUG:
                                        print("BEST parameter found:",UserParSet)
                                    ParametersSet=UserParSet
                                    ListOfParDir.append(line.strip().strip("+"))
                                else:
                                    ListOfParDir.append(line.strip())
                        if len(ListOfParDir)==0:
                            print("ERROR:: it seems ",ParameterFile," is empty... proper fill the file or delete it")
                            print("I cannot proceed, bye!")
                            exit(1)
                        if not found :                                      # case b)
                            ListOfParDir.sort()
                            ParametersSet=ListOfParDir[0]
                    except IOError:
                        print('ERROR:: ops, this should not happens, something goes wrong with ',ParameterFile)
                        print("I cannot proceed, bye!")
                        exit(1)
                else:                                                       #case c)
                    ListOfParDir= glob.glob(ArchivePATH+"/RawPar*") # simulation folder always startwith RawPar
                    ListOfParDir.sort()
                    ParametersSet=ListOfParDir[0]
                pass
            if gdsp.SET_ParametersSet(ParametersSet): #<---------------------------- step 4 Key point (mandatory), Set the ParametersSet variable
                DoModulation=True
            else:
                print('ERROR:: it seems the set of simulations you required does not exist please check it--> ',ParametersSet)
                print("I cannot proceed, bye!")
                exit(1)                
        else:
            print('ERROR:: it seems Archive path does not exist please check it--> ',ArchivePATH)
            print("I cannot proceed, bye!")
            exit(1)
    else:
        DoModulation=False
        if DEBUG: print("WARNING:: Path to Archive is missing, modulated Spectra cannot be evaluated")

    # ----------------------------------------------------------------
    # Step 5 - Evaluate Modulated Spectra
    # ----------------------------------------------------------------  
    if DoModulation: 
        J_mods=gdsp.CRSpectra(ExpNameKey,OutputX=OutputX,SumIsotope=SumAllIsotpes)
        """ J_mods contains all fluxes in the form:
            0 - OutputBinning Energy/Rigidity 
            1 - J_Mod         modulated spectra
            5 - J_LIS         LIS Flux
            J_Mod is the modulated spectra, but in case of forecast J_Mod_aver should be used instead
            note that if simulation is not a forecast, all J_Mod arrays coincide
        """
        if J_mods[0][0]<0:
            print("ERROR: There Was an error evaluating Simulation Function returns ",J_mods[0][0])
            exit(1)
        
        # --- save txt
        if OutputX=='Tkin': 
            File_header="Kinetic Energy/nuc [GeV/nuc]\t Modulated Spectrum [(m^2 s sr GeV/n)^{-1}]\t LIS [(m^2 s sr GeV/n)^{-1}]"
        else:
            File_header="Rigidity [GV]\t Modulated Spectrum [(m^2 s sr GV)^{-1}]\t LIS [(m^2 s sr GV)^{-1}]"
        
        saveCS= np.column_stack((J_mods[0],J_mods[1],J_mods[2]))
        Prel = 'ModSpectra_'
        
        np.savetxt(Prel+OutputFileName+"_"+ExpNameKey+"_"+OutputX+".dat",saveCS,
                      header=File_header,
                      footer="HelMod-4 Module %s "%(__version__))   

    # ----------------------------------------------------------------
    # Step 6 - Create Plots
    # ----------------------------------------------------------------  
    if MakePlot:
        import matplotlib.pyplot as pl
        Particle,Exper=ExpNameKey.split('_',1);
        if OutputX=='Tkin': 
            ylabel="Differential Intensity"+r" [(m$^2$ s sr GeV)$^{-1}$]"
            xlabel="Kinetic Energy [GeV/nuc]"
            TKO=True
        else:
            ylabel="Differential Intensity"+r" [(m$^2$ s sr GV)$^{-1}$]"
            xlabel="Rigidity [GV]"
            TKO=False


        if PrintLIS:
            # -- make LIS Plot
            pl.clf()
            fig = pl.figure(figsize=(7, 6))
            pl.plot(xLIS,yLIS,'--k', linewidth=2,label="%s LIS"%(Particle))
            pl.legend(numpoints=1)
            pl.yscale('log')
            pl.xscale('log')
            pl.ylabel(ylabel)
            pl.xlabel(xlabel)
            # pl.tight_layout()
            pl.savefig("Fig_LIS_%s_%s_%s.png" %(OutputFileName,ExpNameKey,OutputX))
            if DEBUG:
                  pl.show()
            pl.close()

        if DoModulation:
            # -- make modulated Plot
            pl.clf()
            fig = pl.figure(figsize=(7, 6))
            ax0 = pl.subplot2grid((2, 1), (0, 0), rowspan=2)
            ax0.plot(J_mods[0],J_mods[2],'--k', linewidth=2,label="%s LIS"%(Particle))
            ax0.plot(J_mods[0],J_mods[1],'-r', linewidth=2,label="%s" %(Exper))
            pl.legend(numpoints=1)
            pl.yscale('log')
            pl.xscale('log')
            pl.ylabel(ylabel)
            pl.xlabel(xlabel)
            # pl.tight_layout()
            pl.savefig("Fig_Mod_%s_%s_%s.png" %(OutputFileName,ExpNameKey,OutputX))
            if DEBUG:
                  pl.show()
            pl.close()

            # -- make modulated Plot with Data
            if not "_CR" in ExpNameKey: # historical paramaters Simulation
                try:
                    
                    SimulazEnergy = J_mods[0]
                    SimulazFlux   = J_mods[1]
                    LIS           = J_mods[2]
                    # ...... Get Experimental Data .........
                    # ExpEnergy = []
                    # ExpFlux   = []
                    # ExpErr    = []
                    # ExpTXTPATH =ArchivePATH+"/DataTXT/"
                    ExperDataFile,DataLabel=GetExpFileNameAndLabel(ArchivePATH,ExpNameKey,TKO)
                    ExpEnergy,ExpFlux,ExpErrInf,ExpErrSup=np.loadtxt(ExperDataFile,unpack=True)
                    ExpErr=[ExpErrInf,ExpErrSup]
                    if DEBUG:
                        print("DEBUGLINE::ExpFlux,",ExpFlux)
                        print("DEBUGLine::SimulazFlux",SimulazFlux)
                        print("DEBUGLINE::ExperDataFile=",ExperDataFile)
                        print("DEBUGLINE::DataLabel=",DataLabel)
                    if len(ExpFlux)!=len(SimulazFlux):
                        print( "ERROR::#1115#::there is something wrong with length of dataFile and Simulation...")
                        print( len(ExpFlux),"!=",len(SimulazFlux))
                    # ...... END Get Experimental Data .........

                    # ... evaluate distance between data and simulations ...
                    DistanceFlux    = (np.array(SimulazFlux, dtype=np.float)-ExpFlux)/ExpFlux
                    expZero         = np.zeros(len(ExpEnergy))
                    expZeroErr      = [ExpErrInf/ExpFlux,ExpErrSup/ExpFlux]
                    DistanceLIS     = (np.array(LIS, dtype=np.float)-ExpFlux)/ExpFlux


                    pl.clf()
                    fig = pl.figure(figsize=(7, 8))
                    ax0 = pl.subplot2grid((3, 1), (0, 0), rowspan=2)
                    # pl.xlim(pl_xrange)
                    ax0.plot(SimulazEnergy, LIS,'--k', linewidth=2,label="%s LIS"%(Particle))
                    ax0.plot(SimulazEnergy, SimulazFlux,'-r', linewidth=2,label="Modulated Spectrum")
                    ax0.errorbar(ExpEnergy, ExpFlux, yerr=ExpErr, fmt=".k",label="%s" %(DataLabel))
                    pl.legend(numpoints=1)
                    pl.yscale('log')
                    pl.xscale('log')
                    pl.ylabel(ylabel)
                    ax1 = pl.subplot2grid((3, 1), (2, 0))
                    # pl.xlim(pl_xrange)
                    pl.ylim([-0.4, +0.4])
                    ax1.errorbar(SimulazEnergy,expZero, yerr=expZeroErr, fmt=".k",label="%s" %(DataLabel))
                    ax1.plot(SimulazEnergy, DistanceFlux, "-r",label="Modulated Spectrum")
                    ax1.plot(SimulazEnergy, DistanceLIS, "--k",label="LIS")
                    pl.xlabel(xlabel)
                    pl.ylabel("Relative difference")
                    pl.xscale('log')
                    pl.tight_layout()
                    pl.savefig("Fig_ModData_%s_%s_%s.png" %(OutputFileName,ExpNameKey,OutputX))
                    if DEBUG:
                          pl.show()
                    pl.close()
                except:
                    if DEBUG: print("Some error making Plot with data")