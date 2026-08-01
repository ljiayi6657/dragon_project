#!/usr/bin/python3
from __future__ import print_function
import os, sys, time, math

import pickle

import numpy as np

from bisect import bisect_left

np.seterr(divide='ignore')
np.seterr(over='ignore')
np.seterr(invalid='ignore')

timeinsec=365.25*24*3600    
yearinsec=timeinsec
kpcincm=3.086e+21
kpcinly=3261.56
lightspeed=2.998e+10 #cm/s
enlosb=1.4e-16 #GeV/s
erginGeV=624.151
Thomsonxsec=6.6524587321e-25 #cm^2
#Bfieldstrength=3.75e-6 
Bfieldstrength=7.5e-6 # Gauss
electronmass=0.511e-3 #GeV/c^2
k_b=8.617333262145e-14 #GeV/K

syncb=erginGeV*Thomsonxsec*lightspeed*Bfieldstrength**2/(6*math.pi*electronmass**2) #1/(GeV s)

Uphs=[0.26,0.25,0.055,0.37,0.23,0.12]    # ev/cm^2
Tphs=[2.725,33.07,313.32,3249.3,6150.4,23,209]

zcoeffs=[-3.996e-2,-9.100e-1,-1.197e-1,3.305e-3,1.044e-3,-7.013e-5,-9.618e-6] 	

ICb=Thomsonxsec*lightspeed*4/(3*electronmass**2) #  1/(GeV^2 s cm^2)


Robs=8.3 #kpc   

precalcfolder="/home/motz/CALETana/astro/"


def loadresults(rfn):
    sfile=open(rfn,'rb')   
    loadthing=pickle.load(sfile)
    sfile.close
    return loadthing

def initpropmod(promod):
        
    global propmod

    global fixDC
    global fixPS
    global diffnormrad
    global diffnormheight
    global highdelt
    global deltbreak
    global deltsoft
    global lowdelt
    global lowdeltbreak
    global lowdeltsoft
    global DB
    global DE
    global fixPSstr
    global fixDCstr
    global difflstr
    global direstr
    global solDC

    propmod=promod
    
    haloz=6 
    if propmod=="C1ZDLB":
        fixDC=3.0664
        fixPS=0.5141
        diffnormrad=10.70
        diffnormheight=4.50
        highdelt=0.0018
        deltbreak=913.5324
        deltsoft=0.4130
        lowdelt=0.2112
        lowdeltbreak=8.4373
        lowdeltsoft=0.0529
        dire=14.7400
    elif propmod=="YDLB":
        fixDC=1.297
        fixPS=0.5742
        diffnormrad=4.62
        highdelt=0.0531
        deltbreak=914.4262
        deltsoft=0.3262
        lowdelt=0.3126
        lowdeltbreak=12.3284
        lowdeltsoft=0.0535
    elif propmod=="XD":
        fixDC=0.16
        fixPS=0.5
        diffnormrad=3.0
        highdelt=0.01
        deltbreak=1000.0 
        deltsoft=0.3 
    elif propmod=="LD":
        fixDC=0.66
        fixPS=0.5
        diffnormrad=4.5
        highdelt=0.2
        deltbreak=500.0 
        deltsoft=0.05     
    elif propmod=="MD":
        fixDC=1.32
        fixPS=0.5
        diffnormrad=4.5
        highdelt=0.2
        deltbreak=500.0 
        deltsoft=0.05         
    elif propmod=="HD":
        fixDC=1.78
        fixPS=0.5
        diffnormrad=4.5
        highdelt=0.2
        deltbreak=500.0 
        deltsoft=0.05             
    else:
        fixDC=1.3
        fixPS=0.6   
    if highdelt:
        DB="B"+(str(deltbreak)).replace(".","d")+("H%1.4f"%highdelt).replace(".","d")+("S%1.4f"%deltsoft).replace(".","d") #"B300d0H0d33S0d2"
    else:
        DB=""
    if lowdelt:
        DB=DB+"LB"+(str(lowdeltbreak)).replace(".","d")+("L%1.4f"%lowdelt).replace(".","d")+("S%1.4f"%lowdeltsoft).replace(".","d") #"B300d0H0d33S0d2"    
        
    DE="-DE%sN0d15R%sB2d0"%(str(diffnormheight).replace(".","d"),str(diffnormrad).replace(".","d"))
    
    fixPSstr=str("-%1.4f"%(fixPS)).replace(".","d")
    if DB:
        fixPSstr=fixPSstr+DB
    fixDCstr="-"+str(fixDC).replace(".","d")
    difflstr="-L%d"%haloz
    solDC=fixDC*math.exp(6.3/diffnormrad)
    if dire > 0:            
        direstr=("-R%1.2f"%dire).replace(".","d")
    else:
        direstr=""
    if DE:      
        direstr=direstr+DE
    if haloz and not haloz==6:
        direstr=direstr+("-L%1.0f"%haloz).replace(".","d")
    if not Bfieldstrength==7.5e-6:
        BF=("-BT%1.4f"%(Bfieldstrength*1e6)).replace(".","d")
        direstr=direstr+BF    
      
def initeloss(pcrd,pcel):        
    global precalcrdiff
    global precalceloss
    global rdiffarray
    global elossarray
    global elossarraykeys
    global elosslist

    precalcrdiff=pcrd
    precalceloss=pcel
    rdiffarray=[]
    elossarray=[]
    elossarraykeys=[]
    elosslist=[]
    
    if precalceloss:
        elossfilearrayname=precalcfolder+"elossdict_%s_100bpd.dat"%propmod
        if os.path.isfile(elossfilearrayname):
            print("loading elossarray")
            lelossarray=loadresults(elossfilearrayname)
            maxkeylen=max([len(ed.keys()) for ed in lelossarray])
            for ed in lelossarray:
                elossarray.append(ed)
                #elossarraykeys.append(np.append(np.array(sorted(ed.keys())),np.full(maxkeylen-len(ed.keys()),max(ed.keys()))))
                elossarraykeys.append(np.array(sorted(ed.keys())))
                #print(len(sorted(ed.keys())))
                
        else:
            print("elossarray not found!")
            sys.exit(1)
        for Ei in range(10001):
            nowe=10**(Ei*0.001)
            elosslist.append(CalcEloss(nowe))
        
        
    if precalcrdiff:
        rdifffilearrayname=precalcfolder+"rdiffarray_%s_100bpd.dat"%propmod
        if os.path.isfile(rdifffilearrayname):
            print("loading rdiffarray")
            lrdiffarray=loadresults(rdifffilearrayname)
            #for rd in lrdiffarray:
                #rdiffarray.append(rd)
            rdiffarray.extend(lrdiffarray)
        else:
            print("rdiffarray not found !")
            sys.exit(1)

def Eloss(E):
    elossarr=np.array(elosslist)
    i=np.maximum(np.minimum((np.ceil(np.log10(E)*1000.0)).astype(int),len(elossarr)),0)
    Eup=10**(i*0.001)
    Elow=10**((i-1)*0.001)
    Ef=(E-Elow)/(Eup-Elow)    
    return np.power(elossarr[i-1],1-Ef)*np.power(elossarr[i],Ef)
    
#def Einitialss(ts,es):
#    out=[]
#    for t in list(ts):
#        out.append([])
#        for e in list(es):
#            out[-1].append(Einitial(t,e))
#    return np.array(out)

#def Einitialss(ts,es):
#    out=[]
#    for t in list(ts):
#        out.append(Einitials(t,es))
#    return np.array(out)
            

def Einitial(t,E):
    i=int(math.ceil(math.log10(E)*100.0))
    Eup=10**(i*0.01)
    Elow=10**((i-1)*0.01)
    Eupdict=elossarray[i]        
    if len(Eupdict.keys())==0:
        return E
    Eupsortkeys=elossarraykeys[i]    
    oet=False
    if t>Eupsortkeys[-1]:
        #print("(Warining) Eup: requested t = %e , maximum t in table is %e , energy = %1.4f"%(t,sorted(Eupdict.keys())[-1],E)) 
        #Eupt=Eupdict[sorted(Eupdict.keys())[-1]]   
        return 0
    elif t<Eupsortkeys[1]:
       Eupt=pow(E,1-(t/Eupsortkeys[0]))*pow(Eupdict[Eupsortkeys[0]],t/Eupsortkeys[0])
    else: 
        ei=bisect_left(Eupsortkeys,t)
        et=Eupsortkeys[ei]
        oet=Eupsortkeys[ei-1]
        Tf=(t-oet)/(et-oet)
        Eupt=pow(Eupdict[oet],1-Tf)*pow(Eupdict[et],Tf)

    Elowdict=elossarray[i-1]
    if len(Elowdict.keys())==0:
        Ef=E/Eup
        return pow(E,1-Ef)*pow(Eupt,Ef)
    Elowsortkeys=elossarraykeys[i-1]      
    oet=False
    if t>Elowsortkeys[-1]:
        print("(Warning1) Elow: requested t = %e , maximum t in table is %e , energy = %1.4f"%(t,sorted(Elowdict.keys())[-1],E)) 
        return 0
        #Elowt=Elowdict[sorted(Elowdict.keys())[-1]]  
    elif t<Elowsortkeys[1]:
       Elowt=pow(E,1-(t/Elowsortkeys[0]))*pow(Elowdict[Elowsortkeys[0]],t/Elowsortkeys[0])
    else: 
        ei=bisect_left(Elowsortkeys,t)
        et=Elowsortkeys[ei]
        oet=Elowsortkeys[ei-1]
        Tf=(t-oet)/(et-oet)
        Elowt=pow(Elowdict[oet],1-Tf)*pow(Elowdict[et],Tf)
    Ef=(E-Elow)/(Eup-Elow)
    return pow(Elowt,1-Ef)*pow(Eupt,Ef)
    
def Einitialss(ts,Es):
    aelossarray=np.array(elossarray)
    aelossarraykeys=np.array(elossarraykeys, dtype=object)
    i=(np.ceil(np.log10(Es)*100.0)).astype(int)
    Eups=10**(i*0.01)
    Elows=10**((i-1)*0.01)
    Eupdict=aelossarray[i]        
    Eupsortkeys=aelossarraykeys[i]      
    Euptl=[]
    for t in ts:
        Euptl.append([])
        for  esk,eud,e in zip(Eupsortkeys,Eupdict,Es):
            if t>esk[-1]: 
                Euptl[-1].append(0)
            elif t<esk[1]:
                Euptl[-1].append(pow(e,1-(t/esk[0]))*pow(eud[esk[0]],t/esk[0]))
            else: 
                ei=bisect_left(esk,t)
                et=esk[ei]
                oet=esk[ei-1]
                Tf=(t-oet)/(et-oet)
                Euptl[-1].append(pow(eud[oet],1-Tf)*pow(eud[et],Tf))
    Eupt=np.array(Euptl)
    Elowdict=aelossarray[i-1]
    Elowsortkeys=aelossarraykeys[i-1]      
    Elowtl=[]
    for t in ts:
        Elowtl.append([])
        for esk,eld,e in zip(Elowsortkeys,Elowdict,Es):
            if t>esk[-1]: 
                Elowtl[-1].append(0)
            elif t<esk[1]:
                Elowtl[-1].append(pow(e,1-(t/esk[0]))*pow(eld[esk[0]],t/esk[0]))
            else: 
                ei=bisect_left(esk,t)
                et=esk[ei]
                oet=esk[ei-1]
                Tf=(t-oet)/(et-oet)
                Elowtl[-1].append(pow(eld[oet],1-Tf)*pow(eld[et],Tf))
    Elowt=np.array(Elowtl)
    Ef=(Es-Elows)/(Eups-Elows)
    return np.power(Elowt,1-Ef)*np.power(Eupt,Ef)
        
def rdiffKN(t,E):
    Ti=int(math.ceil(math.log10(t/yearinsec)*100.0))
    Ei=int(math.ceil(math.log10(E)*100.0))
    nowt=10**(Ti*0.01)
    lowt=10**((Ti-1)*0.01)
    nowe=10**(Ei*0.01)
    lowe=10**((Ei-1)*0.01)
    if Ti<=0 or Ei<=0:
        print("error: time < 1 year (%3.4f) or energy < 1 GeV (%3.4f)"%(nowt,nowe))
        return 0.0
    elif Ti>900 or Ei>600:
        print("error: time > G Myr (%3.4f) or energy > 1000 TeV (%3.4f)"%(nowt,nowe))
        return 0.0
    y1a=rdiffarray[Ti-1][Ei-1]
    y2a=rdiffarray[Ti][Ei-1]
    y1b=rdiffarray[Ti-1][Ei]
    y2b=rdiffarray[Ti][Ei]
    Tf=((t/yearinsec)-lowt)/(nowt-lowt)
    Ef=(E-lowe)/(nowe-lowe)
    ya=pow(y1a,1-Tf)*pow(y2a,Tf)
    yb=pow(y1b,1-Tf)*pow(y2b,Tf)
    y=pow(ya,1-Ef)*pow(yb,Ef)
    #print(t,E,y,ya,yb,y1a,y2a,y1b,y2b)
    return y
    
       
def rdiffKNss(t,E):
    rdiffarr=np.array(rdiffarray)
    Ti=np.maximum(np.minimum((np.ceil(np.log10(t/yearinsec)*100.0)).astype(int),900),0)
    Ei=np.maximum(np.minimum((np.ceil(np.log10(E)*100.0)).astype(int),600),0)    
    nowt=10**(Ti*0.01)
    lowt=10**((Ti-1)*0.01)
    nowe=10**(Ei*0.01)
    lowe=10**((Ei-1)*0.01)    
    y1a=rdiffarr[np.ix_(Ti-1,Ei-1)]
    y2a=rdiffarr[np.ix_(Ti,Ei-1)]
    y1b=rdiffarr[np.ix_(Ti-1,Ei)]
    y2b=rdiffarr[np.ix_(Ti,Ei)]
    Tf=np.broadcast_to(np.expand_dims(((t/yearinsec)-lowt)/(nowt-lowt),axis=1) , y1a.shape) 
    Ef=(E-lowe)/(nowe-lowe)
    ya=np.power(y1a,1-Tf)*np.power(y2a,Tf)
    yb=np.power(y1b,1-Tf)*np.power(y2b,Tf)
    y=np.power(ya,1-Ef)*np.power(yb,Ef)
    #print(t,E,y,ya,yb,y1a,y2a,y1b,y2b)
    return y

#def rdiffKNss(ts,es):
#    out=[]
#    for t in list(ts):
#        out.append([])
#        for e in list(es):
#            out[-1].append(rdiffKN(t,e))
#    return np.array(out)

def breakinjectspec(E,gamma,Ecut,lowgam,lowbrk,lowsft):
    outexp=np.copysign(lowsft,lowgam-gamma)
    inexp=np.absolute(gamma-lowgam)/lowsft
    return np.where(E>0,np.power(E/lowbrk,-lowgam) * np.power(np.power(1+(E/lowbrk),inexp),outexp) * np.exp(-(E/Ecut)),0)     
 
def breakinjectspecarr(E,gamma,Ecut,lowgam,lowbrk,lowsft):
    aE=np.array(E)
    agamma=np.array(gamma)
    aEcut=np.array(Ecut)
    out=[]
    for g in agamma:
        out.append([])
        for c in aEcut:                    
            outexp=np.copysign(lowsft,lowgam-g)
            inexp=np.absolute(g-lowgam)/lowsft
            out.append(np.where(E>0,np.power(E/lowbrk,-lowgam) * np.power(np.power(1+(E/lowbrk),inexp),outexp) * np.exp(-(E/Ecut)),0))      
    return out
    
 
def injectspecarr(E,gamma,Ecut):     
    aE=np.array(E)
    agamma=np.array(gamma)
    aEcut=np.array(Ecut)
    out=[]
    for g in agamma:
        out.append([])
        for c in aEcut:
            out[-1].append(np.where(aE>0, np.power(aE,-g) * np.exp( -(aE/c)),0) )
    return np.array(out)
    
def injectspec(E,gamma,Ecut):     
    return np.where(E>0, np.power(E,-gamma) * np.exp( -(E/Ecut)),0) 
    
    
def pointsourcespecKN(E,time,dist,Q0,gamma,Ecut,lowgamma=False,lowbreak=False,lowsoft=False):
    t=time*yearinsec 
    d=dist*kpcincm
    E0=Einitial(t,E)    
    if E0==0 or E0==np.inf:
        return 0
    rd=rdiffKN(t,E)
    if rd==0:
        return 0
    ps0=lightspeed/(4.0*math.pi*math.pow(math.pi,3.0/2.0))
    if lowgamma and lowbreak and lowsoft:
        ps1=breakinjectspec(E0,gamma,Ecut,lowgamma,lowbreak,lowsoft)
        #ps1=math.pow(E0,-lowgamma) * (1+(E0/lowbreak)**(abs(gamma-lowgamma)/lowsoft))**(math.copysign(lowsoft,lowgamma-gamma)) * math.exp( -(E0/Ecut) )   
    else:
        ps1=injectspec(E0,gamma,Ecut)
    ps2=math.exp( -(  (d*d) / (rd*rd) ) ) / math.pow(rd,3)
    ps3=Eloss(E0)/Eloss(E)
    return Q0*ps0*ps1*ps2*ps3
    
def pointsourcespecKNMEMT(Es,Ts,dist,Q0,gamma,Ecut,lowgamma=False,lowbreak=False,lowsoft=False):    
    ts=np.array(Ts)*yearinsec 
    es=np.array(Es)
    d=dist*kpcincm
    E0s=Einitialss(ts,es)    
    rds=rdiffKNss(ts,es)        
    ps0=lightspeed/(4.0*math.pi*math.pow(math.pi,3.0/2.0))    
    if lowgamma and lowbreak and lowsoft:
        ps1=breakinjectspec(E0s,gamma,Ecut,lowgamma,lowbreak,lowsoft)
        #ps1=math.pow(E0,-lowgamma) * (1+(E0/lowbreak)**(abs(gamma-lowgamma)/lowsoft))**(math.copysign(lowsoft,lowgamma-gamma)) * math.exp( -(E0/Ecut) )   
    else:
        ps1=injectspec(E0s,gamma,Ecut)    
    ps2=np.where(rds>0,np.exp( -( np.power(d,2) / np.power(rds,2) ) ) / np.power(rds,3),0)
    ps3=Eloss(E0s)/Eloss(Es)
    return np.nan_to_num(Q0*ps0*ps1*ps2*ps3)

def pointsourcespecKNMEMTS(Es,Ts,dist,Q0,gammas,Ecuts,lowgamma=False,lowbreak=False,lowsoft=False):    
    ts=np.array(Ts)*yearinsec 
    es=np.array(Es)
    d=dist*kpcincm
    E0s=Einitialss(ts,es)    
    rds=rdiffKNss(ts,es)        
    ps0=lightspeed/(4.0*math.pi*math.pow(math.pi,3.0/2.0))    
    if lowgamma and lowbreak and lowsoft:
        ps1=breakinjectspecarr(E0s,gammas,Ecuts,lowgamma,lowbreak,lowsoft)
        #ps1=math.pow(E0,-lowgamma) * (1+(E0/lowbreak)**(abs(gamma-lowgamma)/lowsoft))**(math.copysign(lowsoft,lowgamma-gamma)) * math.exp( -(E0/Ecut) )   
    else:
        ps1=injectspecarr(E0s,gammas,Ecuts)    
    ps2=np.where(rds>0,np.exp( -( np.power(d,2) / np.power(rds,2) ) ) / np.power(rds,3),0)
    ps3=Eloss(E0s)/Eloss(Es)
    return np.nan_to_num(Q0*ps0*ps1*ps2*ps3)

def CalcEloss(E):
    FKN=0.0
    for T,U in zip(Tphs,Uphs):
        z=4*E*T*k_b/electronmass**2
        if z>150:
            FKN=FKN+U*1e-9*(math.log(z)-1.9805)*45.0/(4*math.pi**2*z**2)*1.0061521608090407
        elif z<1.5e-3:
            FKN=FKN+U*1e-9*0.9435782125275768
        else:
            FKN=FKN+U*1e-9*(15.0/math.pi**4)*math.exp(sum([(zcoeffs[i]*math.log(z)**i) for i in range(len(zcoeffs))]))
    return (syncb+ICb*FKN)*E**2
    
def diffcoeff(E,Enorm=4.0):
    Dnorm=solDC*1.0e28 #cm^2/s
    D=Dnorm*math.pow(E/Enorm,fixPS)
    return D

def DBdiffcoeff(R,RR=4.0):
    D0=solDC*1.0e28
    delta=fixPS
    deltal=lowdelt
    deltah=highdelt
    deltadeltal=delta-deltal
    RBl=lowdeltbreak
    SPl=lowdeltsoft
    RB=deltbreak
    SP=deltsoft
    if RR>RBl:
        D=D0*math.pow(R/RR,delta)
    else:   
        D=D0*math.pow(R/RR,deltal)
    D=D*math.pow((1+math.pow(R/RBl,math.copysign(abs(deltadeltal),RBl-RR)/SPl)),math.copysign(SPl,deltadeltal))
    deltadeltah=deltah-delta
    D=D*math.pow((1+math.pow(R/RB,math.copysign(abs(deltadeltah),RB-RR)/SP)),math.copysign(SP,deltadeltah))    
    return D	

