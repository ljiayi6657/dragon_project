#!/usr/bin/python3
from __future__ import print_function
import os, sys, time, math
import numpy as np
import propfunctions as pf
import matplotlib.pyplot as plt

timeinsec=365.25*24*3600    
yearinsec=timeinsec

globeff=1.0e-3

ages=range(10000,70000,10000)
gams=[1.6,1.85,2.1]
cuts=[10,100,100]

def main():
    #iind=float(sys.argv[1])
    #iEcut=float(sys.argv[2])   
    
    #Ts=np.array([5.0e3,1.0e4,5.0e4,1.0e5])
    #ts=Ts*yearinsec
    #es=np.array([50.0,100.0,500.0,1000.0])
    pf.initpropmod("C1ZDLB")
    pf.initeloss(True,True)

    #e0s=pf.Einitialss(ts,es)
    #print(e0s)

    #r1=pf.Eloss(e0s)
    #r2=pf.Eloss(es)
    #r3=r1/r2
    #print(r1,"----------------\n",r2,"----------------\n",r3)
    #pf.breakinjectspec(es,2.0,20.0e3,1.8,10.0,0.5)
    
    fig = plt.figure(figsize=(10,5))
    fig.patch.set_facecolor('white')
    ax1 = fig.add_subplot(1,1,1)
    for age in ages:
        for iind in gams:
            for iEcut in cuts:            
                plotpulsnew(age,0.3,1e51,iind,iEcut*1000,"r",energylist=False,doplot=True)
    #plotpulsnew(2e5,0.3,1e51,iind,iEcut*1000,"b",energylist=False,doplot=True)
    #plotpulsnew(3e6,0.3,1e51,iind,iEcut*1000,"y",energylist=False,doplot=True)
    plotpulsarr(ages,0.3,1e51,gams,[c*1000 for c in cuts],"g",energylist=False,doplot=True)
    ax1.set_xlabel('E [GeV]', fontsize=12)
    ax1.set_xscale('log')
    ax1.set_yscale('log')
    plt.savefig('../astro/pulsplot/testplot-i%2.2f-c%2.2f.png'%(iind,iEcut),dpi=600)
    
def plotpulsnew(age,dist,Q0,iind,iEcut,col,energylist=False,doplot=True):
    if not energylist:
        e=[]
        for i in range(10,600):
            e.append(10.0**(i*0.01))
    else:    
        e=energylist
    f=[]
    start_time = time.time()
    for nowe in e:    
        f.append(globeff*pulsarspecnew(nowe,age,dist,Q0,iind,iEcut))
    print("B--- %s seconds ---" % (time.time() - start_time))    
    if doplot:    
        p,=plt.plot(e, [ei**3*fi for ei,fi in zip(e,f)], color=col, ls="-",zorder=10)    
        return p,e,f
    else:
        return f
        
    
def plotpulsarr(ages,dist,Q0,iinds,iEcuts,col,energylist=False,doplot=True):
    if not energylist:
        e=[]
        for i in range(10,300):
            e.append(10.0**(i*0.02))
    else:    
        e=energylist
    earr=np.array(e)   
    start_time = time.time()
    farr=pulsarspecarr(earr,ages,dist,Q0,iinds,iEcuts)*globeff    
    print("A--- %s seconds ---" % (time.time() - start_time))
    if doplot:    
        #print(list(farr[0]))        
        for gi in range(len(iinds)):
            for ci in range(len(iEcuts)):
                for ai in range(len(ages)):
                    p,=plt.plot(e, [ei**3*fi for ei,fi in zip(e,list(farr[gi][ci][ai]))], color=col, ls=":",zorder=12)    
        return p,e,list(farr[0])
    else:
        return list(farr[0])
        
def pulsarspecnew(E,time,dist,Q0,gamma,Ecut):
    return pf.pointsourcespecKN(E,time,dist,Q0,gamma,Ecut)
    
        
def pulsarspecarr(es,times,dist,Q0,gamma,Ecut):
    return pf.pointsourcespecKNMEMTS(es,times,dist,Q0,gamma,Ecut)

if __name__ == '__main__':
    sys.exit(main())

