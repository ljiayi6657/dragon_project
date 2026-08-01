#!/usr/local/bin/python
from __future__ import print_function
import os, sys, time, math, glob
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as color
from matplotlib.ticker import NullFormatter
import pylab
import socket

from datareader import *



BEAparamnames=["C1","C2","CP","CS","G1","G2","GP","GS","ES","PE","PP"]
BEAparams=[0.26,0.0035,0.0072,0.00016,3.83,2.83,3.70,2.51,1000.0,1.3,0.93]
BEAparamsNoSM=[0.26,0.0035,0.0072,0.00016,3.83,2.83,3.70,2.51,1000.0,0.0,0.0]


#BEAparamnames=["C1", "C2",  "CP",  "CS",  "G1", "G2","GP","GS","ES","PE","PP"]
#BEAparams=    [0.26,0.0035,0.0072,0.00016,3.83,2.83,3.70,2.51,1000.0,1.3,0.93]
#          0    1       2      3     4      5    6    7    8    9   10

def BEAeleflx(e,par=BEAparams):
    solmodfact=pow(e,2)/pow((e+par[9]),2)
    oneflux=par[0]*pow((e+par[9]),-par[4])
    twoflux=par[1]*pow((e+par[9]),-par[5])    
    return solmodfact*(oneflux+twoflux)

    
def BEAposflx(e,par=BEAparams):
    solmodfact=pow(e,2)/pow((e+par[10]),2)
    secposflux=par[2]*pow((e+par[10]),-par[6])
    sourceflux=par[3]*pow((e+par[10]),-par[7])
    return solmodfact*(secposflux+sourceflux)

def BEAbkgposflx(e,par=BEAparams):
    solmodfact=pow(e,2)/pow((e+par[10]),2)
    secposflux=par[2]*pow((e+par[10]),-par[6])
    return solmodfact*secposflux

def BEAposfrac(e,par=BEAparams):
    bpf=BEAposflx(e,par)
    bef=BEAeleflx(e,par)
    return bpf/(bpf+bef)

def BEAtotflx(e,par=BEAparams):
    bpf=BEAposflx(e,par)
    bef=BEAeleflx(e,par)
    return bpf+bef

def BEAbkgtotflx(e,par=BEAparams):
    solmodfactele=pow(e,2)/pow((e+par[9]),2)
    solmodfactpro=pow(e,2)/pow((e+par[10]),2)
    oneflux=par[0]*pow((e+par[9]),-par[4])
    twoflux=par[1]*pow((e+par[9]),-par[5])    
    secposflux=par[2]*pow((e+par[10]),-par[6])
    sourceflux=par[3]*pow((e+par[10]),-par[7])
    return solmodfactele*(oneflux+twoflux-sourceflux)+solmodfactpro*(secposflux)

def BEAbkgeleflx(e,par=BEAparams):
    solmodfactele=pow(e,2)/pow((e+par[9]),2)
    oneflux=par[0]*pow((e+par[9]),-par[4])
    twoflux=par[1]*pow((e+par[9]),-par[5])    
    sourceflux=par[3]*pow((e+par[10]),-par[7])
    return solmodfactele*(oneflux+twoflux-sourceflux)

def BEAbkgposfrac(e,par=BEAparams):
    bpf=BEAbkgposflx(e,par)
    tof=BEAbkgtotflx(e,par)
    return bpf/tof

def bkgfunc(e,par):
    aa = par[0] * math.pow(e, par[2])
    fsum = (aa + 1) * math.exp(-e/par[8])
    return par[5]*math.pow(e, par[6]) * fsum 

def bkgeleflx(e,par):
    return par[5]*math.pow(e, par[6])*math.exp(-e/par[8])

def gssfuncold(e,par):
    aa = par[0] * math.pow(e, par[2]) * math.exp(-e/par[8])
    bb = par[1] * math.pow(e, par[3]) * math.exp(-e/par[4])
    fsum = aa + math.exp(-e/par[8]) + 2*bb
    return par[5]*math.pow(e, par[6]) * fsum 

def gssfunc(e,par,cp=1,powercut=False,supercut=False):
    ele=gssSMeleflx(e,par,[0.0,0.0],cp,powercut,supercut)    
    pos=gssSMposflx(e,par,[0.0,0.0],cp,powercut,supercut)
    return ele+pos


def gssSMposflx(e,par,sm,cp=1,powercut=False,supercut=False):
    e=e+sm[0]
    aa = par[0] * math.pow(e, par[2]) 
    if par[4]>0 and supercut:
        bb = par[1] * math.pow(e, par[3]) * math.pow((1.0+(e/par[4])),-math.pow(e/par[4],cp))
    elif par[4]>0 and powercut:
        bb = par[1] * math.pow(e, par[3]) * math.pow((1.0+(e/par[4])),-cp)
    elif par[4]>0:
        bb = par[1] * math.pow(e, par[3]) * math.exp(-e/par[4])**cp
    else:
        bb = 0.0 
    fsum = aa * math.exp(-e/par[8]) + bb
    flux = par[5]*math.pow(e, par[6]) * fsum 
    solmodfact=pow((e-sm[0]),2)/pow(e,2)
    return flux*solmodfact

def gssposflxold(e,par):
    aa = par[0] * math.pow(e, par[2]) 
    bb = par[1] * math.pow(e, par[3]) * math.exp(-e/par[4])
    fsum = aa * math.exp(-e/par[8]) + bb
    return par[5]*math.pow(e, par[6]) * fsum 

def gssposflx(e,par,cp=1,powercut=False,supercut=False):
    return gssSMposflx(e,par,[0.0,0.0],cp,powercut,supercut)    

def secposflx(e,par):
    aa = par[0] * math.pow(e, par[2]) 
    fsum = aa * math.exp(-e/par[8])
    return par[5]*math.pow(e, par[6]) * fsum 

def srcposflx(e,par,cp=1,powercut=False,supercut=False):
    if supercut:
        bb = par[1] * math.pow(e, par[3]) * math.pow((1.0+(e/par[4])),-math.pow(e/par[4],cp))
    elif powercut:
        bb = par[1] * math.pow(e, par[3]) * math.pow((1.0+(e/par[4])),-cp)
    else:
        bb = par[1] * math.pow(e, par[3]) * math.exp(-e/par[4])**cp
    return par[5]*math.pow(e, par[6]) * bb

def gssSMeleflx(e,par,sm,cp=1,powercut=False,supercut=False):
    e=e+sm[1]
    if par[4]>0 and supercut:
        bb = par[1] * math.pow(e, par[3]) * math.pow((1.0+(e/par[4])),-math.pow(e/par[4],cp))
    elif par[4]>0 and powercut:
        bb = par[1] * math.pow(e, par[3]) * math.pow((1.0+(e/par[4])),-cp)
    elif par[4]>0:
        bb = par[1] * math.pow(e, par[3]) * math.exp(-e/par[4])**cp
    else:
        bb = 0.0 
    if par[11]>0:
        cc = par[11] * math.pow(e, par[12])
    else:
        cc = 0.0 
    fsum = math.exp(-e/par[8]) + bb + cc
    flux = par[5]*math.pow(e, par[6]) * fsum 
    solmodfact=pow((e-sm[1]),2)/pow(e,2)
    return flux*solmodfact


def varslidepowscalecut(e,coeff,indx,indfact,indpow,cut,csc):
    if e>10.0:
        return coeff*pow(e,indx+indfact*pow(e/1000.0,(1.0/indpow)))*math.exp(-(pow(e,csc)/pow(cut,csc)))
    else:
        return 0.0

def gssSNXeleflx(e,par,sm,sn,cp=1,powercut=False,supercut=False):
    e=e+sm[1]
    if par[4]>0 and supercut:
        bb = par[1] * math.pow(e, par[3]) * math.pow((1.0+(e/par[4])),-math.pow(e/par[4],cp))
    elif par[4]>0 and powercut:
        bb = par[1] * math.pow(e, par[3]) * math.pow((1.0+(e/par[4])),-cp)
    elif par[4]>0:
        bb = par[1] * math.pow(e, par[3]) * math.exp(-e/par[4])
    else:
        bb = 0.0 
    if sn[0]>0:
        cc = varslidepowscalecut(e,sn[0],sn[1],sn[2],sn[3],sn[4],sn[5])
    else:
        cc = 0.0 
    fsum = math.exp(-e/par[8]) + bb
    flux = cc+par[5]*math.pow(e, par[6]) * fsum 
    solmodfact=pow((e-sm[1]),2)/pow(e,2)
    return flux*solmodfact


def gsseleflxold(e,par): 
    bb = par[1] * math.pow(e, par[3]) * math.exp(-e/par[4])
    fsum = math.exp(-e/par[8]) + bb
    return par[5]*math.pow(e, par[6]) * fsum

def gsseleflx(e,par,cp=1,powercut=False,supercut=False):
    return gssSMeleflx(e,par,[0.0,0.0],cp,powercut,supercut)    

def flxfrac(e,flx,par):
    aa = par[0] * math.pow(e, par[2])
    bb = flx/math.pow(e, par[6])
    posfrct=(aa * math.exp(-e/par[8]) + bb) / (aa * math.exp(-e/par[8]) + math.exp(-e/par[8]) + 2*bb)
    return posfrct

def gssfracold(e,par):
    aa = par[0] * math.pow(e, par[2]) 
    bb = par[1] * math.pow(e, par[3]) * math.exp(-e/par[4]);
    return (aa * math.exp(-e/par[8]) + bb) / (aa * math.exp(-e/par[8]) + math.exp(-e/par[8]) + 2*bb)

def gssfrac(e,par,cp=1,powercut=False,supercut=False):
    ele=gssSMeleflx(e,par,[0.0,0.0],cp,powercut,supercut)    
    pos=gssSMposflx(e,par,[0.0,0.0],cp,powercut,supercut)
    return pos/(ele+pos)

def bkgfrac(e,par):
    aa = par[0] * math.pow(e, par[2]) 
    return (aa * math.exp(-e/par[8])) / (aa * math.exp(-e/par[8]) + math.exp(-e/par[8]))
    
    
