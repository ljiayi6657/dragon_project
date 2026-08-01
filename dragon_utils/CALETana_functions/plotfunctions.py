#!/usr/bin/python
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
from fluxfunctions import *

dragonalpha=0.8


#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#Species Plot Routines
#==================================================================================================================================
#Individual Experiment Plot Routines        
#VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV


def plotcaltotflux(fig,basepath,index=3.0,vals=False, bw=False,systerr=True):
   if not vals:
    vals=readcaltotflxvals(basepath,systerr)
   e=[]
   flux=[]
   loerr=[]
   uperr=[]
   for point in sorted(vals.keys()):
    e.append(point)
    flux.append(vals[point][0]*math.pow(point, index))
    loerr.append(vals[point][1][0]*math.pow(point, index))
    uperr.append(vals[point][1][1]*math.pow(point, index))
   if systerr:
        co="grey"
        ma="o"
   else:
        co="k"    
        ma="+"
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], fmt='kp')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker = ma ,linestyle = " ", color = co ,markeredgecolor = co)    
   return p


def plotcalICRCflux(fig,basepath,index=3.0,vals=False, bw=False,systerr=True):
   if not vals:
    vals=readcalICRCflxvals(basepath,systerr)
   e=[]
   flux=[]
   loerr=[]
   uperr=[]
   for point in sorted(vals.keys()):
    e.append(point)
    flux.append(vals[point][0]*math.pow(point, index))
    loerr.append(vals[point][1][0]*math.pow(point, index))
    uperr.append(vals[point][1][1]*math.pow(point, index))
   if systerr:
        co="grey"
        ma="o"
   else:
        co="k"    
        ma="+"
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], fmt='kp')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker = ma ,linestyle = " ", color = co ,markeredgecolor = co)    
   return p


def plotcalPRLflux(fig,basepath,index=3.0,vals=False, bw=False,systerr=True):
   if not vals:
    vals=readcalPRLflxvals(basepath,systerr,asymerr=True)
   e=[]
   flux=[]
   loerr=[]
   uperr=[]
   for point in sorted(vals.keys()):
    e.append(point)
    flux.append(vals[point][0]*math.pow(point, index))
    loerr.append(vals[point][1][0]*math.pow(point, index))
    uperr.append(vals[point][1][1]*math.pow(point, index))
   if systerr:
        co="grey"
        ma="o"
   else:
        co="k"    
        ma="+"
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], fmt='kp')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker = ma ,linestyle = " ", color = co ,markeredgecolor = co)    
   return p


def plotcalPRL2flux(fig,basepath,index=3.0,vals=False, bw=False,systerr=True,fitnui=[False],DAMPEbin=False,nonormerr=False,color=False,doublep=False):
   if not vals:
    vals=readcalPRL2flxvals(basepath,systerr,asymerr=True,nuisancefit=fitnui[0],DAMPEbin=DAMPEbin,nonormerr=nonormerr)
   e=[]
   flux=[]
   loerr=[]
   uperr=[]
   for point in sorted(vals.keys()):
    e.append(point)
    flux.append(vals[point][0]*math.pow(point, index))
    loerr.append(vals[point][1][0]*math.pow(point, index))
    uperr.append(vals[point][1][1]*math.pow(point, index))
   if color:
    co=color
    ma="o"
   elif systerr:
        co="goldenrod"
        ma="o"
   else:
        co="red"    
        ma="_"
   if not (fitnui[0] and not doublep):
       if bw:
        p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], fmt='kp')    
       else:
           p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker = ma ,linestyle = " ", color = co ,markeredgecolor = co)    
   if fitnui[0] and len(fitnui)>1:
    modflx=[]
    for point,of,d in zip(e,flux,fitnui[1]):
        modflx.append(((of/math.pow(point, index))+d)*math.pow(point, index))
    if color and not doublep:
        pco=color
    else:
        pco="goldenrod"
    #p2,q,r=plt.errorbar(e[:len(modflx)], modflx, yerr=[loerr[:len(modflx)],uperr[:len(modflx)]], marker = "p" ,linestyle = " ", color = pco ,markeredgecolor = co)    
    p2=plt.fill_between(e[:len(modflx)],flux[:len(modflx)],modflx,color="k",alpha=0.3)
    if doublep:    
           return p,p2
    else:
        return p2
   else:
    return p
    


def plotcalYA2020flux(fig,basepath,index=3.0,vals=False, bw=False,systerr=True,fitnui=[False],DAMPEbin=False,nonormerr=False,BDT=9,color=False,doublep=False):
   if not vals:
    vals=readcalYA2020flxvals(basepath,systerr,asymerr=True,nuisancefit=fitnui[0],DAMPEbin=DAMPEbin,nonormerr=nonormerr,BDT=BDT)
   e=[]
   flux=[]
   loerr=[]
   uperr=[]
   for point in sorted(vals.keys()):
    e.append(point)
    flux.append(vals[point][0]*math.pow(point, index))
    loerr.append(vals[point][1][0]*math.pow(point, index))
    uperr.append(vals[point][1][1]*math.pow(point, index))
   if color:
    co=color
    ma="o"
   elif systerr:
        co="r"
        ma="o"
   else:
        co="red"    
        ma="_"
   if not (fitnui[0] and not doublep):    
       if bw:
        p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], fmt='kp')    
       else:
           p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker = ma ,linestyle = " ", color = co ,markeredgecolor = co)    
   if fitnui[0] and len(fitnui)>1:
    modflx=[]
    for point,of,d in zip(e,flux,fitnui[1]):
        modflx.append(((of/math.pow(point, index))+d)*math.pow(point, index))
    if color and not doublep:
        pco=color
    else:
        pco="r"
    #p2,q,r=plt.errorbar(e[:len(modflx)], modflx, yerr=[loerr[:len(modflx)],uperr[:len(modflx)]], marker = "p" ,linestyle = " ", color = pco ,markeredgecolor = co)    
    p2=plt.fill_between(e[:len(modflx)],flux[:len(modflx)],modflx,color="k",alpha=0.3)
    if doublep:    
           return p,p2
    else:
        return p2
   elif fitnui[0]:
    p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker = ma ,linestyle = " ", color = co ,markeredgecolor = co)
    return p         
   else:
    return p

def plotcalYA2022flux(fig,basepath,index=3.0,vals=False, bw=False,systerr=True,fitnui=[False],DAMPEbin=False,AMSbin=False,nonormerr=False,BDT=13,color=False,doublep=False):
   if not vals:
    vals=readcalYA2022flxvals(basepath,systerr,asymerr=True,nuisancefit=fitnui[0],DAMPEbin=DAMPEbin,AMSbin=AMSbin,nonormerr=nonormerr,BDT=BDT)
   e=[]
   flux=[]
   loerr=[]
   uperr=[]
   for point in sorted(vals.keys()):
    e.append(point)
    flux.append(vals[point][0]*math.pow(point, index))
    loerr.append(vals[point][1][0]*math.pow(point, index))
    uperr.append(vals[point][1][1]*math.pow(point, index))
   if color:
    co=color
    ma="o"
   elif systerr:
        co="r"
        ma="o"
   else:
        co="red"    
        ma="_"
   if not (fitnui[0] and not doublep):    
       if bw:
        p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], fmt='kp')    
       else:
           p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker = ma ,linestyle = " ", color = co ,markeredgecolor = co)    
   if fitnui[0] and len(fitnui)>1:
    modflx=[]
    for point,of,d in zip(e,flux,fitnui[1]):
        modflx.append(((of/math.pow(point, index))+d)*math.pow(point, index))
    if color and not doublep:
        pco=color
    else:
        pco="red"
    #p2,q,r=plt.errorbar(e[:len(modflx)], modflx, yerr=[loerr[:len(modflx)],uperr[:len(modflx)]], marker = "p" ,linestyle = " ", color = pco ,markeredgecolor = co)    
    p2=plt.fill_between(e[:len(modflx)],flux[:len(modflx)],modflx,color="k",alpha=0.3)
    if doublep:    
           return p,p2
    else:
        return p2
   elif fitnui[0]:
    p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker = ma ,linestyle = " ", color = co ,markeredgecolor = co)
    return p         
   else:
    return p
    
def plotcalYA2022bflux(fig,basepath,index=3.0,vals=False, bw=False,systerr=True,fitnui=[False],DAMPEbin=False,AMSbin=False,nonormerr=False,BDT=13,color=False,doublep=False):
   if not vals:
    vals=readcalYA2022bflxvals(basepath,systerr,asymerr=True,nuisancefit=fitnui[0],DAMPEbin=DAMPEbin,AMSbin=AMSbin,nonormerr=nonormerr,BDT=BDT)
   e=[]
   flux=[]
   loerr=[]
   uperr=[]
   for point in sorted(vals.keys()):
    e.append(point)
    flux.append(vals[point][0]*math.pow(point, index))
    loerr.append(vals[point][1][0]*math.pow(point, index))
    uperr.append(vals[point][1][1]*math.pow(point, index))
   if color:
    co=color
    ma="o"
   elif systerr:
        co="r"
        ma="o"
   else:
        co="red"    
        ma="_"
   if not (fitnui[0] and not doublep):    
       if bw:
        p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], fmt='kp')    
       else:
           p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker = ma ,linestyle = " ", color = co ,markeredgecolor = co)    
   if fitnui[0] and len(fitnui)>1:
    modflx=[]
    for point,of,d in zip(e,flux,fitnui[1]):
        modflx.append(((of/math.pow(point, index))+d)*math.pow(point, index))
    if color and not doublep:
        pco=color
    else:
        pco="red"
    #p2,q,r=plt.errorbar(e[:len(modflx)], modflx, yerr=[loerr[:len(modflx)],uperr[:len(modflx)]], marker = "p" ,linestyle = " ", color = pco ,markeredgecolor = co)    
    p2=plt.fill_between(e[:len(modflx)],flux[:len(modflx)],modflx,color="k",alpha=0.3)
    if doublep:    
           return p,p2
    else:
        return p2
   elif fitnui[0]:
    p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker = ma ,linestyle = " ", color = co ,markeredgecolor = co)
    return p         
   else:
    return p    
    
def plotcalYA2022fflux(fig,basepath,index=3.0,vals=False, bw=False,systerr=True,fitnui=[False],DAMPEbin=False,AMSbin=False,nonormerr=False,BDT=13,color=False,doublep=False):
   if not vals:
    vals=readcalYA2022bflxvals(basepath,systerr,asymerr=True,nuisancefit=fitnui[0],DAMPEbin=DAMPEbin,AMSbin=AMSbin,nonormerr=nonormerr,BDT=BDT,sysfact=2.0)
   e=[]
   flux=[]
   loerr=[]
   uperr=[]
   for point in sorted(vals.keys()):
    e.append(point)
    flux.append(vals[point][0]*math.pow(point, index))
    loerr.append(vals[point][1][0]*math.pow(point, index))
    uperr.append(vals[point][1][1]*math.pow(point, index))
   if color:
    co=color
    ma="o"
   elif systerr:
        co="r"
        ma="o"
   else:
        co="red"    
        ma="_"
   if not (fitnui[0] and not doublep):    
       if bw:
        p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], fmt='kp')    
       else:
           p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker = ma ,linestyle = " ", color = co ,markeredgecolor = co)    
   if fitnui[0] and len(fitnui)>1:
    modflx=[]
    for point,of,d in zip(e,flux,fitnui[1]):
        modflx.append(((of/math.pow(point, index))+d)*math.pow(point, index))
    if color and not doublep:
        pco=color
    else:
        pco="red"
    #p2,q,r=plt.errorbar(e[:len(modflx)], modflx, yerr=[loerr[:len(modflx)],uperr[:len(modflx)]], marker = "p" ,linestyle = " ", color = pco ,markeredgecolor = co)    
    p2=plt.fill_between(e[:len(modflx)],flux[:len(modflx)],modflx,color="k",alpha=0.3)
    if doublep:    
           return p,p2
    else:
        return p2
   elif fitnui[0]:
    p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker = ma ,linestyle = " ", color = co ,markeredgecolor = co)
    return p         
   else:
    return p    

def plotcalYA2023flux(fig,basepath,index=3.0,vals=False, bw=False,systerr=True,fitnui=[False],finebin=False,DAMPEbin=False,nonormerr=False,onesidesysterr=False,BDT=13,staterrfact=1,color=False,doublep=False):
   if not vals:
    vals=readcalYA2023flxvals(basepath,systerr,asymerr=True,nuisancefit=fitnui[0],finebin=finebin,DAMPEbin=DAMPEbin,nonormerr=nonormerr,onesidesysterr=onesidesysterr,BDT=BDT,staterrfact=staterrfact)
   e=[]
   flux=[]
   loerr=[]
   uperr=[]
   for point in sorted(vals.keys()):
    e.append(point)
    flux.append(vals[point][0]*math.pow(point, index))
    loerr.append(vals[point][1][0]*math.pow(point, index))
    uperr.append(vals[point][1][1]*math.pow(point, index))
   if color:
    co=color
    ma="o"
   elif systerr:
        co="r"
        ma="o"
   else:
        co="red"    
        ma="_"
   if not (fitnui[0] and not doublep):    
       if bw:
        p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], fmt='kp')    
       else:
           p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker = ma ,linestyle = " ", color = co ,markeredgecolor = co)    
   if fitnui[0] and len(fitnui)>1:
    modflx=[]
    for point,of,d in zip(e,flux,fitnui[1]):
        modflx.append(((of/math.pow(point, index))+d)*math.pow(point, index))
    if color and not doublep:
        pco=color
    else:
        pco="red"
    #p2,q,r=plt.errorbar(e[:len(modflx)], modflx, yerr=[loerr[:len(modflx)],uperr[:len(modflx)]], marker = "p" ,linestyle = " ", color = pco ,markeredgecolor = co)    
    p2=plt.fill_between(e[:len(modflx)],flux[:len(modflx)],modflx,color="k",alpha=0.3)
    if doublep:    
           return p,p2
    else:
        return p2
   elif fitnui[0]:
    p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker = ma ,linestyle = " ", color = co ,markeredgecolor = co)
    return p         
   else:
    return p    
    
def plotcalYA2025flux(fig,basepath,index=3.0,vals=False, bw=False,systerr=True,fitnui=[False],finebin=False,DAMPEbin=False,nonormerr=False,onesidesysterr=False,BDT=13,staterrfact=1,color=False,doublep=False,perTeV=False):
   if not vals:
    vals=readcalYA2025flxvals(basepath,systerr,asymerr=True,nuisancefit=fitnui[0],finebin=finebin,DAMPEbin=DAMPEbin,nonormerr=nonormerr,onesidesysterr=onesidesysterr,BDT=BDT,staterrfact=staterrfact)
   e=[]
   flux=[]
   loerr=[]
   uperr=[]
   unitfact=1.0
   if perTeV:
    unitfact=1e-3
   for point in sorted(vals.keys()):
    e.append(point*unitfact)
    flux.append(vals[point][0]*unitfact*math.pow(point, index))
    loerr.append(vals[point][1][0]*unitfact*math.pow(point, index))
    uperr.append(vals[point][1][1]*unitfact*math.pow(point, index))
   if color:
    co=color
    ma="o"
   elif systerr:
        co="r"
        ma="o"
   else:
        co="red"    
        ma="_"
   if not (fitnui[0] and not doublep):    
       if bw:
        p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], fmt='kp')    
       else:
           p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker = ma ,linestyle = " ", color = co ,markeredgecolor = co)    
   if fitnui[0] and len(fitnui)>1:
    modflx=[]
    for point,of,d in zip(e,flux,fitnui[1]):
        modflx.append(((of/math.pow(point, index))+d)*math.pow(point, index))
    if color and not doublep:
        pco=color
    else:
        pco="red"
    #p2,q,r=plt.errorbar(e[:len(modflx)], modflx, yerr=[loerr[:len(modflx)],uperr[:len(modflx)]], marker = "p" ,linestyle = " ", color = pco ,markeredgecolor = co)    
    p2=plt.fill_between(e[:len(modflx)],flux[:len(modflx)],modflx,color="k",alpha=0.3)
    if doublep:    
           return p,p2
    else:
        return p2
   elif fitnui[0]:
    p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker = ma ,linestyle = " ", color = co ,markeredgecolor = co)
    return p         
   else:
    return p    
    
def plotCAL23AMS21flux(fig,basepath,index=3.0,vals=False, bw=False,systerr=True,fitnui=[False],finebin=False,DAMPEbin=False,nonormerr=False,onesidesysterr=False,BDT=13,staterrfact=1,color=False,doublep=False,switchE=10.5,minE=2.0,plotbelowmine=True):
   if not vals:
    vals=mergeYA2023AMS2021(basepath,systerr,asymerr=True,nuisancefit=fitnui[0],finebin=finebin,DAMPEbin=DAMPEbin,nonormerr=nonormerr,onesidesysterr=onesidesysterr,BDT=BDT,staterrfact=staterrfact,switchE=switchE)
   e=[]
   ea=[]
   eb=[]
   flux=[]
   fluxa=[]
   fluxb=[]
   loerr=[]
   uperr=[]
   loerra=[]
   uperra=[]
   loerrb=[]
   uperrb=[]
   for point in sorted(vals.keys()):
    if point<minE:
        if plotbelowmine:
            eb.append(point)
            fluxb.append(vals[point][0]*math.pow(point, index))
            loerrb.append(vals[point][1][0]*math.pow(point, index))
            uperrb.append(vals[point][1][1]*math.pow(point, index))
        else:
            continue
    elif point>switchE:
        e.append(point)
        flux.append(vals[point][0]*math.pow(point, index))
        loerr.append(vals[point][1][0]*math.pow(point, index))
        uperr.append(vals[point][1][1]*math.pow(point, index))
    else:
        ea.append(point)
        fluxa.append(vals[point][0]*math.pow(point, index))
        loerra.append(vals[point][1][0]*math.pow(point, index))
        uperra.append(vals[point][1][1]*math.pow(point, index))
    
   if color:
    co=color
    coa=color
    ma="o"
    maa="s"
   elif systerr:
        co="r"
        coa="orange"
        ma="+"        
        maa="+"
   else:
        co="r"   
        coa="orange"
        ma="_"
        maa="_"
   if plotbelowmine:
       pb,qb,rb=plt.errorbar(eb, fluxb, yerr=[loerrb,uperrb], marker = maa ,linestyle = " ", color = coa ,markeredgecolor = coa)    
   if not (fitnui[0] and not doublep):    
       if bw:
        p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], fmt='kp')    
        pa,qa,ra=plt.errorbar(ea, fluxa, yerr=[loerra,uperra], fmt='ks')    
       else:
        p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker = ma ,linestyle = " ", color = co ,markeredgecolor = co)    
        pa,qa,ra=plt.errorbar(ea, fluxa, yerr=[loerra,uperra], marker = maa ,linestyle = " ", color = coa ,markeredgecolor = coa)    
   if fitnui[0] and len(fitnui)>1:
    modflx=[]
    alle=ea+e
    allflux=fluxa+flux
    print(len(alle),len(allflux),len(fitnui[1]))
    for point,of,d in zip(alle,allflux,fitnui[1]):
        modflx.append(((of/math.pow(point, index))+d)*math.pow(point, index))
    if color and not doublep:
        pco=color
    else:
        pco="r"        
    p2=plt.fill_between(alle[:len(modflx)],allflux[:len(modflx)],modflx,color="k",alpha=0.3)
    if doublep:    
        return p,pa,p2
    else:
        return p2
   elif fitnui[0]:
    p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker = ma ,linestyle = " ", color = co ,markeredgecolor = co)
    pa,qa,ra=plt.errorbar(ea, fluxa, yerr=[loerra,uperra], marker = ma ,linestyle = " ", color = coa ,markeredgecolor = coa)
    return p,pa         
   else:
    return p,pa    

def plotCALpAMSflux(fig,basepath,index=3.0,systerr=True,AMSprefact=-1):
   vals= combocalYA22AMSvals(bp=basepath,systerr=systerr,asymerr=True,AMSprefact=AMSprefact)
   e=[]
   flux=[]
   loerr=[]
   uperr=[]
   for point in sorted(vals.keys()):
    e.append(point)
    flux.append(vals[point][0]*math.pow(point, index))
    loerr.append(vals[point][1][0]*math.pow(point, index))
    uperr.append(vals[point][1][1]*math.pow(point, index))  
   if AMSprefact==-1:
    co="darkcyan"
   elif AMSprefact==-1:
    co="darkblue"
   else:
    co="purple" 
   p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker = "." ,linestyle = " ", color = co ,markeredgecolor = co)
   return p         
   
def plotCALpAMSfluxb(fig,basepath,index=3.0,systerr=True,AMSprefact=-1):
   vals= combocalYA22bAMSvals(bp=basepath,systerr=systerr,asymerr=True,AMSprefact=AMSprefact)
   e=[]
   flux=[]
   loerr=[]
   uperr=[]
   for point in sorted(vals.keys()):
    e.append(point)
    flux.append(vals[point][0]*math.pow(point, index))
    loerr.append(vals[point][1][0]*math.pow(point, index))
    uperr.append(vals[point][1][1]*math.pow(point, index))  
   if AMSprefact==-1:
    co="darkcyan"
   elif AMSprefact==-1:
    co="darkblue"
   else:
    co="purple" 
   p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker = "." ,linestyle = " ", color = co ,markeredgecolor = co)
   return p

def plotts93frac(fig,basepath,tsvals=False):
   if not tsvals:
    tsvals=readts93vals(basepath)
   e=[]
   fract=[]
   sterr=[]
   for point in sorted(tsvals.keys()):
    e.append(point)
    fract.append(tsvals[point][0])
    sterr.append(tsvals[point][1])
   p,q,r=plt.errorbar(e, fract, yerr=sterr, fmt='y.')    
   return p

def plotcapricefrac(fig,basepath):
    p1=plotcaprice94frac(fig,basepath)
    p2=plotcaprice98frac(fig,basepath)
    return p1,p2    

def plotcaprice94frac(fig,basepath,capvals=False):
   if not capvals:
    capvals=readcaprice94vals(basepath)
   e=[]
   fract=[]
   sterr=[]
   for point in sorted(capvals.keys()):
    e.append(point)
    fract.append(capvals[point][0])
    sterr.append(capvals[point][1])
   p,q,r=plt.errorbar(e, fract, yerr=sterr, fmt='kv')    
   return p

def plotcaprice98frac(fig,basepath,capvals=False):
   if not capvals:
    capvals=readcaprice98vals(basepath)
   e=[]
   fract=[]
   sterr=[]
   for point in sorted(capvals.keys()):
    e.append(point)
    fract.append(capvals[point][0])
    sterr.append(capvals[point][1])
   p,q,r=plt.errorbar(e, fract, yerr=sterr, fmt='k^')    
   return p

def plotamsfrac(fig,basepath,amsvals=False, bw=False):
   if not amsvals:
    amsvals=readamsvals(basepath)
   e=[]
   fract=[]
   sterr=[]
   for point in sorted(amsvals.keys()):
    e.append(point)
    fract.append(amsvals[point][0])
    sterr.append(amsvals[point][1])
   if bw:
    p,q,r=plt.errorbar(e, fract, yerr=sterr, fmt='k*')
   else:
    p,q,r=plt.errorbar(e, fract, yerr=sterr, fmt='r.',markeredgecolor = 'r')    
   return p

def plotsystamsfrac(fig,basepath,amsvals=False, bw=False):
   if not amsvals:
    amsvals=readamsvals(basepath)
   e=[]
   fract=[]
   sterr=[]
   for point in sorted(amsvals.keys()):
    e.append(point)
    fract.append(amsvals[point][0])
    sterr.append(amsvals[point][1])
   if bw:
    p,q,r=plt.errorbar(e, fract, yerr=sterr, fmt='k.')
   else:
    p,q,r=plt.errorbar(e, fract, yerr=sterr, fmt='r.',markeredgecolor = 'r')    
   return p

def plotpamelafrac(fig,basepath,pamvals=False, bw=False):
   if not pamvals:
    pamvals=readpamela0vals(basepath)
   e=[]
   fract=[]
   sterr=[]
   for point in sorted(pamvals.keys()):
    e.append(point)
    fract.append(pamvals[point][0])
    sterr.append(pamvals[point][1])
   if bw:
       p,q,r=plt.errorbar(e, fract, yerr=sterr, fmt='kv')    
   else:
    p,q,r=plt.errorbar(e, fract, yerr=sterr, fmt='bv',markeredgecolor = 'b')    
   return p

def plotfermifrac(fig,basepath,fervals=False, bw=False):
   if not fervals:
    fervals=readfermi0vals(basepath)
   e=[]
   fract=[]
   sterr=[]
   for point in sorted(fervals.keys()):
    e.append(point)
    fract.append(fervals[point][0])
    sterr.append(fervals[point][1])
   if bw:
       p,q,r=plt.errorbar(e, fract, yerr=sterr, fmt='k.')    
   else:
    p,q,r=plt.errorbar(e, fract, yerr=sterr, color='seagreen', marker=".", linestyle=" ")    
   return p




def plotDAMPEflux(fig,basepath,index=3,damvals=False, bw=False):
   if not damvals:
    damvals=readDAMPEflxvals(basepath)
   e=[]
   flux=[]
   sterr=[]
   for point in sorted(damvals.keys()):
    e.append(point)
    flux.append(damvals[point][0]*math.pow(point, index))
    sterr.append(damvals[point][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='k.')
   else:    
        p,q,r=plt.errorbar(e, flux, yerr=sterr, color='b', marker=".", linestyle=" ")
   return p    

def plotfermiflux(fig,basepath,index=3,fermivals=False, bw=False):
   if not fermivals:
    fermivals=readfermivals(basepath)
   e=[]
   flux=[]
   sterr=[]
   for point in sorted(fermivals.keys()):
    e.append(point)
    flux.append(fermivals[point][0]*math.pow(point, index))
    sterr.append(fermivals[point][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='k.')
   else:    
        p,q,r=plt.errorbar(e, flux, yerr=sterr, color='seagreen', marker=".", linestyle=" ")
   return p    

def plotpurefermiflux(fig,basepath,index=3,fermivals=False, bw=False):
   if not fermivals:
    fermivals=readfermivals_old(basepath)
   e=[]
   flux=[]
   sterr=[]
   for point in sorted(fermivals.keys()):
    e.append(point)
    flux.append(fermivals[point][0]*math.pow(point, index))
    sterr.append(fermivals[point][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='k.')
   else:    
        p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='c.')
   return p    

def plotpamelaflux(fig,basepath,index=3,pamelavals=False, bw=False):
   if not pamelavals:
    pamelavals=readpamelavals(basepath)
   e=[]
   flux=[]
   sterr=[]
   for point in sorted(pamelavals.keys()):
    e.append(point)
    flux.append(pamelavals[point][0]*math.pow(point, index))
    sterr.append(pamelavals[point][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='kv')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='b.',markeredgecolor = 'b')    
   return p

def plotaticflux(fig,basepath,index=3,aticvals=False, bw=False):
   if not aticvals:
    aticvals=readaticvals(basepath)
   e=[]
   flux=[]
   sterr=[]
   for point in sorted(aticvals.keys()):
    e.append(point)
    flux.append(aticvals[point][0]*math.pow(point, index))
    sterr.append(aticvals[point][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='kx')
   else:    
       p,q,r=plt.errorbar(e, flux, yerr=sterr, linestyle=' ', marker='x', color='pink')    
   return p

def plothesslowEflux(fig,basepath,index=3,hessvals=False, bw=False):
   if not hessvals:
    hessvals=readhesslowEvals(basepath)
   e=[]
   flux=[]
   sterr=[]
   for point in sorted(hessvals.keys()):
    e.append(point)
    flux.append(hessvals[point][0]*math.pow(point, index))
    sterr.append(hessvals[point][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='k^')
   else:    
       p,q,r=plt.errorbar(e, flux, yerr=sterr, marker='^', color="orange", linestyle= ' ' ,markeredgecolor = 'b')    
   return p

def plotpurehesslowEflux(fig,basepath,index=3,hessvals=False, bw=False):
   if not hessvals:
    hessvals=readhesslowEvals_old(basepath)
   e=[]
   flux=[]
   sterr=[]
   for point in sorted(hessvals.keys()):
    e.append(point)
    flux.append(hessvals[point][0]*math.pow(point, index))
    sterr.append(hessvals[point][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='k^')
   else:    
       p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='y^',markeredgecolor = 'b')    
   return p

def plothessstdflux(fig,basepath,index=3,hessvals=False, bw=False):
   if not hessvals:
    hessvals=readhessstdvals(basepath)
   e=[]
   flux=[]
   sterr=[]
   for point in sorted(hessvals.keys()):
    e.append(point)
    flux.append(hessvals[point][0]*math.pow(point, index))
    sterr.append(hessvals[point][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='kv')
   else:    
       p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='yv',markeredgecolor = 'r')    
   return p


def plothessnewflux(fig,basepath,index=3,hessvals=False, bw=False):
   if not hessvals:
    hessvals=readhessnewvals(basepath)
   e=[]
   flux=[]
   loerr=[]
   uperr=[]
   for point in sorted(hessvals.keys()):
    e.append(point)
    flux.append(hessvals[point][0]*math.pow(point, index))
    loerr.append(hessvals[point][1][0]*math.pow(point, index))
    uperr.append(hessvals[point][1][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], fmt='kv')
   else:    
       p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], linestyle = " ", marker = "v", color="purple" ,markeredgecolor = 'purple')
   hsys=readhesssysvals(basepath)
   plt.fill(hsys[0],hsys[1],alpha=0.2,color="purple")
   return p

def plothess2024flux(fig,basepath,index=3,hessvals=False, bw=False):
   if not hessvals:
    hessvals=readhess2024vals(basepath)
   e=[]
   flux=[]
   loerr=[]
   uperr=[]
   uplims=[]
   for point in sorted(hessvals.keys()):
    e.append(point)
    print(point)
    flux.append(hessvals[point][0]*math.pow(point, index))
    loerr.append(hessvals[point][1][0]*math.pow(point, index))
    uperr.append(hessvals[point][1][1]*math.pow(point, index))
    if point>20e3:
        uplims.append(True)
    else:
        uplims.append(False)
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], fmt='kv')
   else:    
       p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], uplims=uplims,linestyle = " ", marker = "s", markersize=4, color="purple" ,markeredgecolor = 'purple')
       
   #hsys24=readhess24sysvals(basepath)
   #plt.fill(hsys24[0],hsys24[1],alpha=0.2,color="purple",label="Estimated true flux")
   #hsys24uncer=readhess24uncervals(basepath)
   #plt.fill(hsys24uncer[0],hsys24uncer[1],alpha=0.2,color="blue")
   #hsys24sysblue=readhess24sysbluevals(basepath)
   #plt.fill(hsys24sysblue[0],hsys24sysblue[1],alpha=0.2,color="blue")
   #hsys24sys20=readhess24sys20vals(basepath)
   #plt.fill(hsys24sys20[0],hsys24sys20[1],alpha=0.2,color="blue",label="95% range considering 2 sigma")
   return p
   
   
def plothess2024limit(fig,basepath,index=3,hessvals=False, bw=False):
   if not hessvals:
    hessvals=readhess2024vals(basepath)
   e=[]
   lims=[]
   for point in sorted(hessvals.keys()):
    if point<2e4:
        shift_e=point*1.21
        e.append(shift_e)
        print(point)
        lims.append((hessvals[point][0]+2*hessvals[point][1][1])*math.pow(shift_e, index))
   p, = plt.plot(e,lims,":",color="purple",alpha=1,linewidth=3) 
   return p
   

def plothess2024estimated(fig,basepath,index=3,hessvals=False, bw=False):
   hsys24=readhess24sysvals(basepath)
   p=plt.fill(hsys24[0],hsys24[1],alpha=0.2,color="purple",label="Estimated true flux")
   return p[0]

def plothess2024sigma2upperlower(fig,basepath,index=3,hessvals=False, bw=False):
   hsys24sigma2upp=readhess24sigma2upp(basepath)
   p, = plt.plot(hsys24sigma2upp[0],hsys24sigma2upp[1],"--",color="blue",alpha=1,linewidth=2)
   #hsys24sigma2low=readhess24sigma2low(basepath)
   #q, = plt.plot(hsys24sigma2low[0],hsys24sigma2low[1],"--",color="blue",alpha=1,linewidth=2)
   return p
   
   
def plothess2024err20flux(fig,basepath,index=3,hessvals=False, bw=False):
   if not hessvals:
    hessvals=readhess2024err20vals(basepath)
   e=[]
   flux=[]
   loerr=[]
   uperr=[]
   for point in sorted(hessvals.keys()):
    e.append(point)
    flux.append(hessvals[point][0]*math.pow(point, index))
    loerr.append(hessvals[point][1][0]*math.pow(point, index))
    uperr.append(hessvals[point][1][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], fmt='kv')
   else:    
       p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], linestyle = " ", marker = "v", color="purple" ,markeredgecolor = 'purple')
   #hsys24=readhess24sysvals(basepath)
   #plt.fill(hsys24[0],hsys24[1],alpha=0.2,color="purple")
   #hsys24uncer=readhess24uncervals(basepath)
   #plt.fill(hsys24uncer[0],hsys24uncer[1],alpha=0.2,color="blue")
   #hsys24sysblue=readhess24sysbluevals(basepath)
   #plt.fill(hsys24sysblue[0],hsys24sysblue[1],alpha=0.2,color="blue")
   #hsys24sys20=readhess24sys20vals(basepath)
   #plt.fill(hsys24sys20[0],hsys24sys20[1],alpha=0.2,color="blue")
   return p



def plotVeritasflux(fig,basepath,index=3,Veritasvals=False, bw=False):
   if not Veritasvals:
    Veritasvals=readVeritasvals(basepath)
   e=[]
   flux=[]
   sterr=[]
   for point in sorted(Veritasvals.keys()):
    e.append(point)
    flux.append(Veritasvals[point][0]*math.pow(point, index))
    sterr.append(Veritasvals[point][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='k^')
   else:    
       p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='b^',markeredgecolor = 'b')    
   return p


def plotcalsimflux(fig,basepath,index=3,calsimvals=False, bw=False):
   if not calsimvals:
    calsimvals=readcalsimvals(basepath)
   e=[]
   flux=[]
   sterr=[]
   for point in sorted(calsimvals.keys()):
    e.append(point)
    flux.append(calsimvals[point][0]*math.pow(point, index-3.0))
    sterr.append(calsimvals[point][1]*math.pow(point, index-3.0))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='ks')
   else:    
       p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='rs',markeredgecolor = 'r')    
   return p

def plotamsflux(fig,basepath,index=3,amsvals=False):
   if not amsvals:
    amsvals=readamsflxvals(basepath)
   e=[]
   flux=[] 
   sterr=[]
   for point in sorted(amsvals.keys()):
    e.append(point)
    flux.append(amsvals[point][0]*math.pow(point, index))
    sterr.append(amsvals[point][1]*math.pow(point, index))
   p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='m*',markeredgecolor = 'm')
   return p


def plotamsnewflux(fig,basepath,index=3,amsvals=False,Eerror=False):
   if not amsvals:
    if Eerror:
        amsvals=readamstotflxvals(basepath,Eindx=index)
        co="pink"
        ma="o"
    else:
        amsvals=readamstotflxvals(basepath)
        co="brown"
        ma="."
   e=[]
   flux=[] 
   sterr=[]
   for point in sorted(amsvals.keys()):
    e.append(point)
    flux.append(amsvals[point][0]*math.pow(point, index))
    sterr.append(amsvals[point][1]*math.pow(point, index))
   p,q,r=plt.errorbar(e, flux, yerr=sterr, marker=ma,color=co, markeredgecolor = co,linestyle=" ")
   return p

def plotamsposflux(fig,basepath,index=3,amsvals=False):
   if not amsvals:
    amsvals=readamsposvals(basepath)
   e=[]
   flux=[] 
   sterr=[]
   for point in sorted(amsvals.keys()):
    e.append(point)
    flux.append(amsvals[point][0]*math.pow(point, index))
    sterr.append(amsvals[point][1]*math.pow(point, index))
   p,q,r=plt.errorbar(e, flux, yerr=sterr, marker='.',color='goldenrod', markeredgecolor = 'goldenrod',linestyle=" ")
   return p


def plotamsposfluxnewest(fig,basepath,index=3,amsvals=False,systerror=True):
   if not amsvals:
    amsvals=readamsposvalsnewest(basepath,systerr=systerror)
   e=[]
   flux=[] 
   sterr=[]
   for point in sorted(amsvals.keys()):
    e.append(point)
    flux.append(amsvals[point][0]*math.pow(point, index))
    sterr.append(amsvals[point][1]*math.pow(point, index))
   p,q,r=plt.errorbar(e, flux, yerr=sterr, marker='+',color='r', markeredgecolor = 'r',linestyle=" ")
   return p



def plotamsposfluxnew(fig,basepath,index=3,amsvals=False):
   if not amsvals:
    amsvals=readamsposvalsnew(basepath)
   e=[]
   flux=[] 
   sterr=[]
   for point in sorted(amsvals.keys()):
    e.append(point)
    flux.append(amsvals[point][0]*math.pow(point, index))
    sterr.append(amsvals[point][1]*math.pow(point, index))
   #p,=plt.plot(e, flux, marker='v',color='orange', markeredgecolor = 'orange',linestyle=" ")
   p,q,r=plt.errorbar(e, flux, yerr=sterr, marker='o',color='lightblue', markeredgecolor = 'darkblue',ecolor='darkblue', linestyle=" ")
   return p


def plotamseleflux(fig,basepath,index=3,amsvals=False):
   if not amsvals:
    amsvals=readamselevals(basepath)
   e=[]
   flux=[] 
   sterr=[]
   for point in sorted(amsvals.keys()):
    e.append(point)
    flux.append(amsvals[point][0]*math.pow(point, index))
    sterr.append(amsvals[point][1]*math.pow(point, index))
   p,q,r=plt.errorbar(e, flux, yerr=sterr, marker='*',color='m', markeredgecolor = 'm',linestyle=" ")
   return p


def plotamselefluxnewest(fig,basepath,index=3,amsvals=False,systerror=True):
   if not amsvals:
    amsvals=readamselevalsnewest(basepath,systerr=systerror)
   e=[]
   flux=[] 
   sterr=[]
   for point in sorted(amsvals.keys()):
    e.append(point)
    flux.append(amsvals[point][0]*math.pow(point, index))
    sterr.append(amsvals[point][1]*math.pow(point, index))
   p,q,r=plt.errorbar(e, flux, yerr=sterr, marker='.',color='goldenrod', markeredgecolor = 'goldenrod',linestyle=" ")
   return p


def plotamstotfluxnewest(fig,basepath,index=3,amsvals=False,systerror=True):
   if not amsvals:
    amsvals=readamstotvalsnewest(basepath,systerr=systerror)
   e=[]
   flux=[] 
   sterr=[]
   for point in sorted(amsvals.keys()):
    e.append(point)
    flux.append(amsvals[point][0]*math.pow(point, index))
    sterr.append(amsvals[point][1]*math.pow(point, index))
   p,q,r=plt.errorbar(e, flux, yerr=sterr, marker='.',color='brown', markeredgecolor = 'brown',linestyle=" ")
   return p

def plotamstotflux2021PR(fig,basepath,index=3,amsvals=False,systerror=True):
   if not amsvals:
    amsvals=readams2021totflxvals(basepath,systerr=systerror)
   e=[]
   flux=[] 
   sterr=[]
   for point in sorted(amsvals.keys()):
    e.append(point)
    flux.append(amsvals[point][0]*math.pow(point, index))
    sterr.append(amsvals[point][1][0]*math.pow(point, index))
   p,q,r=plt.errorbar(e, flux, yerr=sterr, marker='.',color='orange', markeredgecolor = 'orange',linestyle=" ")
   return p

#====================================================================================================
#DRAGON plot routines
#VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV

def interpolatedragon(fdict,phi,si=0):
    pphi=phi[0]
    ephi=phi[1]
    pdict={}
    edict={}
    for e in fdict.keys():
        if e-pphi>0.0:
            solmodp=pow(e-pphi,2)/pow((e),2)    
            pdict[e-pphi]=fdict[e][0+si]*solmodp
        if e-ephi>0.0:
            solmode=pow(e-ephi,2)/pow((e),2)    
            edict[e-ephi]=fdict[e][1+si]*solmode
    nedict={}
    npdict={}
    for pe in pdict.keys():
        if pe in edict.keys():
            continue
        edel=sorted(edict.keys())
        for ei in range(len(edel)):
            he=edel[ei]
            if he>pe:
                le=edel[ei-1]
                lf=edict[le]
                hf=edict[he]
                nedict[pe]=lf+(hf-lf)*(pe-le)/(he-le)
                break
            elif ei==len(edel)-1:
                nedict[ee]=edict[edel[-1]]

    for ee in edict.keys():
        if ee in pdict.keys():
            continue
        edel=sorted(pdict.keys())
        for ei in range(len(edel)):
            he=edel[ei]
            if he>ee:
                le=edel[ei-1]
                lf=pdict[le]
                hf=pdict[he]
                npdict[ee]=lf+(hf-lf)*(ee-le)/(he-le)
                break
            elif ei==len(edel)-1:
                npdict[ee]=pdict[edel[-1]]

    
    edict.update(nedict)
    pdict.update(npdict)
    return edict,pdict
            
        

def plotDragonflux(fig,dragonfile,index=3,dragonpath=False,style=("r","p","r"),phi=[0.0,0.0]):
   if not dragonpath:
    dvals=readDragonOutput(dragonfile)
   else:    
    dvals=readDragonOutput(dragonfile,dragonpath)
   e=[]
   flux=[] 
   edict,pdict=interpolatedragon(dvals,phi)    
   for point in sorted(edict.keys()):
    e.append(point)
    flux.append((edict[point]+pdict[point])*math.pow(point, index))
   p,=plt.plot(e, flux,color=style[0],marker=style[1],markeredgecolor=style[2],linewidth=2,linestyle=" ", alpha=dragonalpha)
   return p

def plotDragonfluxdiff(fig,fit,dragonfile,index=3,dragonpath=False,style=("r","p","r"),phi=[0.0,0.0]):
   if not dragonpath:
    dvals=readDragonOutput(dragonfile)
   else:    
    dvals=readDragonOutput(dragonfile,dragonpath)
   e=[]
   flux=[] 
   edict,pdict=interpolatedragon(dvals,phi)    
   for point in sorted(edict.keys()):
    e.append(point)
    flux.append(((edict[point]+pdict[point])-gssfunc(point,fit))/gssfunc(point,fit))
   p,=plt.plot(e, flux,color=style[0],linewidth=2,linestyle="-", alpha=dragonalpha)
   return p

def plotDragonposflux(fig,dragonfile,index=3,dragonpath=False,style=("r","p","r"),phi=[0.0,0.0]):
   if not dragonpath:
    dvals=readDragonOutput(dragonfile)
   else:    
    dvals=readDragonOutput(dragonfile,dragonpath)
   e=[]
   flux=[] 
   for point in sorted(dvals.keys()):
    if point-phi[0]>0.0:
        solmod=pow(point-phi[0],2)/pow((point),2)    
        e.append(point-phi[0])
        flux.append((dvals[point][0]*solmod)*math.pow(point-phi[0], index))
   p,=plt.plot(e, flux,color=style[0],marker=style[1],markeredgecolor=style[2],linewidth=2,linestyle=" ", alpha=dragonalpha)
   return p

def plotDragoneleflux(fig,dragonfile,index=3,dragonpath=False,style=("r","p","r"),phi=[0.0,0.0]):
   if not dragonpath:
    dvals=readDragonOutput(dragonfile)
   else:    
    dvals=readDragonOutput(dragonfile,dragonpath)
   e=[]
   flux=[] 
   for point in sorted(dvals.keys()):
    if point-phi[1]>0.0:
        solmod=pow(point-phi[1],2)/pow((point),2)    
        e.append(point-phi[1])
        flux.append((dvals[point][1]*solmod)*math.pow(point-phi[1], index))
   p,=plt.plot(e, flux,color=style[0],marker=style[1],markeredgecolor=style[2],linewidth=2,linestyle=" ", alpha=dragonalpha)
   return p

def plotDragonfrac(fig,dragonfile,dragonpath=False,style=("r","p","r"),phi=[0.0,0.0]):
   if not dragonpath:
    dvals=readDragonOutput(dragonfile)
   else:    
    dvals=readDragonOutput(dragonfile,dragonpath)
   e=[]
   frac=[] 
   edict,pdict=interpolatedragon(dvals,phi)    
   for point in sorted(edict.keys()):
    e.append(point)
    frac.append(pdict[point]/(edict[point]+pdict[point]))
   p,=plt.plot(e, frac,color=style[0],marker=style[1],markeredgecolor=style[2],linewidth=2,linestyle=" ", alpha=dragonalpha)
   return p

def plotDragonfracdiff(fig,fit,dragonfile,dragonpath=False,style=("r","p","r"),phi=[0.0,0.0]):
   if not dragonpath:
    dvals=readDragonOutput(dragonfile)
   else:    
    dvals=readDragonOutput(dragonfile,dragonpath)
   e=[]
   frac=[] 
   edict,pdict=interpolatedragon(dvals,phi)    
   for point in sorted(edict.keys()):
    e.append(point)
    frac.append(((pdict[point]/(edict[point]+pdict[point]))-gssfrac(point,fit))/gssfrac(point,fit))
   p,=plt.plot(e, frac,color=style[0],linewidth=2,linestyle="-", alpha=dragonalpha)
   return p



def plotDrabkgflux(fig,dragonfile,index=3,dragonpath=False,style=("g","p","g"),phi=[0.0,0.0]):
   if not dragonpath:
    dvals=readDragonOutput(dragonfile)
   else:    
    dvals=readDragonOutput(dragonfile,dragonpath)
   e=[]
   flux=[] 
   edict,pdict=interpolatedragon(dvals,phi,si=2)    
   for point in sorted(edict.keys()):
    e.append(point)
    flux.append((edict[point]+pdict[point])*math.pow(point, index))
   p,=plt.plot(e, flux,color=style[0],marker=style[1],markeredgecolor=style[2],linewidth=2,linestyle=" ", alpha=dragonalpha)
   return p

def plotDrabkgfluxdiff(fig,fit,dragonfile,index=3,dragonpath=False,style=("r","p","r"),phi=[0.0,0.0]):
   if not dragonpath:
    dvals=readDragonOutput(dragonfile)
   else:    
    dvals=readDragonOutput(dragonfile,dragonpath)
   e=[]
   flux=[] 
   edict,pdict=interpolatedragon(dvals,phi,si=2)    
   for point in sorted(edict.keys()):
    e.append(point)
    flux.append(((edict[point]+pdict[point])-bkgfunc(point,fit))/bkgfunc(point,fit))
   p,=plt.plot(e, flux,color=style[0],linewidth=2,linestyle="-", alpha=dragonalpha)
   return p


def plotDrabkgposflux(fig,dragonfile,index=3,dragonpath=False,style=("g","p","g"),phi=[0.0,0.0]):
   if not dragonpath:
    dvals=readDragonOutput(dragonfile)
   else:    
    dvals=readDragonOutput(dragonfile,dragonpath)
   e=[]
   flux=[] 
   for point in sorted(dvals.keys()):
    if point-phi[0]>0.0:
        solmod=pow(point-phi[0],2)/pow((point),2)    
        e.append(point-phi[0])
        flux.append((dvals[point][2]*solmod)*math.pow(point-phi[0], index))
   p,=plt.plot(e, flux,color=style[0],marker=style[1],markeredgecolor=style[2],linewidth=2,linestyle=" ", alpha=dragonalpha)
   return p

def plotDrabkgeleflux(fig,dragonfile,index=3,dragonpath=False,style=("g","p","g"),phi=[0.0,0.0]):
   if not dragonpath:
    dvals=readDragonOutput(dragonfile)
   else:    
    dvals=readDragonOutput(dragonfile,dragonpath)
   e=[]
   flux=[] 
   for point in sorted(dvals.keys()):
    if point-phi[1]>0.0:
        solmod=pow(point-phi[1],2)/pow((point),2)    
        e.append(point-phi[1])
        flux.append((dvals[point][3]*solmod)*math.pow(point-phi[1], index))
   p,=plt.plot(e, flux,color=style[0],marker=style[1],markeredgecolor=style[2],linewidth=2,linestyle=" ", alpha=dragonalpha)
   return p

def plotDrabkgfrac(fig,dragonfile,dragonpath=False,style=("g","p","g"),phi=[0.0,0.0]):
   if not dragonpath:
    dvals=readDragonOutput(dragonfile)
   else:    
    dvals=readDragonOutput(dragonfile,dragonpath)
   e=[]
   frac=[] 
   edict,pdict=interpolatedragon(dvals,phi,si=2)    
   for point in sorted(edict.keys()):
    e.append(point)
    frac.append(pdict[point]/(edict[point]+pdict[point]))
   p,=plt.plot(e, frac,color=style[0],marker=style[1],markeredgecolor=style[2],linewidth=2,linestyle=" ", alpha=dragonalpha)
   return p

def plotDrabkgfracindx(fig,dragonfile,dragonpath=False,style=("r","p","r"),phi=[0.0,0.0]):
   if not dragonpath:
    dvals=readDragonOutput(dragonfile)
   else:    
    dvals=readDragonOutput(dragonfile,dragonpath)
   e=[]
   frac=[] 
   indx=[]
   edict,pdict=interpolatedragon(dvals,phi,si=2)    
   for point in sorted(edict.keys()):
    if point>300.0:
        break
    e.append(point)
    frac.append(pdict[point]/(edict[point]+pdict[point]))
   for ei in range(1,len(e)-1):
    #print "---------------"
    #print e[ei]
    #print math.log(frac[ei+1]/frac[ei-1])/math.log(e[ei+1]/e[ei-1])
    #print math.log(frac[ei+1]/frac[ei-1])
    #print math.log(e[ei+1]/e[ei-1])
    indx.append(math.log(frac[ei+1]/frac[ei-1])/math.log(e[ei+1]/e[ei-1]))
   p,=plt.plot(e[1:-1],indx,color=style[0],linewidth=2,linestyle="-", alpha=dragonalpha)
   return p

def plotDrabkgfracdiff(fig,fit,dragonfile,dragonpath=False,style=("r","p","r"),phi=[0.0,0.0]):
   if not dragonpath:
    dvals=readDragonOutput(dragonfile)
   else:    
    dvals=readDragonOutput(dragonfile,dragonpath)
   e=[]
   frac=[] 
   edict,pdict=interpolatedragon(dvals,phi,si=2)    
   for point in sorted(edict.keys()):
    e.append(point)
    frac.append(((pdict[point]/(edict[point]+pdict[point]))-bkgfrac(point,fit))/bkgfrac(point,fit))
   p,=plt.plot(e, frac,color=style[0],linewidth=2,linestyle="-", alpha=dragonalpha)
   return p

#===================================================================================================================
# GALPROP
#VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV


def plotGalpropflux(fig,galpropfile,index=3,galproppath=False,style=("y","o","maroon"),phi=[0.0,0.0]):
   if not galproppath:
    dvals=readGalpropOut(galpropfile)
   else:    
    dvals=readGalpropOut(galpropfile,galproppath)
   e=[]
   flux=[] 
   for point in sorted(dvals.keys()):
    e.append(point)
    flxlst=dvals[point]
    flux.append((flxlst[0]+flxlst[1]+flxlst[2])*math.pow(point, index))
   #print e
   #print flux
   p,=plt.plot(e, flux,color=style[0],marker=style[1],markeredgecolor=style[2],linewidth=2,linestyle=" ", alpha=dragonalpha)
   return p

def plotGalpropposflux(fig,galpropfile,index=3,galproppath=False,style=("y","o","maroon"),phi=[0.0,0.0]):
   if not galproppath:
    dvals=readGalpropOut(galpropfile)
   else:    
    dvals=readGalpropOut(galpropfile,galproppath)
   e=[]
   flux=[] 
   for point in sorted(dvals.keys()):
    e.append(point)
    flxlst=dvals[point]
    flux.append((flxlst[0])*math.pow(point, index))
   #print e
   #print flux
   p,=plt.plot(e, flux,color=style[0],marker=style[1],markeredgecolor=style[2],linewidth=2,linestyle=" ", alpha=dragonalpha)
   return p

def plotGalpropeleflux(fig,galpropfile,index=3,galproppath=False,style=("y","o","maroon"),phi=[0.0,0.0]):
   if not galproppath:
    dvals=readGalpropOut(galpropfile)
   else:    
    dvals=readGalpropOut(galpropfile,galproppath)
   e=[]
   flux=[] 
   for point in sorted(dvals.keys()):
    e.append(point)
    flxlst=dvals[point]
    flux.append((flxlst[1]+flxlst[2])*math.pow(point, index))
   #print e
   #print flux
   p,=plt.plot(e, flux,color=style[0],marker=style[1],markeredgecolor=style[2],linewidth=2,linestyle=" ", alpha=dragonalpha)
   return p

def plotGalpropfrac(fig,galpropfile,galproppath=False,style=("y","o","maroon"),phi=[0.0,0.0]):
   if not galproppath:
    dvals=readGalpropOut(galpropfile)
   else:    
    dvals=readGalpropOut(galpropfile,galproppath)
   e=[]
   frac=[] 
   for point in sorted(dvals.keys()):
    e.append(point)
    flxlst=dvals[point]
    frac.append(flxlst[0]/(flxlst[0]+flxlst[1]+flxlst[2]))
   #print e
   #print frac
   p,=plt.plot(e, frac,color=style[0],marker=style[1],markeredgecolor=style[2],linewidth=2,linestyle=" ", alpha=dragonalpha)
   return p

def plotGalpropfracindx(fig,galpropfile,galproppath=False,style=("y","o","maroon"),phi=[0.0,0.0]):
   if not galproppath:
    dvals=readGalpropOut(galpropfile)
   else:    
    dvals=readGalpropOut(galpropfile,galproppath)
   e=[]
   frac=[] 
   indx=[]
   for point in sorted(dvals.keys()):
    if point>300.0:
        break
    e.append(point)
    flxlst=dvals[point]
    frac.append(flxlst[0]/(flxlst[0]+flxlst[1]+flxlst[2]))
   #print e
   #print frac
   for ei in range(1,len(e)-1):
    indx.append(math.log(frac[ei+1]/frac[ei-1])/math.log(e[ei+1]/e[ei-1]))
   p,=plt.plot(e[1:-1],indx,color=style[0],linewidth=2,linestyle="-", alpha=dragonalpha)
   return p

#GALPROP index info:
#nuleus no. 1 - n = 1 Z = 1 A = 0 K = 0     secondary positron
#nuleus no. 2 - n = 2 Z = -1 A = 0 K = 0     secondary electron
#nuleus no. 3 - n = 3 Z = -1 A = 0 K = 0     primary electron
#nuleus no. 4 - n = 4 Z = -1 A = 1 K = 0     tertiary antiproton
#nuleus no. 5 - n = 5 Z = -1 A = 1 K = 0     secondary antiproton
#nuleus no. 6 - n = 6 Z = 1 A = 1 K = 0     secondary proton
#nuleus no. 7 - n = 7 Z = 1 A = 1 K = 0     primary proton
#nuleus no. 8 - n = 8 Z = 1 A = 2 K = 0     deuterons (all zero)

#---------------- PROTON ---------------------------------
#VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV


def plotGalpropproflux(fig,galpropfile,index=2.7,galproppath=False,style=("y","o","maroon"),phi=[0.0,0.0]):
   if not galproppath:
    dvals=readGalpropOut(galpropfile)
   else:    
    dvals=readGalpropOut(galpropfile,galproppath)
   e=[]
   flux=[] 
   for point in sorted(dvals.keys()):
    e.append(point)
    flxlst=dvals[point]
    flux.append((flxlst[5]+flxlst[6])*math.pow(point, index))
   #print e
   #print flux
   p,=plt.plot(e, flux,color=style[0],marker=style[1],markeredgecolor=style[2],linewidth=2,linestyle=" ", alpha=dragonalpha)
   return p


def plotDragonaprfrac(fig,dragonfile,dragonpath=False,style=("b","p","b"),phi=[0.0,0.0]):
   if not dragonpath:
    dvals=readDragonOutput(dragonfile)
   else:    
    dvals=readDragonOutput(dragonfile,dragonpath)
   e=[]
   frac=[] 
   edict,pdict=interpolatedragon(dvals,phi,si=4)    
   for point in sorted(edict.keys()):
    e.append(point)
    frac.append(pdict[point]/(edict[point]+pdict[point]))
   p,=plt.plot(e, frac,color=style[0],marker=style[1],markeredgecolor=style[2],linewidth=2,linestyle=" ", alpha=dragonalpha)
   return p

def plotDragonproflux(fig,dragonfile,index=2.7,dragonpath=False,style=("b","p","b"),phi=[0.0,0.0]):
   if not dragonpath:
    dvals=readDragonOutput(dragonfile)    
   else:    
    dvals=readDragonOutput(dragonfile,dragonpath)
   e=[]
   flux=[] 
   sqpromass=pow(938.272/1000.0,2)
   for point in sorted(dvals.keys()):
    if point-phi[0]>0.0:
        solmod=(pow(point-phi[0],2)-sqpromass)/(pow((point),2)-sqpromass)    
        e.append(point-phi[0])
        flux.append((dvals[point][5]*solmod)*math.pow(point-phi[0], index))
   p,=plt.plot(e, flux,color=style[0],marker=style[1],markeredgecolor=style[2],linewidth=2,linestyle=" ", alpha=dragonalpha)
   return p



def plotpamelaproflux(fig,basepath,index=2.7,pamelavals=False, bw=False):
   if not pamelavals:
    pamelavals=readpamelaprovals(basepath)
   e=[]
   flux=[]
   sterr=[]
   for point in sorted(pamelavals.keys()):
    e.append(point)
    flux.append(pamelavals[point][0]*math.pow(point, index))
    sterr.append(pamelavals[point][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='kv')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='b.',markeredgecolor = 'b')    
   return p


def plotpamelaproSMflux(fig,basepath,index=2.7,pamelavals=False):
   if not pamelavals:
    pamelavals=readpamelaSMvals(basepath)
   e=[]
   flux=[[],[],[],[]]
   sterr=[[],[],[],[]]
   for point in sorted(pamelavals.keys()):
    e.append(point)
    for i in range(4):
        flux[i].append(pamelavals[point][i][0]*math.pow(point, index))
        sterr[i].append(pamelavals[point][i][1]*math.pow(point, index))
   
   p1,q1,r1=plt.errorbar(e, flux[0], yerr=sterr[0], fmt='rv',alpha=0.4)    
   p2,q2,r2=plt.errorbar(e, flux[1], yerr=sterr[1], fmt='yv',alpha=0.4)    
   p3,q3,r3=plt.errorbar(e, flux[2], yerr=sterr[2], fmt='gv',alpha=0.4)    
   p4,q4,r4=plt.errorbar(e, flux[3], yerr=sterr[3], fmt='bv',alpha=0.4)    
   return p1,p2,p3,p4

def plotpamelaproLISflux(fig,basepath,index=2.7,pamelavals=False):
   if not pamelavals:
    pamelavals=readpamelaLISvals(basepath)
   e=[]
   flux=[]
   for point in sorted(pamelavals.keys()):
    e.append(point)
    flux.append(pamelavals[point][0]*math.pow(point, index))
    p,=plt.plot(e, flux, color="blue", linewidth=2, linestyle="-")    
   return p

def plotpamelaaprfrac(fig,basepath,pamelavals=False, bw=False):
   if not pamelavals:
    pamelavals=readpamelaaprvals(basepath)
   e=[]
   frac=[]
   sterr=[]
   for point in sorted(pamelavals.keys()):
    e.append(point)
    frac.append(pamelavals[point][0])
    sterr.append(pamelavals[point][1])
   if bw:
    p,q,r=plt.errorbar(e, frac, yerr=sterr, fmt='kv')    
   else:
       p,q,r=plt.errorbar(e, frac, yerr=sterr, fmt='bv',markeredgecolor = 'b')    
   return p




def plotamsproflux(fig,basepath,index=2.7,amsvals=False, bw=False,convtoE=True):
   if not amsvals:
    amsvals=readamsproflxvals(basepath,convtoE)
   e=[]
   flux=[]
   sterr=[]
   for point in sorted(amsvals.keys()):
    e.append(point)
    flux.append(amsvals[point][0]*math.pow(point, index))
    sterr.append(amsvals[point][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='kv')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=sterr, marker='.', color = "goldenrod",markeredgecolor = 'goldenrod',linestyle = " ",zorder=10)    
   return p

def plotcalproflux(fig,basepath,index=2.7,calvals=False, bw=False,convtoR=False):
   if not calvals:
    calvals=readcalproflxvals(basepath,convtoR)
   e=[]
   flux=[]
   sterr=[]
   for point in sorted(calvals.keys()):
    e.append(point)
    flux.append(calvals[point][0]*math.pow(point, index))
    sterr.append(calvals[point][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='kp')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=sterr, marker='p', color = "r" ,markeredgecolor = "r" ,linestyle = " ")    
   return p
   

def plotcal2021proflux(fig,basepath,index=2.7,calvals=False, bw=False,convtoR=False):
   if not calvals:
    calvals=readcal2021proflxvals(basepath,convtoR)
   e=[]
   flux=[]
   loerr=[]
   uperr=[]
   for point in sorted(calvals.keys()):
    e.append(point)
    flux.append(calvals[point][0]*math.pow(point, index))
    loerr.append(calvals[point][1][0]*math.pow(point, index))
    uperr.append(calvals[point][1][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], fmt='kp')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker='p', color = "r" ,markeredgecolor = "r" ,linestyle = " ",zorder=10)    
   return p   
   
def plotcal2022proflux(fig,basepath,index=2.7,calvals=False, bw=False):
   if not calvals:
    calvals=readcal2022proflxvals(basepath)
   e=[]
   flux=[]
   loerr=[]
   uperr=[]
   for point in sorted(calvals.keys()):
    e.append(point)
    flux.append(calvals[point][0]*math.pow(point, index))
    loerr.append(calvals[point][1][0]*math.pow(point, index))
    uperr.append(calvals[point][1][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], fmt='kp')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker='p', color = "r" ,markeredgecolor = "r" ,linestyle = " ",zorder=10)    
   return p   

def plotvoyagerproflux(fig,basepath,index=2.7,voyvals=False, bw=False):
   if not voyvals:
    voyvals=readvoyagerproflxvals(basepath)
   e=[]
   flux=[]
   err=[]
   for point in sorted(voyvals.keys()):
    e.append(point)
    flux.append(voyvals[point][0]*math.pow(point, index))
    err.append(voyvals[point][1]*math.pow(point, index))
    
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=err, fmt='kv')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=err, marker='v', color = "g" ,markeredgecolor = "g" ,linestyle = " ",zorder=10)    
   return p      
   

def plotDAMPEproflux(fig,basepath,index=2.7,damvals=False, bw=False,convtoR=False):
   if not damvals:
    damvals=readDAMPEproflxvals(basepath,convtoR)
   e=[]
   flux=[]
   sterr=[]
   for point in sorted(damvals.keys()):
    e.append(point)
    flux.append(damvals[point][0]*math.pow(point, index))
    sterr.append(damvals[point][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='k*')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=sterr, marker='s', color = "lightblue" ,markeredgecolor = "lightblue" ,linestyle = " ")    
   return p   


def plotcream1proflux(fig,basepath,index=2.7,vals=False, bw=False):
   if not vals:
    vals=readcreamproflxvals(basepath)
   e=[]
   flux=[]
   loerr=[]
   uperr=[]
   for point in sorted(vals.keys()):
    e.append(point)
    flux.append(vals[point][0]*math.pow(point, index))
    loerr.append(vals[point][1][0]*math.pow(point, index))
    uperr.append(vals[point][1][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], fmt='kp')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker = 'v' ,linestyle = " ", color = 'orange' ,markeredgecolor = 'orange')    
   return p

def plotcream3proflux(fig,basepath,index=2.7,vals=False, bw=False):
   if not vals:
    vals=readcreamproflxvals(basepath,C3=True)
   e=[]
   flux=[]
   loerr=[]
   uperr=[]
   for point in sorted(vals.keys()):
    e.append(point)
    flux.append(vals[point][0]*math.pow(point, index))
    loerr.append(vals[point][1][0]*math.pow(point, index))
    uperr.append(vals[point][1][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], fmt='kp')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker = 'v' ,linestyle = " ", color = 'brown' ,markeredgecolor = 'brown')    
   return p



#---------------- Helium---------------------------------
#VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV

def plotamsHEflux(fig,basepath,index=2.7,amsvals=False, bw=False,convtoE=True):
   if not amsvals:
    amsvals=readamsHEflxvals(basepath,convtoE)
   e=[]
   flux=[]
   sterr=[]
   for point in sorted(amsvals.keys()):
    e.append(point)
    flux.append(amsvals[point][0]*math.pow(point, index))
    sterr.append(amsvals[point][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='k.')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=sterr, color='goldenrod', marker=".", linestyle=" ")    
   return p
   
def plotcalHEflux(fig,basepath,index=2.7,calvals=False, bw=False):
   if not calvals:
    calvals=readcalHEflxvals(basepath)
   e=[]
   flux=[]
   loerr=[]
   uperr=[]
   for point in sorted(calvals.keys()):
    e.append(point)
    flux.append(calvals[point][0]*math.pow(point, index))
    loerr.append(calvals[point][1][0]*math.pow(point, index))
    uperr.append(calvals[point][1][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], fmt='k.')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker = 'd' ,linestyle = " ", color = 'r', markeredgecolor = 'r')    
   return p


def plotcal2021HEflux(fig,basepath,index=2.7,calvals=False, bw=False):
   if not calvals:
    calvals=readcal2021HEflxvals(basepath)
   e=[]
   flux=[]
   loerr=[]
   uperr=[]
   for point in sorted(calvals.keys()):
    e.append(point)
    flux.append(calvals[point][0]*math.pow(point, index))
    loerr.append(calvals[point][1][0]*math.pow(point, index))
    uperr.append(calvals[point][1][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], fmt='k.')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker = 'd' ,linestyle = " ", color = 'r', markeredgecolor = 'r')    
   return p
   
def plotcal2022HEflux(fig,basepath,index=2.7,calvals=False, bw=False):
   if not calvals:
    calvals=readcal2022PRLHEflxvals(basepath)
   e=[]
   flux=[]
   loerr=[]
   uperr=[]
   for point in sorted(calvals.keys()):
    e.append(point)
    flux.append(calvals[point][0]*math.pow(point, index))
    loerr.append(calvals[point][1][0]*math.pow(point, index))
    uperr.append(calvals[point][1][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], fmt='k.')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker = 'd' ,linestyle = " ", color = 'r', markeredgecolor = 'r')    
   return p


def plotamsHE3fract(fig,basepath,amsvals=False, bw=False):
   if not amsvals:
    amsvals=readamsHE3fractvals(basepath)
   e=[]
   fract=[]
   sterr=[]
   for point in sorted(amsvals.keys()):
    e.append(point)
    fract.append(amsvals[point][0])
    sterr.append(amsvals[point][1])
   if bw:
       p,q,r=plt.errorbar(e, fract, yerr=sterr, fmt='k.')    
   else:
    p,q,r=plt.errorbar(e, fract, yerr=sterr, color='goldenrod', marker=".", linestyle=" ")    
   return p
   

def plotDAMPEheflux(fig,basepath,index=2.7,damvals=False, bw=False):
   if not damvals:
    damvals=readDAMPEheflxvals(basepath)
   e=[]
   flux=[]
   sterr=[]
   for point in sorted(damvals.keys()):
    e.append(point)
    flux.append(damvals[point][0]*math.pow(point, index))
    sterr.append(damvals[point][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='k*')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=sterr, marker='s', color = "lightblue" ,markeredgecolor = "lightblue" ,linestyle = " ")    
   return p      



def plotvoyagerheflux(fig,basepath,index=2.7,voyvals=False, bw=False):
   if not voyvals:
    voyvals=readvoyagerheflxvals(basepath)
   e=[]
   flux=[]
   err=[]
   for point in sorted(voyvals.keys()):
    e.append(point)
    flux.append(voyvals[point][0]*math.pow(point, index))
    err.append(voyvals[point][1]*math.pow(point, index))
    
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=err, fmt='kv')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=err, marker='v', color = "g" ,markeredgecolor = "g" ,linestyle = " ",zorder=10)    
   return p      

#---------------- Lithium---------------------------------
#VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV

def plotamsLIflux(fig,basepath,index=2.7,amsvals=False, bw=False,convtoE=True):
   if not amsvals:
    amsvals=readamsLIflxvals(basepath,convtoE)
   e=[]
   flux=[]
   sterr=[]
   for point in sorted(amsvals.keys()):
    e.append(point)
    flux.append(amsvals[point][0]*math.pow(point, index))
    sterr.append(amsvals[point][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='k.')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=sterr, color='goldenrod', marker="^", linestyle=" ")
   return p
   
#---------------- Beryllium---------------------------------
#VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV   
   
def plotamsBEflux(fig,basepath,index=2.7,amsvals=False, bw=False,convtoE=True):
   if not amsvals:
    amsvals=readamsBEflxvals(basepath,convtoE)
   e=[]
   flux=[]
   sterr=[]
   for point in sorted(amsvals.keys()):
    e.append(point)
    flux.append(amsvals[point][0]*math.pow(point, index))
    sterr.append(amsvals[point][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='k.')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=sterr, color='goldenrod', marker="s", linestyle=" ")
   return p   
   
def plotpamelaBeRatio(fig,basepath,pamvals=False, Be9=False):
   if not pamvals:
    pamvals=readpamelaBeRatios(basepath,Be9=Be9)
   e=[]
   fract=[]
   sterr=[]
   for point in sorted(pamvals.keys()):
    e.append(point)
    fract.append(pamvals[point][0])
    sterr.append(pamvals[point][1])
   if Be9:
    p,q,r=plt.errorbar(e, fract, yerr=sterr, color='limegreen', marker="o", linestyle=" ")    
   else:
    p,q,r=plt.errorbar(e, fract, yerr=sterr, color='salmon', marker="s", linestyle=" ")   
   return p

#---------------- Boron---------------------------------
#VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV   

def plotamsBflux(fig,basepath,index=2.7,amsvals=False, bw=False,convtoE=True):
   if not amsvals:
    amsvals=readamsBflxvals(basepath,convtoE)
   e=[]
   flux=[]
   sterr=[]
   for point in sorted(amsvals.keys()):
    e.append(point)
    flux.append(amsvals[point][0]*math.pow(point, index))
    sterr.append(amsvals[point][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='k.')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=sterr, color='goldenrod', marker="p", linestyle=" ")
   return p
   
#---------------- Carbon---------------------------------
#VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV   

def plotamsCflux(fig,basepath,index=2.7,amsvals=False, bw=False,convtoE=True):
   if not amsvals:
    amsvals=readamsCflxvals(basepath,convtoE)
   e=[]
   flux=[]
   sterr=[]
   for point in sorted(amsvals.keys()):
    e.append(point)
    flux.append(amsvals[point][0]*math.pow(point, index))
    sterr.append(amsvals[point][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='k.')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=sterr, color='goldenrod', marker=".", linestyle=" ")  
   return p

def plotcalCflux(fig,basepath,index=2.7,calvals=False, bw=False,convtoR=False):
   if not calvals:
    calvals=readcalCflxvals(basepath)
   e=[]
   flux=[]
   loerr=[]
   uperr=[]
   for point in sorted(calvals.keys()):
    e.append(point)
    flux.append(calvals[point][0]*math.pow(point, index))
    loerr.append(calvals[point][1][0]*math.pow(point, index))
    uperr.append(calvals[point][1][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], fmt='kh')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker='p', color = "r" ,markeredgecolor = "r" ,linestyle = " ")    
   return p
   
   
def plotvoyagercaflux(fig,basepath,index=2.7,voyvals=False, bw=False):
   if not voyvals:
    voyvals=readvoyagercaflxvals(basepath)
   e=[]
   flux=[]
   err=[]
   for point in sorted(voyvals.keys()):
    e.append(point)
    flux.append(voyvals[point][0]*math.pow(point, index))
    err.append(voyvals[point][1]*math.pow(point, index))
    
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=err, fmt='kv')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=err, marker='v', color = "g" ,markeredgecolor = "g" ,linestyle = " ",zorder=10)    
   return p      

   
def plotpamelaBCratio(fig,basepath,pamvals=False, bw=False):
   if not pamvals:
    pamvals=readpamelaBCratio(basepath)
   e=[]
   fract=[]
   sterr=[]
   for point in sorted(pamvals.keys()):
    e.append(point)
    fract.append(pamvals[point][0])
    sterr.append(pamvals[point][1])
   if bw:
       p,q,r=plt.errorbar(e, fract, yerr=sterr, fmt='k*')    
   else:
    p,q,r=plt.errorbar(e, fract, yerr=sterr, color='b', marker=".", linestyle=" ")    
   return p

def plotamsBCratio(fig,basepath,amsvals=False, bw=False):
   if not amsvals:
    amsvals=readamsBCratio(basepath)
   e=[]
   fract=[]
   sterr=[]
   for point in sorted(amsvals.keys()):
    e.append(point)
    fract.append(amsvals[point][0])
    sterr.append(amsvals[point][1])
   if bw:
       p,q,r=plt.errorbar(e, fract, yerr=sterr, fmt='k.')    
   else:
    p,q,r=plt.errorbar(e, fract, yerr=sterr, color='goldenrod', marker=".", linestyle=" ")    
   return p
   

def plotYAcalBCratio(fig,basepath,calvals=False, bw=False):
   if not calvals:
    calvals=readYAcalBCratio(basepath)
   e=[]
   fract=[]
   sterr=[]
   for point in sorted(calvals.keys()):
    e.append(point)
    fract.append(calvals[point][0])
    sterr.append(calvals[point][1])
   if bw:
       p,q,r=plt.errorbar(e, fract, yerr=sterr, fmt='k.')    
   else:
    p,q,r=plt.errorbar(e, fract, yerr=sterr, color='r', marker="p", linestyle=" ")    
   return p   
   

def plotcal2021BCratio(fig,basepath,calvals=False, bw=False):
   if not calvals:
    calvals=readcal2021BCratio(basepath)
   e=[]
   fract=[]
   loerr=[]
   uperr=[]
   for point in sorted(calvals.keys()):
    e.append(point)
    fract.append(calvals[point][0])
    loerr.append(calvals[point][1][0])
    uperr.append(calvals[point][1][1])
   if bw:
       p,q,r=plt.errorbar(e, fract, yerr=sterr, fmt='k.')    
   else:
    p,q,r=plt.errorbar(e, fract, yerr=[loerr,uperr], color='r', marker="p", linestyle=" ")    
   return p      
   
def plotcal2022BCratio(fig,basepath,calvals=False, bw=False):
   if not calvals:
    calvals=readcal2022PBBCratio(basepath)
   e=[]
   fract=[]
   loerr=[]
   uperr=[]
   for point in sorted(calvals.keys()):
    e.append(point)
    fract.append(calvals[point][0])
    loerr.append(calvals[point][1][0])
    uperr.append(calvals[point][1][1])
   if bw:
       p,q,r=plt.errorbar(e, fract, yerr=sterr, fmt='k.')    
   else:
    p,q,r=plt.errorbar(e, fract, yerr=[loerr,uperr], color='r', marker="p", linestyle=" ")    
   return p   

#---------------- Oxygen---------------------------------
#VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV   
   
def plotamsOflux(fig,basepath,index=2.7,amsvals=False, bw=False,convtoE=True):
   if not amsvals:
    amsvals=readamsOflxvals(basepath,convtoE)
   e=[]
   flux=[]
   sterr=[]
   for point in sorted(amsvals.keys()):
    e.append(point)
    flux.append(amsvals[point][0]*math.pow(point, index))
    sterr.append(amsvals[point][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='k8')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=sterr, color='goldenrod', marker=".", linestyle=" ")
   return p

def plotcalOflux(fig,basepath,index=2.7,calvals=False, bw=False,convtoR=False):
   if not calvals:
    calvals=readcalOflxvals(basepath)
   e=[]
   flux=[]
   loerr=[]
   uperr=[]
   for point in sorted(calvals.keys()):
    e.append(point)
    flux.append(calvals[point][0]*math.pow(point, index))
    loerr.append(calvals[point][1][0]*math.pow(point, index))
    uperr.append(calvals[point][1][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], fmt='k8')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker='p', color = "r" ,markeredgecolor = "r" ,linestyle = " ")    
   return p   
   
def plotcalCOratio(fig,basepath,calvals=False, bw=False):
   if not calvals:
    calvals=readcalCOratio(basepath)
   e=[]
   fract=[]
   loerr=[]
   uperr=[]
   for point in sorted(calvals.keys()):
    e.append(point)
    fract.append(calvals[point][0])
    loerr.append(calvals[point][1][0])
    uperr.append(calvals[point][1][1])
   if bw:
    p,q,r=plt.errorbar(e, fract, yerr=[loerr,uperr], fmt='k.')    
   else:
       p,q,r=plt.errorbar(e, fract, yerr=[loerr,uperr], marker='.', color = "r" ,markeredgecolor = "r" ,linestyle = " ")    
   return p      

def plotvoyageroxflux(fig,basepath,index=2.7,voyvals=False, bw=False):
   if not voyvals:
    voyvals=readvoyageroxflxvals(basepath)
   e=[]
   flux=[]
   err=[]
   for point in sorted(voyvals.keys()):
    e.append(point)
    flux.append(voyvals[point][0]*math.pow(point, index))
    err.append(voyvals[point][1]*math.pow(point, index))
    
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=err, fmt='kv')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=err, marker='v', color = "g" ,markeredgecolor = "g" ,linestyle = " ",zorder=10)    
   return p      

#---------------- Neon---------------------------------
#VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV   
   
def plotamsNEflux(fig,basepath,index=2.7,amsvals=False, bw=False,convtoE=True):
   if not amsvals:
    amsvals=readamsNEflxvals(basepath,convtoE)
   e=[]
   flux=[]
   sterr=[]
   for point in sorted(amsvals.keys()):
    e.append(point)
    flux.append(amsvals[point][0]*math.pow(point, index))
    sterr.append(amsvals[point][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='k.')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=sterr, color='goldenrod', marker=".", linestyle=" ")
   return p

#---------------- Magnesium---------------------------------
#VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV   
   
def plotamsMNflux(fig,basepath,index=2.7,amsvals=False, bw=False,convtoE=True):
   if not amsvals:
    amsvals=readamsMNflxvals(basepath,convtoE)
   e=[]
   flux=[]
   sterr=[]
   for point in sorted(amsvals.keys()):
    e.append(point)
    flux.append(amsvals[point][0]*math.pow(point, index))
    sterr.append(amsvals[point][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='ko')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=sterr, color='goldenrod', marker=".", linestyle=" ")
   return p


#---------------- Silicon---------------------------------
#VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV      

def plotamsSIflux(fig,basepath,index=2.7,amsvals=False, bw=False,convtoE=True):
   if not amsvals:
    amsvals=readamsSIflxvals(basepath,convtoE)
   e=[]
   flux=[]
   sterr=[]
   for point in sorted(amsvals.keys()):
    e.append(point)
    flux.append(amsvals[point][0]*math.pow(point, index))
    sterr.append(amsvals[point][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='k.')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=sterr, color='goldenrod', marker=".", linestyle=" ")
   return p   
   
   
#----------------Iron---------------------------------
#VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV      

def plotcalFeflux(fig,basepath,index=2.6,calvals=False, bw=False,convtoR=False):
   if not calvals:
    calvals=readcalFeflxvals(basepath)
   e=[]
   flux=[]
   loerr=[]
   uperr=[]
   for point in sorted(calvals.keys()):
    e.append(point)
    flux.append(calvals[point][0]*math.pow(point, index))
    loerr.append(calvals[point][1][0]*math.pow(point, index))
    uperr.append(calvals[point][1][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], fmt='ko')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker='p', color = "r" ,markeredgecolor = "r" ,linestyle = " ")    
   return p

def plotamsFEflux(fig,basepath,index=2.7,amsvals=False, bw=False,convtoE=True):
   if not amsvals:
    amsvals=readamsFEflxvals(basepath,convtoE)
   e=[]
   flux=[]
   sterr=[]
   for point in sorted(amsvals.keys()):
    e.append(point)
    flux.append(amsvals[point][0]*math.pow(point, index))
    sterr.append(amsvals[point][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='k.')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=sterr, color='goldenrod', marker=".", linestyle=" ")
   return p   
   
def plotamsFEOratio(fig,basepath,amsvals=False, bw=False):
   if not amsvals:
    amsvals=readamsFEOratio(basepath)
   e=[]
   frac=[]
   sterr=[]
   for point in sorted(amsvals.keys()):
    e.append(point)
    frac.append(amsvals[point][0])
    sterr.append(amsvals[point][1])
   if bw:
    p,q,r=plt.errorbar(e, frac, yerr=sterr, fmt='k.')    
   else:
       p,q,r=plt.errorbar(e, frac, yerr=sterr, color='goldenrod', marker=".", linestyle=" ")
   return p
   
def plotamsFESIratio(fig,basepath,amsvals=False, bw=False):
   if not amsvals:
    amsvals=readamsFESIratio(basepath)
   e=[]
   frac=[]
   sterr=[]
   for point in sorted(amsvals.keys()):
    e.append(point)
    frac.append(amsvals[point][0])
    sterr.append(amsvals[point][1])
   if bw:
    p,q,r=plt.errorbar(e, frac, yerr=sterr, fmt='k.')    
   else:
       p,q,r=plt.errorbar(e, frac, yerr=sterr, color='goldenrod', marker=".", linestyle=" ")
   return p   
   
def plotamsFEHEratio(fig,basepath,amsvals=False, bw=False):
   if not amsvals:
    amsvals=readamsFEHEratio(basepath)
   e=[]
   frac=[]
   sterr=[]
   for point in sorted(amsvals.keys()):
    e.append(point)
    frac.append(amsvals[point][0])
    sterr.append(amsvals[point][1])
   if bw:
    p,q,r=plt.errorbar(e, frac, yerr=sterr, fmt='k.')    
   else:
       p,q,r=plt.errorbar(e, frac, yerr=sterr, color='goldenrod', marker=".", linestyle=" ")
   return p      


def plotheaoFeSubFeratio(fig,basepath,hvals=False):
   if not hvals:
      hvals=readheaoFeSubFeratio(basepath)
   e=[]
   ratio=[]
   loerr=[]
   uperr=[]
   for point in sorted(hvals.keys()):
    e.append(point)
    ratio.append(hvals[point][0])
    loerr.append(hvals[point][1][0])
    uperr.append(hvals[point][1][1])

   p,q,r=plt.errorbar(e, ratio, yerr=[loerr,uperr], marker=".", markersize="8",color = "g" ,markeredgecolor = "g" ,linestyle = " ")    
   return p


def plotsanrikuFeSubFeratio(fig,basepath,hvals=False):
   if not hvals:
      hvals=readsanrikuFeSubFeratio(basepath)
   e=[]
   ratio=[]
   loerr=[]
   uperr=[]
   for point in sorted(hvals.keys()):
    e.append(point)
    ratio.append(hvals[point][0])
    loerr.append(hvals[point][1][0])
    uperr.append(hvals[point][1][1])

   p,q,r=plt.errorbar(e, ratio, yerr=[loerr,uperr], marker="s", markersize="5",color = "peru" ,markeredgecolor = "peru" ,linestyle = " ")    
   return p


   
#----------------Nickel---------------------------------
#VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV 

def plotcalNiflux(fig,basepath,index=2.6,calvals=False, bw=False,convtoR=False):
   if not calvals:
    calvals=readcalNiflxvals(basepath)
   e=[]
   flux=[]
   loerr=[]
   uperr=[]
   for point in sorted(calvals.keys()):
    e.append(point)
    flux.append(calvals[point][0]*math.pow(point, index))
    loerr.append(calvals[point][1][0]*math.pow(point, index))
    uperr.append(calvals[point][1][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], fmt='ko')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=[loerr,uperr], marker='o', color = "r" ,markeredgecolor = "2" ,linestyle = " ")    
   return p

def plotcalFeNiratio(fig,basepath,calvals=False):
   if not calvals:
      calvals=readcalFeNiratio(basepath)
   e=[]
   ratio=[]
   loerr=[]
   uperr=[]
   for point in sorted(calvals.keys()):
    e.append(point)
    ratio.append(calvals[point][0])
    loerr.append(calvals[point][1][0])
    uperr.append(calvals[point][1][1])

   p,q,r=plt.errorbar(e, ratio, yerr=[loerr,uperr], marker='o', color = "r" ,markeredgecolor = "2" ,linestyle = " ")    
   return p

def plotheaoFeNiratio(fig,basepath,hvals=False):
   if not hvals:
      hvals=readheaoFeNiratio(basepath)
   e=[]
   ratio=[]
   loerr=[]
   uperr=[]
   for point in sorted(hvals.keys()):
    e.append(point)
    ratio.append(hvals[point][0])
    loerr.append(hvals[point][1][0])
    uperr.append(hvals[point][1][1])

   p,q,r=plt.errorbar(e, ratio, yerr=[loerr,uperr], marker="*", markersize="12",color = "k" ,markeredgecolor = "2" ,linestyle = " ")    
   return p



#---------------- Abundances---------------------------------
#VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV   

def plotUlyssesratio(Z1,Z2,basepath):
    uvals=readUlyssesnucratio(Z1,Z2,basepath)
    e=[]
    frac=[]
    sterr=[]
    for point in sorted(uvals.keys()):
        e.append(point)
        frac.append(uvals[point][0])
        sterr.append(uvals[point][1])
    p,q,r=plt.errorbar(e, frac, yerr=sterr, color='darkorange', marker="s", linestyle=" ")
    return p
    

#---------------- Antiproton---------------------------------
#VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV   

def plotamsaprfrac(fig,basepath,amsvals=False, bw=False):
   if not amsvals:
    amsvals=readamsaprvals(basepath)
   e=[]
   frac=[]
   sterr=[]
   for point in sorted(amsvals.keys()):
    e.append(point)
    frac.append(amsvals[point][0])
    sterr.append(amsvals[point][1])
   if bw:
    p,q,r=plt.errorbar(e, frac, yerr=sterr, fmt='kv')    
   else:
       p,q,r=plt.errorbar(e, frac, yerr=sterr, color='goldenrod', marker=".", linestyle=" ")
   return p


def plotamsaprflux(fig,basepath,index=2.7,amsvals=False, bw=False):
   if not amsvals:
    amsvals=readamsaprvals(basepath,returnflux=True)
   e=[]
   frac=[]
   flux=[]
   sterr=[]
   for point in sorted(amsvals.keys()):
    e.append(point)
    flux.append(amsvals[point][0]*math.pow(point, index))
    sterr.append(amsvals[point][1]*math.pow(point, index))
   if bw:
    p,q,r=plt.errorbar(e, flux, yerr=sterr, fmt='k.')    
   else:
       p,q,r=plt.errorbar(e, flux, yerr=sterr, color='goldenrod', marker="*", linestyle=" ")
   return p



#---------------- Index ---------------------------------
#VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV   

def plotamspliele(fig,basepath,ivals=False, bw=False):
   if not ivals:
    ivals=readAMSindexele(basepath)
   e=[]
   ind=[]
   sterr=[]
   for point in sorted(ivals.keys()):
    e.append(point)
    ind.append(ivals[point][0])
    sterr.append(ivals[point][1])
   if bw:
    p,q,r=plt.errorbar(e, ind, yerr=sterr, fmt='b.')    
   else:
       p,q,r=plt.errorbar(e, ind, yerr=sterr, fmt='b.',markeredgecolor = 'b')    
   return p

def plotamsplipos(fig,basepath,ivals=False, bw=False):
   if not ivals:
    ivals=readAMSindexpos(basepath)
   e=[]
   ind=[]
   sterr=[]
   for point in sorted(ivals.keys()):
    e.append(point)
    ind.append(ivals[point][0])
    sterr.append(ivals[point][1])
   if bw:
    p,q,r=plt.errorbar(e, ind, yerr=sterr, fmt='r.')    
   else:
       p,q,r=plt.errorbar(e, ind, yerr=sterr, fmt='r.',markeredgecolor = 'r')    
   return p
