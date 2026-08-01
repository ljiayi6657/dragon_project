#!/usr/local/bin/python
from __future__ import print_function
import os, sys, time, math, pickle

nucdat={}
dalton=931.494/1000.0
nucdat["p"]=(1,1,938.272046/1000.0)
nucdat["He"]=(2,3.667,3.727379508)
nucdat["Li"]=(3,6.515,6.515*dalton)
nucdat["Be"]=(4,7.788,7.788*dalton)
nucdat["B"]=(5,10.81,10.81*dalton)
nucdat["C"]=(6,12.011,12.011*dalton)
nucdat["O"]=(8,15.999,15.999*dalton)
nucdat["Ne"]=(10,20.18,20.18*dalton)
nucdat["Mn"]=(12,24.305,24.305*dalton)
nucdat["Si"]=(14,28.085,28.085*dalton)
nucdat["Fe"]=(26,55.845,55.845*dalton)

def EtoR(flx,En,nuc):
    z,a,rm=nucdat[nuc]
    E=En*a
    rflx=flx*math.sqrt(E*(E+2*rm))/(a*(E+rm))*z
    R=rm*math.sqrt( ( ((E/rm)+1.0)**2)-1.0)/z
    return rflx,R


def RtoE(flx,R,nuc):
    z,a,rm=nucdat[nuc]
    E=math.sqrt((z*R)**2+rm**2)-rm
    eflx=flx*(E+rm)/(math.sqrt(E*(E+2*rm))*z)
    eflx=eflx*a
    En=E/a
    return eflx,En

def PPtoPN(flx,E,nuc):
    z,a,rm=nucdat[nuc]
    En=E/a
    PNflx=flx*a
    return PNflx,En


def readcaltotflxvals(basepath='../',systerr=True,centralval=False):
    calfile=open(basepath+'sumdata/BDT_99.dat','r')
    calvals={}
    while True:
        stringline = calfile.readline()
        if stringline=='':
            break
        elif stringline[0]=="#":
            continue
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))        
        flux=float(stringlist.pop(0))/10000.0/E**3
        lostaterr=float(stringlist.pop(0))/10000.0/E**3
        histaterr=float(stringlist.pop(0))/10000.0/E**3
        losyserr=float(stringlist.pop(0))/10000.0/E**3
        hisyserr=float(stringlist.pop(0))/10000.0/E**3
        lototerr=float(stringlist.pop(0))/10000.0/E**3
        hitoterr=float(stringlist.pop(0))/10000.0/E**3
        if systerr:
            if centralval:
                cflx=flux+(hitoterr-lototerr)*0.5
                calvals[E]=[cflx,(hitoterr+lototerr)*0.5,[E1,E2],0]    
            else:
                calvals[E]=[flux,[lototerr,hitoterr],[E1,E2],0]
        else:
            if centralval:
                cflx=flux+(histaterr-lostaterr)*0.5
                calvals[E]=[cflx,(histaterr+lostaterr)*0.5,[E1,E2],0]    
            else:
                calvals[E]=[flux,[lostaterr,histaterr],[E1,E2],0]
    return calvals


def readcalICRCflxvals(basepath='../',systerr=True,centralval=False):
    calfile=open(basepath+'sumdata/ICRC_30_EShift1035_v170711.dat','r')
    calvals={}
    while True:
        stringline = calfile.readline()
        if stringline=='':
            break
        elif stringline[0]=="#":
            continue
        stringlist=stringline.split()        
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))    
        E=float(stringlist.pop(0))    
        Eerr=float(stringlist.pop(0))
        Ncand=int(stringlist.pop(0))
        rBG=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))/10000.0
        lostaterr=float(stringlist.pop(0))/10000.0
        histaterr=float(stringlist.pop(0))/10000.0
        nsyserr=flux*float(stringlist.pop(0))
        losyserr=flux*float(stringlist.pop(0))
        hisyserr=flux*float(stringlist.pop(0))    
        lototerr=math.sqrt(lostaterr**2+losyserr**2)
        hitoterr=math.sqrt(histaterr**2+hisyserr**2)
        if systerr:
            if centralval:
                cflx=flux+(hitoterr-lototerr)*0.5
                calvals[E]=[cflx,(hitoterr+lototerr)*0.5,[E1,E2],0]    
            else:
                calvals[E]=[flux,[lototerr,hitoterr],[E1,E2],0]
        else:
            if centralval:
                cflx=flux+(histaterr-lostaterr)*0.5
                calvals[E]=[cflx,(histaterr+lostaterr)*0.5,[E1,E2],0]    
            else:
                calvals[E]=[flux,[lostaterr,histaterr],[E1,E2],0]
    return calvals


def readcalPRLflxvals(basepath='../',systerr=True,centralval=False,asymerr=False):
    calfile=open(basepath+'sumdata/PRL_40_21mo_bin3_try13_EShift1035_v170725.dat','r')
    calvals={}
    while True:
        stringline = calfile.readline()
        if stringline=='':
            break
        elif stringline[0]=="#":
            continue
        stringlist=stringline.split()        
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))    
        E=float(stringlist.pop(0))    
        Eerr=float(stringlist.pop(0))
        Ncand=int(stringlist.pop(0))
        rBG=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))/10000.0
        lostaterr=float(stringlist.pop(0))/10000.0
        histaterr=float(stringlist.pop(0))/10000.0
        nsyserr=flux*float(stringlist.pop(0))
        losyserr=flux*float(stringlist.pop(0))
        hisyserr=flux*float(stringlist.pop(0))    
        lototerr=math.sqrt(lostaterr**2+losyserr**2)
        hitoterr=math.sqrt(histaterr**2+hisyserr**2)
        if systerr:
            if centralval:
                cflx=flux+(hitoterr-lototerr)*0.5
                calvals[E]=[cflx,(hitoterr+lototerr)*0.5,[E1,E2],0]    
            elif asymerr:
                calvals[E]=[flux,[lototerr,hitoterr],[E1,E2],0]
            else:
                calvals[E]=[flux,(hitoterr+lototerr)*0.5,[E1,E2],0]
        else:
            if centralval:
                cflx=flux+(histaterr-lostaterr)*0.5
                calvals[E]=[cflx,(histaterr+lostaterr)*0.5,[E1,E2],0]
            elif asymerr:
                calvals[E]=[flux,[lostaterr,histaterr],[E1,E2],0]
            else:
                calvals[E]=[flux,(lostaterr+histaterr)*0.5,[E1,E2],0]    

    
    return calvals

def readcalPRL2flxvals(basepath='../',systerr=True,centralval=False,asymerr=False,DAMPEbin=False,nuisancefit=False,singleerr=False,nonormerr=False):
    if DAMPEbin:
        calfile=open(basepath+'sumdata/PRL__50_26mo_dampe_bin_hs_EShift1035.dat','r')
    else:
        calfile=open(basepath+'sumdata/PRL__50_26mo_bin3_try13_hs_EShift1035.dat','r')
    calvals={}
    while True:
        stringline = calfile.readline()
        if stringline=='':
            break
        elif stringline[0]=="#":
            continue
        stringlist=stringline.split()        
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))    
        E=float(stringlist.pop(0))    
        flux=float(stringlist.pop(0))/10000.0/E**3
        lostaterr=float(stringlist.pop(0))/10000.0/E**3
        histaterr=float(stringlist.pop(0))/10000.0/E**3
        losyserr=float(stringlist.pop(0))/10000.0/E**3
        hisyserr=float(stringlist.pop(0))/10000.0/E**3    
        if nuisancefit:
            loBDTerr=flux*float(stringlist.pop(0))
            hiBDTerr=flux*float(stringlist.pop(0))
            trgerr=flux*float(stringlist.pop(0))
            lototerr=math.sqrt(lostaterr**2+loBDTerr**2+trgerr**2)
            hitoterr=math.sqrt(histaterr**2+hiBDTerr**2+trgerr**2)
            s_norm=flux*float(stringlist.pop(0))
            s_trk=flux*float(stringlist.pop(0)) 
            s_chg=flux*float(stringlist.pop(0)) 
            s_ele=flux*float(stringlist.pop(0)) 
            s_MC=flux*float(stringlist.pop(0))
            nui=(s_norm,s_trk,s_chg,s_ele,s_MC)
        elif singleerr:
            loBDTerr=flux*float(stringlist.pop(0))
            hiBDTerr=flux*float(stringlist.pop(0))
            trgerr=flux*float(stringlist.pop(0))
            nui=False
        elif systerr and nonormerr:
            loBDTerr=flux*float(stringlist.pop(0))
            hiBDTerr=flux*float(stringlist.pop(0))
            trgerr=flux*float(stringlist.pop(0))
            s_norm=flux*float(stringlist.pop(0))
            s_trk=flux*float(stringlist.pop(0)) 
            s_chg=flux*float(stringlist.pop(0)) 
            s_ele=flux*float(stringlist.pop(0)) 
            s_MC=flux*float(stringlist.pop(0))
            lototerr=math.sqrt(lostaterr**2+loBDTerr**2+trgerr**2+s_trk**2+s_chg**2+s_ele**2+s_MC**2)
            hitoterr=math.sqrt(histaterr**2+hiBDTerr**2+trgerr**2+s_trk**2+s_chg**2+s_ele**2+s_MC**2)
            nui=False
        else:        
            lototerr=math.sqrt(lostaterr**2+losyserr**2)
            hitoterr=math.sqrt(histaterr**2+hisyserr**2)
            nui=False
        if systerr:
            if centralval:
                cflx=flux+(hitoterr-lototerr)*0.5
                calvals[E]=[cflx,(hitoterr+lototerr)*0.5,[E1,E2],nui]    
            elif asymerr:
                calvals[E]=[flux,[lototerr,hitoterr],[E1,E2],nui]
            else:
                calvals[E]=[flux,(hitoterr+lototerr)*0.5,[E1,E2],nui]
        elif singleerr:
            if singleerr=="BDT":
                losumerr=math.sqrt(lostaterr**2+loBDTerr**2)
                hisumerr=math.sqrt(histaterr**2+hiBDTerr**2)
            elif singleerr=="TRG":
                losumerr=math.sqrt(lostaterr**2+trgerr**2)
                hisumerr=math.sqrt(histaterr**2+trgerr**2)
            else:
                print("not valid error option")
                sys.exit(1)    
            if centralval:
                cflx=flux+(hisumerr-losumerr)*0.5
                calvals[E]=[cflx,(hisumerr+losumerr)*0.5,[E1,E2],nui]
            elif asymerr:
                calvals[E]=[flux,[losumerr,hisumerr],[E1,E2],nui]
            else:
                calvals[E]=[flux,(losumerr+hisumerr)*0.5,[E1,E2],nui]    
        else:
            if centralval:
                cflx=flux+(histaterr-lostaterr)*0.5
                calvals[E]=[cflx,(histaterr+lostaterr)*0.5,[E1,E2],nui]
            elif asymerr:
                calvals[E]=[flux,[lostaterr,histaterr],[E1,E2],nui]
            else:
                calvals[E]=[flux,(lostaterr+histaterr)*0.5,[E1,E2],nui]    

    
    return calvals

def readcalYA2020flxvals(basepath='../',systerr=True,centralval=False,asymerr=False,DAMPEbin=False,nuisancefit=False,singleerr=False,nonormerr=False,BDT=9):
    if DAMPEbin:
        calfile=open(basepath+'sumdata/PRL__51_live208_dampe_bin_hs_EShift1035.dat','r')
    elif BDT==13:
        calfile=open(basepath+'sumdata/PRL__51_live208_bin3_try13_hs_EShift1035_BDT13.dat','r')
    else:
        calfile=open(basepath+'sumdata/PRL__51_live208_bin3_try13_hs_EShift1035.dat','r')
    calvals={}
    while True:
        stringline = calfile.readline()
        if stringline=='':
            break
        elif stringline[0]=="#":
            continue
        stringlist=stringline.split()        
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))    
        E=float(stringlist.pop(0))    
        flux=float(stringlist.pop(0))/10000.0/E**3
        lostaterr=float(stringlist.pop(0))/10000.0/E**3
        histaterr=float(stringlist.pop(0))/10000.0/E**3
        losyserr=float(stringlist.pop(0))/10000.0/E**3
        hisyserr=float(stringlist.pop(0))/10000.0/E**3    
        if nuisancefit:
            loBDTerr=flux*float(stringlist.pop(0))
            hiBDTerr=flux*float(stringlist.pop(0))
            trgerr=flux*float(stringlist.pop(0))
            lototerr=math.sqrt(lostaterr**2+loBDTerr**2+trgerr**2)
            hitoterr=math.sqrt(histaterr**2+hiBDTerr**2+trgerr**2)
            s_norm=flux*float(stringlist.pop(0))
            s_trk=flux*float(stringlist.pop(0)) 
            s_chg=flux*float(stringlist.pop(0)) 
            s_ele=flux*float(stringlist.pop(0)) 
            s_MC=flux*float(stringlist.pop(0))
            nui=(s_norm,s_trk,s_chg,s_ele,s_MC)
            
        elif singleerr:
            loBDTerr=flux*float(stringlist.pop(0))
            hiBDTerr=flux*float(stringlist.pop(0))
            trgerr=flux*float(stringlist.pop(0))
            nui=False
        elif systerr and nonormerr:
            loBDTerr=flux*float(stringlist.pop(0))
            hiBDTerr=flux*float(stringlist.pop(0))
            trgerr=flux*float(stringlist.pop(0))
            s_norm=flux*float(stringlist.pop(0))
            s_trk=flux*float(stringlist.pop(0)) 
            s_chg=flux*float(stringlist.pop(0)) 
            s_ele=flux*float(stringlist.pop(0)) 
            s_MC=flux*float(stringlist.pop(0))
            lototerr=math.sqrt(lostaterr**2+loBDTerr**2+trgerr**2+s_trk**2+s_chg**2+s_ele**2+s_MC**2)
            hitoterr=math.sqrt(histaterr**2+hiBDTerr**2+trgerr**2+s_trk**2+s_chg**2+s_ele**2+s_MC**2)
            nui=False
        else:        
            lototerr=math.sqrt(lostaterr**2+losyserr**2)
            hitoterr=math.sqrt(histaterr**2+hisyserr**2)
            nui=False
        if systerr:
            if centralval:
                cflx=flux+(hitoterr-lototerr)*0.5
                calvals[E]=[cflx,(hitoterr+lototerr)*0.5,[E1,E2],nui]    
            elif asymerr:
                calvals[E]=[flux,[lototerr,hitoterr],[E1,E2],nui]
            else:
                calvals[E]=[flux,(hitoterr+lototerr)*0.5,[E1,E2],nui]
        elif singleerr:
            if singleerr=="BDT":
                losumerr=math.sqrt(lostaterr**2+loBDTerr**2)
                hisumerr=math.sqrt(histaterr**2+hiBDTerr**2)
            elif singleerr=="TRG":
                losumerr=math.sqrt(lostaterr**2+trgerr**2)
                hisumerr=math.sqrt(histaterr**2+trgerr**2)
            else:
                print("not valid error option")
                sys.exit(1)    
            if centralval:
                cflx=flux+(hisumerr-losumerr)*0.5
                calvals[E]=[cflx,(hisumerr+losumerr)*0.5,[E1,E2],nui]
            elif asymerr:
                calvals[E]=[flux,[losumerr,hisumerr],[E1,E2],nui]
            else:
                calvals[E]=[flux,(losumerr+hisumerr)*0.5,[E1,E2],nui]    
        else:
            if centralval:
                cflx=flux+(histaterr-lostaterr)*0.5
                calvals[E]=[cflx,(histaterr+lostaterr)*0.5,[E1,E2],nui]
            elif asymerr:
                calvals[E]=[flux,[lostaterr,histaterr],[E1,E2],nui]
            else:
                calvals[E]=[flux,(lostaterr+histaterr)*0.5,[E1,E2],nui]    

    #print (calvals)
    return calvals
    
def readcalYA2022flxvals(basepath='../',systerr=True,centralval=False,asymerr=False,DAMPEbin=False,AMSbin=False,nuisancefit=False,singleerr=False,nonormerr=False,BDT=13):
    if BDT==13 and not AMSbin and not DAMPEbin:
        calfile=open(basepath+'sumdata/PRL__51_live214_bin3_try13_hs_EShift1035.dat','r')
    elif BDT==13 and AMSbin:
        calfile=open(basepath+'sumdata/PRL__51_live215_ams_bin_hs_EShift1035.dat','r')
    else:
        print("BDT ",BDT," not available")
        return
    calvals={}
    while True:
        stringline = calfile.readline()
        if stringline=='':
            break
        elif stringline[0]=="#":
            continue
        stringlist=stringline.split()        
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))    
        E=float(stringlist.pop(0))    
        flux=float(stringlist.pop(0))/10000.0/E**3
        lostaterr=float(stringlist.pop(0))/10000.0/E**3
        histaterr=float(stringlist.pop(0))/10000.0/E**3
        losyserr=float(stringlist.pop(0))/10000.0/E**3
        hisyserr=float(stringlist.pop(0))/10000.0/E**3    
        if nuisancefit:
            loBDTerr=flux*float(stringlist.pop(0))
            hiBDTerr=flux*float(stringlist.pop(0))
            trgerr=flux*float(stringlist.pop(0))
            lototerr=math.sqrt(lostaterr**2+loBDTerr**2+trgerr**2)
            hitoterr=math.sqrt(histaterr**2+hiBDTerr**2+trgerr**2)
            s_norm=flux*float(stringlist.pop(0))
            s_trk=flux*float(stringlist.pop(0)) 
            s_chg=flux*float(stringlist.pop(0)) 
            s_ele=flux*float(stringlist.pop(0)) 
            s_MC=flux*float(stringlist.pop(0))
            nui=(s_norm,s_trk,s_chg,s_ele,s_MC)
            
        elif singleerr:
            loBDTerr=flux*float(stringlist.pop(0))
            hiBDTerr=flux*float(stringlist.pop(0))
            trgerr=flux*float(stringlist.pop(0))
            nui=False
        elif systerr and nonormerr:
            loBDTerr=flux*float(stringlist.pop(0))
            hiBDTerr=flux*float(stringlist.pop(0))
            trgerr=flux*float(stringlist.pop(0))
            s_norm=flux*float(stringlist.pop(0))
            s_trk=flux*float(stringlist.pop(0)) 
            s_chg=flux*float(stringlist.pop(0)) 
            s_ele=flux*float(stringlist.pop(0)) 
            s_MC=flux*float(stringlist.pop(0))
            lototerr=math.sqrt(lostaterr**2+loBDTerr**2+trgerr**2+s_trk**2+s_chg**2+s_ele**2+s_MC**2)
            hitoterr=math.sqrt(histaterr**2+hiBDTerr**2+trgerr**2+s_trk**2+s_chg**2+s_ele**2+s_MC**2)
            nui=False
        else:        
            lototerr=math.sqrt(lostaterr**2+losyserr**2)
            hitoterr=math.sqrt(histaterr**2+hisyserr**2)
            nui=False
        if systerr:
            if centralval:
                cflx=flux+(hitoterr-lototerr)*0.5
                calvals[E]=[cflx,(hitoterr+lototerr)*0.5,[E1,E2],nui]    
            elif asymerr:
                calvals[E]=[flux,[lototerr,hitoterr],[E1,E2],nui]
            else:
                calvals[E]=[flux,(hitoterr+lototerr)*0.5,[E1,E2],nui]
        elif singleerr:
            if singleerr=="BDT":
                losumerr=math.sqrt(lostaterr**2+loBDTerr**2)
                hisumerr=math.sqrt(histaterr**2+hiBDTerr**2)
            elif singleerr=="TRG":
                losumerr=math.sqrt(lostaterr**2+trgerr**2)
                hisumerr=math.sqrt(histaterr**2+trgerr**2)
            else:
                print("not valid error option")
                sys.exit(1)    
            if centralval:
                cflx=flux+(hisumerr-losumerr)*0.5
                calvals[E]=[cflx,(hisumerr+losumerr)*0.5,[E1,E2],nui]
            elif asymerr:
                calvals[E]=[flux,[losumerr,hisumerr],[E1,E2],nui]
            else:
                calvals[E]=[flux,(losumerr+hisumerr)*0.5,[E1,E2],nui]    
        else:
            if centralval:
                cflx=flux+(histaterr-lostaterr)*0.5
                calvals[E]=[cflx,(histaterr+lostaterr)*0.5,[E1,E2],nui]
            elif asymerr:
                calvals[E]=[flux,[lostaterr,histaterr],[E1,E2],nui]
            else:
                calvals[E]=[flux,(lostaterr+histaterr)*0.5,[E1,E2],nui]    

    #print (calvals)
    return calvals
    
    
def readcalYA2022bflxvals(basepath='../',systerr=True,centralval=False,asymerr=False,DAMPEbin=False,AMSbin=False,nuisancefit=False,singleerr=False,nonormerr=False,BDT=13,sysfact=1.0):
    if BDT==13 and not AMSbin and not DAMPEbin:
        calfile=open(basepath+'sumdata/PRL__51_live215_bin3_try13_hs_EShift1035.dat','r')
    elif BDT==13 and AMSbin:
        calfile=open(basepath+'sumdata/PRL__51_live215_ams_bin_hs_EShift1035_mod.dat','r')
    else:
        print("BDT ",BDT," not available")
        return
    calvals={}
    while True:
        stringline = calfile.readline()
        if stringline=='':
            break
        elif stringline[0]=="#":
            continue
        stringlist=stringline.split()        
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))    
        E=float(stringlist.pop(0))    
        flux=float(stringlist.pop(0))/10000.0/E**3
        lostaterr=float(stringlist.pop(0))/10000.0/E**3/math.sqrt(sysfact)
        histaterr=float(stringlist.pop(0))/10000.0/E**3/math.sqrt(sysfact)
        losyserr=float(stringlist.pop(0))/10000.0/E**3
        hisyserr=float(stringlist.pop(0))/10000.0/E**3    
        if nuisancefit:
            loBDTerr=flux*float(stringlist.pop(0))
            hiBDTerr=flux*float(stringlist.pop(0))
            trgerr=flux*float(stringlist.pop(0))
            lototerr=math.sqrt(lostaterr**2+loBDTerr**2+trgerr**2)
            hitoterr=math.sqrt(histaterr**2+hiBDTerr**2+trgerr**2)
            s_norm=flux*float(stringlist.pop(0))
            s_trk=flux*float(stringlist.pop(0)) 
            s_chg=flux*float(stringlist.pop(0)) 
            s_ele=flux*float(stringlist.pop(0)) 
            s_MC=flux*float(stringlist.pop(0))
            nui=(s_norm,s_trk,s_chg,s_ele,s_MC)
            
        elif singleerr:
            loBDTerr=flux*float(stringlist.pop(0))
            hiBDTerr=flux*float(stringlist.pop(0))
            trgerr=flux*float(stringlist.pop(0))
            nui=False
        elif systerr and nonormerr:
            loBDTerr=flux*float(stringlist.pop(0))
            hiBDTerr=flux*float(stringlist.pop(0))
            trgerr=flux*float(stringlist.pop(0))
            s_norm=flux*float(stringlist.pop(0))
            s_trk=flux*float(stringlist.pop(0)) 
            s_chg=flux*float(stringlist.pop(0)) 
            s_ele=flux*float(stringlist.pop(0)) 
            s_MC=flux*float(stringlist.pop(0))
            lototerr=math.sqrt(lostaterr**2+loBDTerr**2+trgerr**2+s_trk**2+s_chg**2+s_ele**2+s_MC**2)
            hitoterr=math.sqrt(histaterr**2+hiBDTerr**2+trgerr**2+s_trk**2+s_chg**2+s_ele**2+s_MC**2)
            nui=False
        else:        
            lototerr=math.sqrt(lostaterr**2+losyserr**2)
            hitoterr=math.sqrt(histaterr**2+hisyserr**2)
            nui=False
        if systerr:
            if centralval:
                cflx=flux+(hitoterr-lototerr)*0.5
                calvals[E]=[cflx,(hitoterr+lototerr)*0.5,[E1,E2],nui]    
            elif asymerr:
                calvals[E]=[flux,[lototerr,hitoterr],[E1,E2],nui]
            else:
                calvals[E]=[flux,(hitoterr+lototerr)*0.5,[E1,E2],nui]
        elif singleerr:
            if singleerr=="BDT":
                losumerr=math.sqrt(lostaterr**2+loBDTerr**2)
                hisumerr=math.sqrt(histaterr**2+hiBDTerr**2)
            elif singleerr=="TRG":
                losumerr=math.sqrt(lostaterr**2+trgerr**2)
                hisumerr=math.sqrt(histaterr**2+trgerr**2)
            else:
                print("not valid error option")
                sys.exit(1)    
            if centralval:
                cflx=flux+(hisumerr-losumerr)*0.5
                calvals[E]=[cflx,(hisumerr+losumerr)*0.5,[E1,E2],nui]
            elif asymerr:
                calvals[E]=[flux,[losumerr,hisumerr],[E1,E2],nui]
            else:
                calvals[E]=[flux,(losumerr+hisumerr)*0.5,[E1,E2],nui]    
        else:
            if centralval:
                cflx=flux+(histaterr-lostaterr)*0.5
                calvals[E]=[cflx,(histaterr+lostaterr)*0.5,[E1,E2],nui]
            elif asymerr:
                calvals[E]=[flux,[lostaterr,histaterr],[E1,E2],nui]
            else:
                calvals[E]=[flux,(lostaterr+histaterr)*0.5,[E1,E2],nui]    

    #print (calvals)
    return calvals
    
    
def readcalYA2023flxvals(basepath='../',systerr=True,centralval=False,asymerr=False,finebin=False,DAMPEbin=False,nuisancefit=False,singleerr=False,nonormerr=False,onesidesysterr=False,manualsyserr=False,BDT=13,staterrfact=1):
    if BDT==13 and not finebin and not DAMPEbin:
        calfile=open(basepath+'sumdata/PRL__60_live220_bin3_try13_hs_EShift1035_230912.dat','r')
    elif BDT==13 and finebin and not DAMPEbin:
        calfile=open(basepath+'sumdata/PRL__60_live220_bin3_try13_hs_EShift1035_finebin.dat','r')
    elif BDT==13 and DAMPEbin and not finebin:
        calfile=open(basepath+'sumdata/PRL__60_live220_dampe_bin_hs_EShift1035_1TeVconst.dat','r')
    elif BDT==13 and DAMPEbin and finebin:
        print("error, fine and DAMPE binning requested at the same time")
    else:
        print("BDT ",BDT," not available")
        return
    if not staterrfact==1:            
        import ROOT
        muMax_global=[1000]
        fc68=ROOT.TFeldmanCousins(0.68)
        fc68.SetMuMax(muMax_global[0])
    calvals={}
    while True:
        stringline = calfile.readline()
        if stringline=='':
            break
        elif stringline[0]=="#":
            continue
        stringlist=stringline.split()        
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))    
        E=float(stringlist.pop(0))    
        flux=float(stringlist.pop(0))/10000.0/E**3
        lostaterr=float(stringlist.pop(0))/10000.0/E**3
        histaterr=float(stringlist.pop(0))/10000.0/E**3
        losyserr=float(stringlist.pop(0))/10000.0/E**3
        hisyserr=float(stringlist.pop(0))/10000.0/E**3    
        loBDTerr=flux*float(stringlist.pop(0))
        hiBDTerr=flux*float(stringlist.pop(0))
        trgerr=flux*float(stringlist.pop(0))
        s_norm=flux*float(stringlist.pop(0))
        s_trk=flux*float(stringlist.pop(0)) 
        s_chg=flux*float(stringlist.pop(0)) 
        s_ele=flux*float(stringlist.pop(0)) 
        s_MC=flux*float(stringlist.pop(0))
        nevt=float(stringlist.pop(0)) 
        nbkg=float(stringlist.pop(0))        
        if not staterrfact==1:
            olostaterr=lostaterr
            ohistaterr=histaterr
            if nevt>50:
                lostaterr=olostaterr/math.sqrt(staterrfact)
                histaterr=ohistaterr/math.sqrt(staterrfact)
            else:
                uplim=fc68.CalculateUpperLimit(nevt*staterrfact,0.0)
                errupevt=uplim-(nevt*staterrfact)
                lolim=fc68.GetLowerLimit()
                errloevt=(nevt*staterrfact)-lolim
                print(nevt*staterrfact,nbkg*staterrfact,uplim,lolim,errupevt,errloevt)
                lostaterr=errloevt*flux/nevt    
                histaterr=errupevt*flux/nevt    
            print("energy ",E," , changed lo stat err from ",olostaterr," to ",lostaterr)
            print("energy ",E," , changed hi stat err from ",ohistaterr," to ",histaterr)
        if nuisancefit:            
            lototerr=math.sqrt(lostaterr**2+loBDTerr**2+trgerr**2)
            hitoterr=math.sqrt(histaterr**2+hiBDTerr**2+trgerr**2)            
            nui=(s_norm,s_trk,s_chg,s_ele,s_MC)            
        elif singleerr:            
            nui=False
        elif systerr and manualsyserr:
            if onesidesysterr:
                los_norm=min(s_norm,0)
                his_norm=max(s_norm,0)
                los_trk=min(s_trk,0)
                his_trk=max(s_trk,0)
                los_chg=min(s_chg,0)
                his_chg=max(s_chg,0)
                los_ele=min(s_ele,0)
                his_ele=max(s_ele,0)
                los_MC=min(s_MC,0)
                his_MC=max(s_MC,0)                
            else:
                los_norm=s_norm
                his_norm=s_norm
                los_trk=s_trk
                his_trk=s_trk
                los_chg=s_chg
                his_chg=s_chg
                los_ele=s_ele
                his_ele=s_ele
                los_MC=s_MC
                his_MC=s_MC
            if nonormerr:                
                lototerr=math.sqrt(lostaterr**2+loBDTerr**2+trgerr**2+los_trk**2+los_chg**2+los_ele**2+los_MC**2)
                hitoterr=math.sqrt(histaterr**2+hiBDTerr**2+trgerr**2+his_trk**2+his_chg**2+his_ele**2+his_MC**2)
            else:
                lototerr=math.sqrt(lostaterr**2+loBDTerr**2+trgerr**2+los_trk**2+los_chg**2+los_ele**2+los_MC**2+los_norm**2)
                hitoterr=math.sqrt(histaterr**2+hiBDTerr**2+trgerr**2+his_trk**2+his_chg**2+his_ele**2+his_MC**2+his_norm**2)
            nui=False
        else:        
            lototerr=math.sqrt(lostaterr**2+losyserr**2)
            hitoterr=math.sqrt(histaterr**2+hisyserr**2)
            nui=False
        
            
        if systerr:
            if centralval:
                cflx=flux+(hitoterr-lototerr)*0.5
                calvals[E]=[cflx,(hitoterr+lototerr)*0.5,[E1,E2],nui]    
            elif asymerr:
                calvals[E]=[flux,[lototerr,hitoterr],[E1,E2],nui]
            else:
                calvals[E]=[flux,(hitoterr+lototerr)*0.5,[E1,E2],nui]
        elif singleerr:
            if singleerr=="BDT":
                losumerr=math.sqrt(lostaterr**2+loBDTerr**2)
                hisumerr=math.sqrt(histaterr**2+hiBDTerr**2)
            elif singleerr=="TRG":
                losumerr=math.sqrt(lostaterr**2+trgerr**2)
                hisumerr=math.sqrt(histaterr**2+trgerr**2)
            else:
                print("not valid error option")
                sys.exit(1)    
            if centralval:
                cflx=flux+(hisumerr-losumerr)*0.5
                calvals[E]=[cflx,(hisumerr+losumerr)*0.5,[E1,E2],nui]
            elif asymerr:
                calvals[E]=[flux,[losumerr,hisumerr],[E1,E2],nui]
            else:
                calvals[E]=[flux,(losumerr+hisumerr)*0.5,[E1,E2],nui]    
        else:
            if centralval:
                cflx=flux+(histaterr-lostaterr)*0.5
                calvals[E]=[cflx,(histaterr+lostaterr)*0.5,[E1,E2],nui]
            elif asymerr:
                calvals[E]=[flux,[lostaterr,histaterr],[E1,E2],nui]
            else:
                calvals[E]=[flux,(lostaterr+histaterr)*0.5,[E1,E2],nui]    

    #print (calvals)
    return calvals
    
def readcalYA2025flxvals(basepath='../',systerr=True,centralval=False,asymerr=False,finebin=False,DAMPEbin=False,nuisancefit=False,singleerr=False,nonormerr=False,onesidesysterr=False,manualsyserr=False,BDT=13,staterrfact=1):
    if BDT==13 and not finebin and not DAMPEbin:
        calfile=open(basepath+'sumdata/PRL__60_live222_bin3_try13_hs_EShift1035.dat','r')
    elif BDT==13 and finebin and not DAMPEbin:
        print("data not available")
        sys.exit(1)
        #calfile=open(basepath+'sumdata/PRL__60_live220_bin3_try13_hs_EShift1035_finebin.dat','r')
    elif BDT==13 and DAMPEbin and not finebin:
        print("data not available")
        sys.exit(1)
        #calfile=open(basepath+'sumdata/PRL__60_live220_dampe_bin_hs_EShift1035_1TeVconst.dat','r')
    elif BDT==13 and DAMPEbin and finebin:
        print("error, fine and DAMPE binning requested at the same time")
    else:
        print("BDT ",BDT," not available")
        return
    if not staterrfact==1:            
        import ROOT
        muMax_global=[1000]
        fc68=ROOT.TFeldmanCousins(0.68)
        fc68.SetMuMax(muMax_global[0])
    calvals={}
    while True:
        stringline = calfile.readline()
        if stringline=='':
            break
        elif stringline[0]=="#":
            continue
        stringlist=stringline.split()        
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))    
        E=float(stringlist.pop(0))    
        flux=float(stringlist.pop(0))/10000.0/E**3
        lostaterr=float(stringlist.pop(0))/10000.0/E**3
        histaterr=float(stringlist.pop(0))/10000.0/E**3
        losyserr=float(stringlist.pop(0))/10000.0/E**3
        hisyserr=float(stringlist.pop(0))/10000.0/E**3    
        loBDTerr=flux*float(stringlist.pop(0))
        hiBDTerr=flux*float(stringlist.pop(0))
        trgerr=flux*float(stringlist.pop(0))
        s_norm=flux*float(stringlist.pop(0))
        s_trk=flux*float(stringlist.pop(0)) 
        s_chg=flux*float(stringlist.pop(0)) 
        s_ele=flux*float(stringlist.pop(0)) 
        s_MC=flux*float(stringlist.pop(0))
        #nevt=float(stringlist.pop(0)) 
        #nbkg=float(stringlist.pop(0))        
        if not staterrfact==1:
            print("staterrfact not 1 is not supported, remains at 1")
            #olostaterr=lostaterr
            #ohistaterr=histaterr
            #if nevt>50:
            #    lostaterr=olostaterr/math.sqrt(staterrfact)
            #    histaterr=ohistaterr/math.sqrt(staterrfact)
            #else:
            #    uplim=fc68.CalculateUpperLimit(nevt*staterrfact,0.0)
            #    errupevt=uplim-(nevt*staterrfact)
            #    lolim=fc68.GetLowerLimit()
            #    errloevt=(nevt*staterrfact)-lolim
            #    print(nevt*staterrfact,nbkg*staterrfact,uplim,lolim,errupevt,errloevt)
            #    lostaterr=errloevt*flux/nevt    
            #    histaterr=errupevt*flux/nevt    
            #print("energy ",E," , changed lo stat err from ",olostaterr," to ",lostaterr)
            #print("energy ",E," , changed hi stat err from ",ohistaterr," to ",histaterr)
        if nuisancefit:            
            lototerr=math.sqrt(lostaterr**2+loBDTerr**2+trgerr**2)
            hitoterr=math.sqrt(histaterr**2+hiBDTerr**2+trgerr**2)            
            nui=(s_norm,s_trk,s_chg,s_ele,s_MC)            
        elif singleerr:            
            nui=False
        elif systerr and manualsyserr:
            if onesidesysterr:
                los_norm=min(s_norm,0)
                his_norm=max(s_norm,0)
                los_trk=min(s_trk,0)
                his_trk=max(s_trk,0)
                los_chg=min(s_chg,0)
                his_chg=max(s_chg,0)
                los_ele=min(s_ele,0)
                his_ele=max(s_ele,0)
                los_MC=min(s_MC,0)
                his_MC=max(s_MC,0)                
            else:
                los_norm=s_norm
                his_norm=s_norm
                los_trk=s_trk
                his_trk=s_trk
                los_chg=s_chg
                his_chg=s_chg
                los_ele=s_ele
                his_ele=s_ele
                los_MC=s_MC
                his_MC=s_MC
            if nonormerr:                
                lototerr=math.sqrt(lostaterr**2+loBDTerr**2+trgerr**2+los_trk**2+los_chg**2+los_ele**2+los_MC**2)
                hitoterr=math.sqrt(histaterr**2+hiBDTerr**2+trgerr**2+his_trk**2+his_chg**2+his_ele**2+his_MC**2)
            else:
                lototerr=math.sqrt(lostaterr**2+loBDTerr**2+trgerr**2+los_trk**2+los_chg**2+los_ele**2+los_MC**2+los_norm**2)
                hitoterr=math.sqrt(histaterr**2+hiBDTerr**2+trgerr**2+his_trk**2+his_chg**2+his_ele**2+his_MC**2+his_norm**2)
            nui=False
        else:        
            lototerr=math.sqrt(lostaterr**2+losyserr**2)
            hitoterr=math.sqrt(histaterr**2+hisyserr**2)
            nui=False
        
            
        if systerr:
            if centralval:
                cflx=flux+(hitoterr-lototerr)*0.5
                calvals[E]=[cflx,(hitoterr+lototerr)*0.5,[E1,E2],nui]    
            elif asymerr:
                calvals[E]=[flux,[lototerr,hitoterr],[E1,E2],nui]
            else:
                calvals[E]=[flux,(hitoterr+lototerr)*0.5,[E1,E2],nui]
        elif singleerr:
            if singleerr=="BDT":
                losumerr=math.sqrt(lostaterr**2+loBDTerr**2)
                hisumerr=math.sqrt(histaterr**2+hiBDTerr**2)
            elif singleerr=="TRG":
                losumerr=math.sqrt(lostaterr**2+trgerr**2)
                hisumerr=math.sqrt(histaterr**2+trgerr**2)
            else:
                print("not valid error option")
                sys.exit(1)    
            if centralval:
                cflx=flux+(hisumerr-losumerr)*0.5
                calvals[E]=[cflx,(hisumerr+losumerr)*0.5,[E1,E2],nui]
            elif asymerr:
                calvals[E]=[flux,[losumerr,hisumerr],[E1,E2],nui]
            else:
                calvals[E]=[flux,(losumerr+hisumerr)*0.5,[E1,E2],nui]    
        else:
            if centralval:
                cflx=flux+(histaterr-lostaterr)*0.5
                calvals[E]=[cflx,(histaterr+lostaterr)*0.5,[E1,E2],nui]
            elif asymerr:
                calvals[E]=[flux,[lostaterr,histaterr],[E1,E2],nui]
            else:
                calvals[E]=[flux,(lostaterr+histaterr)*0.5,[E1,E2],nui]    

    #print (calvals)
    return calvals
    
def combocalYA22AMSvals(bp='../expdata/',systerr=True,asymerr=False,AMSprefact=-1):
    posvals=readamsposvalsnewest(basepath=bp,systerr=systerr,nuisancefit=False,energyerror=False)
    totvals=readcalYA2022flxvals(basepath=bp,systerr=systerr,centralval=False,asymerr=asymerr,DAMPEbin=False,AMSbin=True,nuisancefit=False,singleerr=False,nonormerr=False,BDT=13)
    sumvals={}
    #print(sorted(posvals.keys()))
    #print(sorted(totvals.keys()))
    for Ei,dat in posvals.items():
        for Ej in totvals.keys():
            if Ej>dat[2][0] and Ej<dat[2][1]:
                jdat=totvals[Ej]
                if asymerr:
                    toterr=[math.sqrt(jdat[1][0]**2+dat[1]**2),math.sqrt(jdat[1][1]**2+dat[1]**2)]
                else:
                    toterr=math.sqrt(jdat[1]**2+dat[1]**2)                                        
                sumvals[Ei]=[AMSprefact*dat[0]+jdat[0],toterr,dat[2],dat[3]]
                break
    return sumvals 
   
def combocalYA22bAMSvals(bp='../expdata/',systerr=True,asymerr=False,AMSprefact=-1):
    posvals=readamsposvalsnewest(basepath=bp,systerr=systerr,nuisancefit=False,energyerror=False)
    totvals=readcalYA2022bflxvals(basepath=bp,systerr=systerr,centralval=False,asymerr=asymerr,DAMPEbin=False,AMSbin=True,nuisancefit=False,singleerr=False,nonormerr=False,BDT=13)
    sumvals={}
    #print(sorted(posvals.keys()))
    #print(sorted(totvals.keys()))
    for Ei,dat in posvals.items():
        for Ej in totvals.keys():
            if Ej>dat[2][0] and Ej<dat[2][1]:
                jdat=totvals[Ej]
                if asymerr:
                    toterr=[math.sqrt(jdat[1][0]**2+dat[1]**2),math.sqrt(jdat[1][1]**2+dat[1]**2)]
                else:
                    toterr=math.sqrt(jdat[1]**2+dat[1]**2)                                        
                sumvals[Ei]=[AMSprefact*dat[0]+jdat[0],toterr,dat[2],dat[3]]
                break
    return sumvals 

def mergeYA2023AMS2021(basepath='../',systerr=True,centralval=False,asymerr=False,finebin=False,DAMPEbin=False,nuisancefit=False,singleerr=False,nonormerr=False,onesidesysterr=False,manualsyserr=False,BDT=13,staterrfact=1,Eindx=False,switchE=10.5,overlap=False):
    caldata=readcalYA2023flxvals(basepath=basepath,systerr=systerr,centralval=centralval,asymerr=asymerr,finebin=finebin,DAMPEbin=DAMPEbin,nuisancefit=nuisancefit,singleerr=singleerr,nonormerr=nonormerr,onesidesysterr=onesidesysterr,manualsyserr=manualsyserr,BDT=13,staterrfact=1)
    amsdata=readams2021totflxvals(basepath=basepath,systerr=systerr,Eindx=Eindx)
    mergevals={}
    for E in caldata.keys():
        if E<switchE and not overlap:
            continue
        mergevals[E]=caldata[E]
    if nuisancefit:
        nui=(0.0,0.0,0.0,0.0,0.0)
    else:
        nui=False
    for E in amsdata.keys():
        if E>switchE and not overlap:
            continue
        mergevals[E]=[amsdata[E][0],amsdata[E][1],amsdata[E][2],nui]
    return mergevals    
        
        
            
        

def readDAMPEflxvals(basepath='../',systerr=True):
    damfile=open(basepath+'sumdata/DAMPE.dat','r')
    damvals={}
    while True:
        stringline = damfile.readline()
        if stringline=='':
            break
        elif stringline[0]=="#":
            continue
        stringlist=stringline.split()        
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))    
        E=float(stringlist.pop(0))
        Eerr=float(stringlist.pop(0))    
        accept=float(stringlist.pop(0))    
        accepterr=float(stringlist.pop(0))
        N=float(stringlist.pop(0))
        bkgfrac=float(stringlist.pop(0))*0.01
        bkgfracerr=float(stringlist.pop(0))*0.01    
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        syserr=float(stringlist.pop(0))
        index=float(stringlist.pop(0))
        flux=flux*(10.0**(-index))/10000.0
        staterr=staterr*(10.0**(-index))/10000.0
        syserr=syserr*(10.0**(-index))/10000.0
        #print(E,flux*E**3,index)
        if systerr:
            damvals[E]=[flux,math.sqrt(staterr**2+syserr**2),[E1,E2],0]
        else:
            damvals[E]=[flux,staterr,[E1,E2],0]

    
    return damvals

def readts93vals(basepath='../'):
    tsfile=open(basepath+'fractdata/TS93.dat','r')
    tsvals={}
    while True:
        stringline = tsfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        binsize=E2-E1
        fract=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        tsvals[E]=[fract,staterr,[E1,E2]]
    return tsvals

def readcaprice94vals(basepath='../'):
    capfile=open(basepath+'fractdata/caprice94.dat','r')
    capvals={}
    while True:
        stringline = capfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        binsize=E2-E1
        fract=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        capvals[E]=[fract,staterr,[E1,E2]]
    return capvals

def readcaprice98vals(basepath='../'):
    capfile=open(basepath+'fractdata/caprice98.dat','r')
    capvals={}
    while True:
        stringline = capfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        binsize=E2-E1
        fract=float(stringlist.pop(0))
        staterrl=float(stringlist.pop(0))
        staterrh=float(stringlist.pop(0))
        staterr=(staterrl+staterrh)/2.0
        capvals[E]=[fract,staterr,[E1,E2]]
    return capvals

def readamsvals(basepath='../'):
    #return readamsvalsall("fract",basepath)
    return readamsfractnew(basepath)    

def readamsflxvals(basepath='../'):
    return readamsvalsall("sum",basepath)

def readtotflxvals(basepath='../'):
    return readamsvalsall("sum",basepath)

def readamselevals(basepath='../'):
    return readamsvalsall("ele",basepath)

def readamsposvals(basepath='../'):
    return readamsvalsall("pos",basepath)

def readams2021totflxvals(basepath='../',systerr=True,Eindx=False):
    amsfile=open(basepath+'sumdata/AMS2021PR.dat','r')
    AMSvals={}
    while True:
        stringline = amsfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        E=float(stringlist.pop(0))
        Eerr=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))/10000.0
        staterr=float(stringlist.pop(0))/10000.0
        syserr=float(stringlist.pop(0))/10000.0
        expo=int(stringlist.pop(0))
        sumflx=flux*pow(10,expo)
        if Eindx:
            effEerr=flux*(Eerr/E)*(Eindx-1.0)
        else:
            effEerr=0.0
        if systerr:
            sumerr=math.sqrt(staterr*staterr+syserr*syserr+effEerr*effEerr)*pow(10,expo)
        else:
            sumerr=math.sqrt(staterr*staterr+effEerr*effEerr)*pow(10,expo)
        AMSvals[E]=[sumflx,[sumerr,sumerr],[E1,E2],0]
    return AMSvals

def readamsvalsall(mode,basepath='../'):
    amsfile=open(basepath+'sumdata/AMS.dat','r')
    AMSvals={}
    while True:
        stringline = amsfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        E=float(stringlist.pop(0))
        Eerr=float(stringlist.pop(0))
        eflux=float(stringlist.pop(0))/10000.0
        estaterr=float(stringlist.pop(0))/10000.0
        esyserr=float(stringlist.pop(0))/10000.0
        eexpo=int(stringlist.pop(0))
        pflux=float(stringlist.pop(0))/10000.0
        pstaterr=float(stringlist.pop(0))/10000.0
        psyserr=float(stringlist.pop(0))/10000.0
        pexpo=int(stringlist.pop(0))
        eleflx=eflux*pow(10,eexpo)
        eleerr=math.sqrt(estaterr*estaterr+esyserr*esyserr)*pow(10,eexpo)
        poserr=math.sqrt(pstaterr*pstaterr+psyserr*psyserr)*pow(10,pexpo)
        posflx=pflux*pow(10,pexpo)
        sumflx=eleflx+posflx
        sumerr=math.sqrt(eleerr*eleerr+poserr*poserr)
        fract=pflux*pow(10,pexpo)/sumflx
        fracterr=(poserr/posflx)+(sumerr/sumflx)
        binsize=E2-E1
        if mode=="fract":
            AMSvals[E]=[fract,fracterr,[E1,E2],0]
        elif mode=="sum":
            AMSvals[E]=[sumflx,sumerr,[E1,E2],0]
        elif mode=="ele":
            AMSvals[E]=[eleflx,eleerr,[E1,E2],0]
        elif mode=="pos":
            AMSvals[E]=[posflx,poserr,[E1,E2],0]
    return AMSvals



def readamsfractnew(basepath='../'):
    amsfile=open(basepath+'fractdata/AMSfract.dat','r')
    AMSvals={}
    while True:
        stringline = amsfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        N=int(stringlist.pop(0))
        fract=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        accerr=float(stringlist.pop(0))
        selerr=float(stringlist.pop(0))
        migerr=float(stringlist.pop(0))
        referr=float(stringlist.pop(0))
        ccerr=float(stringlist.pop(0))
        systerr=float(stringlist.pop(0))
        E = math.sqrt(E1*E2)
        binsize=E2-E1
        toterr=math.sqrt(staterr*staterr+systerr*systerr)
        AMSvals[E]=[fract,staterr,[E1,E2],N]
    return AMSvals



def readamsvalsfuture(basepath='../'):
    amsfile=open(basepath+'fractdata/AMSfract.dat','r')
    AMSvals={}
    while True:
        stringline = amsfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        N=int(stringlist.pop(0))
        fract=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        accerr=float(stringlist.pop(0))
        selerr=float(stringlist.pop(0))
        migerr=float(stringlist.pop(0))
        referr=float(stringlist.pop(0))
        ccerr=float(stringlist.pop(0))
        systerr=float(stringlist.pop(0))
        E = math.sqrt(E1*E2)
        binsize=E2-E1
        staterr=staterr*0.5 #projected data for 2021 = 4*2015 data -> half error
        toterr=math.sqrt(staterr*staterr+systerr*systerr)
        AMSvals[E]=[fract,staterr,[E1,E2],N]
    return AMSvals

def readamsfractold(basepath='../'):
    amsfile=open(basepath+'fractdata/ams02.dat','r')
    AMSvals={}
    while True:
        stringline = amsfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))
        dash=stringlist.pop(0)
        E2=float(stringlist.pop(0))
        N=int(stringlist.pop(0))
        fract=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        E = math.sqrt(E1*E2)
        binsize=E2-E1
        AMSvals[E]=[fract,staterr,[E1,E2],N]
    return AMSvals

def readamsposvalsold(basepath='../'):
    amsfile=open(basepath+'posdata/AMSpositron.dat','r')
    AMSvals={}
    while True:
        stringline = amsfile.readline()
        if stringline=='' or stringline=='\n':
            break
        if stringline[0]=='#':
            continue
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))
        flux=E**(-3.0)*flux/10000.0
        AMSvals[E]=[flux,0,[E,E],0]
    return AMSvals


def readamsposvalsnewest(basepath='../',systerr=True,nuisancefit=False,energyerror=False):
    amsfile=open(basepath+'posdata/AMSnewestpositron.dat','r')
    AMSvals={}
    Eindx=[]
    indxE=[]
    if energyerror:
        indexfile=open(basepath+'posdata/AMSpositronindex.dat','r')
        while True:
            stringline = indexfile.readline()
            if stringline=='' or stringline=='\n':
                break
            stringlist=stringline.split()
            iE=float(stringlist.pop(0))
            indx=float(stringlist.pop(0))
            indxE.append(iE)
            Eindx.append(abs(indx))    
    
    while True:
        stringline = amsfile.readline()
        if stringline=='' or stringline=='\n':
            break
        if stringline[0]=='#':
            continue
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        E=float(stringlist.pop(0))
        Eerr=float(stringlist.pop(0))
        N=float(stringlist.pop(0))
        Nerr=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        tmplerr=float(stringlist.pop(0))
        ccerr=float(stringlist.pop(0))
        efferr=float(stringlist.pop(0))
        unferr=float(stringlist.pop(0))
        systerr=float(stringlist.pop(0))
        ten=int(stringlist.pop(0))
        exponent=int(stringlist.pop(0))
        if len(indxE)>0:
            useindx=False
            for j in range(len(indxE)):
                if indxE[j]>E:
                    x1=indxE[j-1]
                    x2=indxE[j]
                    y1=Eindx[j-1]
                    y2=Eindx[j]
                    f=(E-x1)/(x2-x1)
                    useindx=pow(y1,1.0-f)*pow(y2,f)
                    break
            if not useindx:
                useindx=Eindx[-1]
            effEerr=flux*(Eerr/E)*(useindx-1.0)
        if systerr:
            if energyerror:
                err=math.sqrt(staterr*staterr+systerr*systerr+effEerr*effEerr)
            else:
                err=math.sqrt(staterr*staterr+systerr*systerr)
        else:
            err=staterr
        flux=flux*pow(10.0,exponent)/10000.0
        err=err*pow(10.0,exponent)/10000.0
        AMSvals[E]=[flux,err,[E1,E2],0]
    return AMSvals

def readamselevalsnewest(basepath='../',systerr=True,nuisancefit=False,energyerror=False):
    amsfile=open(basepath+'eledata/AMSnewestelectron.dat','r')
    AMSvals={}
    Eindx=[]
    indxE=[]
    if energyerror:
        indexfile=open(basepath+'eledata/AMSelectronindex.dat','r')
        while True:
            stringline = indexfile.readline()
            if stringline=='' or stringline=='\n':
                break
            stringlist=stringline.split()
            iE=float(stringlist.pop(0))
            indx=float(stringlist.pop(0))
            indxE.append(iE)
            Eindx.append(abs(indx))    
    
    while True:
        stringline = amsfile.readline()
        if stringline=='' or stringline=='\n':
            break
        if stringline[0]=='#':
            continue
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        E=float(stringlist.pop(0))
        Eerr=float(stringlist.pop(0))
        N=float(stringlist.pop(0))
        Nerr=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        systerr=float(stringlist.pop(0))
        ten=int(stringlist.pop(0))
        exponent=int(stringlist.pop(0))
        if len(indxE)>0:
            useindx=False
            for j in range(len(indxE)):
                if indxE[j]>E:
                    x1=indxE[j-1]
                    x2=indxE[j]
                    y1=Eindx[j-1]
                    y2=Eindx[j]
                    f=(E-x1)/(x2-x1)
                    useindx=pow(y1,1.0-f)*pow(y2,f)
                    break
            if not useindx:
                useindx=Eindx[-1]
            effEerr=flux*(Eerr/E)*(useindx-1.0)
        if systerr:
            if energyerror:
                err=math.sqrt(staterr*staterr+systerr*systerr+effEerr*effEerr)
            else:
                err=math.sqrt(staterr*staterr+systerr*systerr)
        else:
            err=staterr
        flux=flux*pow(10.0,exponent)/10000.0
        err=err*pow(10.0,exponent)/10000.0
        AMSvals[E]=[flux,err,[E1,E2],0]
    return AMSvals


def readamstotvalsnewest(basepath='../',systerr=True):
    amsfile=open(basepath+'sumdata/AMSnewestsum.dat','r')
    AMSvals={}
    Eindx=[]
    indxE=[]
    while True:
        stringline = amsfile.readline()
        if stringline=='' or stringline=='\n':
            break
        if stringline[0]=='#':
            continue
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        E=math.sqrt(E1*E2)
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        systerr=float(stringlist.pop(0))
        ten=int(stringlist.pop(0))
        exponent=int(stringlist.pop(0))
        if systerr:
            err=math.sqrt(staterr*staterr+systerr*systerr)
        else:
            err=staterr
        flux=flux*pow(10.0,exponent)/10000.0
        err=err*pow(10.0,exponent)/10000.0
        AMSvals[E]=[flux,err,[E1,E2],0]
    return AMSvals

def readamsposvalsnew(basepath='../'):
    amsfile=open(basepath+'posdata/AMSnewpositron.dat','r')
    AMSvals={}
    while True:
        stringline = amsfile.readline()
        if stringline=='' or stringline=='\n':
            break
        if stringline[0]=='#':
            continue
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))
        uperr=float(stringlist.pop(0))
        err=uperr-flux
        flux=E**(-3.0)*flux/10000.0
        err=E**(-3.0)*err/10000.0
        AMSvals[E]=[flux,err,[E,E],0]
    return AMSvals


def readamselevalsold(basepath='../'):
    amsfile=open(basepath+'eledata/AMSelectron.dat','r')
    AMSvals={}
    while True:
        stringline = amsfile.readline()
        if stringline=='' or stringline=='\n':
            break
        if stringline[0]=='#':
            continue
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))
        flux=E**(-3.0)*flux/10000.0
        AMSvals[E]=[flux,0,[E,E],0]
    return AMSvals

def readamsvals_old(basepath='../'):
    amsfile=open(basepath+'fractdata/ams02.dat','r')
    AMSvals={}
    while True:
        stringline = amsfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))
        dash=stringlist.pop(0)
        E2=float(stringlist.pop(0))
        N=int(stringlist.pop(0))
        fract=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        syserr=float(stringlist.pop(-1))
        toterr=math.sqrt(staterr*staterr+syserr*syserr)
        E = math.sqrt(E1*E2)
        binsize=E2-E1
        AMSvals[E]=[fract,toterr,[E1,E2],N]
    return AMSvals

def readpamela0vals(basepath='../'):
    pamfile=open(basepath+'fractdata/pamela0.dat','r')
    pamvals={}
    while True:
        stringline = pamfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        E=float(stringlist.pop(0))
        fract=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        binsize=E2-E1
        pamvals[E]=[fract,staterr,[E1,E2],0]
    return pamvals

def readfermi0vals(basepath='../'):
    fermifile=open(basepath+'fractdata/fermi0.dat','r')
    FERMIvals={}
    while True:
        stringline = fermifile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        frac=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        errh=float(stringlist.pop(0))
        errl=float(stringlist.pop(0))
        #staterr=max((errh+errl)/2.0,staterr)
        E = math.sqrt(E1*E2);
        binsize=E2-E1
        FERMIvals[E]=[frac,staterr,[E1,E2],0]
    return FERMIvals

def readfermivals(basepath='../'):
    fermifile=open(basepath+'sumdata/Fermi.dat','r')
    FERMIvals={}
    while True:
        stringline = fermifile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        n=float(stringlist.pop(-1))
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        N=int(stringlist.pop(0))
        cont=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        syserrh=float(stringlist.pop(0))
        syserrl=float(stringlist.pop(0))
        E = math.sqrt(E1*E2);
        upbound=flux+staterr+syserrh
        lowbound=flux-staterr-syserrl
        flux=(upbound+lowbound)/2.0
        flux = flux*math.pow(10,-n)/10000.0 # m^2 => cm^2
        toterr = ((upbound-lowbound)/2.0)*math.pow(10,-n)/10000.0
        binsize=E2-E1
        FERMIvals[E]=[flux,toterr,[E1,E2],0]
    return FERMIvals

#   <E>  Elo  Eup   y   ystat_lo  ystat_up  ysyst_lo  ysyst_up  yerrtot_lo  yerrtot_up

def readhessvals(basepath='../'):
    hessfile=open(basepath+'sumdata/Hess.dat','r')
    HESSvals={}
    while True:
        stringline = fermifile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        toterrh=float(stringlist.pop(-1))
        toterrl=float(stringlist.pop(-1))
        flux=(toterrh+toterrl)/2.0
        toterr=(toterrh-toterrl)/2.0
        binsize=E2-E1
        HESSvals[E]=[flux,toterr,[E1,E2],0]
    return HESSvals


def readfermivals_old(basepath='../'):
    fermifile=open(basepath+'sumdata/Fermi.dat','r')
    FERMIvals={}
    while True:
        stringline = fermifile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        n=float(stringlist.pop(-1))
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        N=int(stringlist.pop(0))
        cont=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        E = math.sqrt(E1*E2);
        flux = flux*math.pow(10,-n)/10000.0 # m^2 => cm^2
        staterr = staterr*math.pow(10,-n)/10000.0
        binsize=E2-E1
        FERMIvals[E]=[flux,staterr,[E1,E2],0]
    return FERMIvals

def readpamelavals(basepath='../'):
    pamelafile=open(basepath+'sumdata/Pamela.dat','r')
    PAMELAvals={}
    while True:
        stringline = pamelafile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        n=float(stringlist.pop(-1))
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        E=float(stringlist.pop(0))
        N=int(stringlist.pop(0))
        flux=float(stringlist.pop(0))
        staterrm=float(stringlist.pop(0))
        staterrp=float(stringlist.pop(0))
        staterr=staterrm+staterrp
        flux = flux*math.pow(10,n)/10000.0 # m^2 => cm^2
        staterr = staterr*math.pow(10,n)/10000.0
        binsize=E2-E1
        PAMELAvals[E]=[flux,staterr,[E1,E2]]
    return PAMELAvals

def readpamelaSMvals(basepath='../'):
    pamelaSMfile=open(basepath+'sumdata/PamelaSM.dat','r')
    PAMELAvals={}
    while True:
        stringline = pamelaSMfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        E=(E1+E2)/2.0
        blocks=[]
        for i in range(4):
            B=stringlist.pop(0)
            if "X" in B:
                PB=B.partition("X")
                B=PB[0]
                ex=float(PB[2])
            else:
                ex=0.0    
            fler=B.split('P')
            flux=float(fler[0])*math.pow(10,ex)/10.0
            toterr=(float(fler[1])+float(fler[2]))*math.pow(10,ex)/10.0
            blocks.append([flux,toterr,[E1,E2]])
        PAMELAvals[E]=blocks
    return PAMELAvals

def readpamelaLISvals(basepath='../'):
    pamelaLISfile=open(basepath+'sumdata/PamelaLIS.dat','r')
    PAMELAvals={}
    while True:
        stringline = pamelaLISfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))
        flux = flux/10000.0 # m^2 => cm^2
        flux=flux*1000.0 # per MEV => per GEV
        PAMELAvals[E]=[flux,False,False]
    return PAMELAvals



def readaticvals(basepath='../'):
    aticfile=open(basepath+'sumdata/Atic.dat','r')
    ATICvals={}
    while True:
        stringline = aticfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))
        staterrm=float(stringlist.pop(0))
        staterrp=float(stringlist.pop(0))
        #staterr=staterrm+staterrp
        staterr=math.sqrt(staterrm**2+staterrp**2)
        flux = flux/10000.0 # m^2 => cm^2
        staterr = staterr/10000.0
        binsize=E2-E1
        ATICvals[E]=[flux,staterr,[E1,E2]]
    return ATICvals

def readhessallvals(basepath='../'):
    hessfile=open(basepath+'sumdata/Hess.dat','r')
    HESSvals={}
    while True:
        stringline = hessfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        E1=float(stringlist.pop(0)) # ! dummy 
        E2=float(stringlist.pop(0)) # ! is 0 in file
        flux=float(stringlist.pop(0))
        toterrh=float(stringlist.pop(-1))
        toterrl=float(stringlist.pop(-1))
        flux=flux+toterrh-toterrl
        toterr=(toterrh+toterrl)/2.0
        flux=flux/10000.0
        toterr=toterr/10000.0
        HESSvals[E]=[flux,toterr,[E,E]]
    return HESSvals

def readhesslowEvals(basepath='../'):
    hessfile=open(basepath+'sumdata/Hess-lowE.dat','r')
    HESSvals={}
    while True:
        stringline = hessfile.readline()
        if stringline=='###\n':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))

        statlow=float(stringlist.pop(0))
        statup=float(stringlist.pop(0))
        staterr=(statup+statlow)/2.0
        E1=float(stringlist.pop(0)) 
        sysE1low=float(stringlist.pop(0))
        sysE1up=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        sysE2low=float(stringlist.pop(0))
        sysE2up=float(stringlist.pop(0))
        syslow=sysE1low+(sysE2low-sysE1low)*E/E2    
        sysup=sysE1up+(sysE2up-sysE1up)*E/E2        
        flux=(sysup+syslow)/2.0
        syserr=(sysup-syslow)/2.0
        toterr=(math.sqrt(syserr*syserr+staterr*staterr))
        flux=E**(-3.0)*flux/10000.0
        toterr=E**(-3.0)*toterr/10000.0
        HESSvals[E]=[flux,toterr,[E1,E2]]
    return HESSvals

def readhesslowEvals_old(basepath='../'):
    hessfile=open(basepath+'sumdata/Hess-lowE-old.dat','r')
    HESSvals={}
    while True:
        stringline = hessfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        E1=float(stringlist.pop(0)) # ! dummy 
        E2=float(stringlist.pop(0)) # ! is 0 in file
        flux=float(stringlist.pop(0))
        toterrh=float(stringlist.pop(-1))
        toterrl=float(stringlist.pop(-1))
        flux=flux+toterrh-toterrl
        toterr=(toterrh+toterrl)/2.0
        flux=flux/10000.0
        toterr=toterr/10000.0
        HESSvals[E]=[flux,toterr,[E,E]]
    return HESSvals

def readhessstdvals(basepath='../'):
    hessfile=open(basepath+'sumdata/Hess-std.dat','r')
    HESSvals={}
    while True:
        stringline = hessfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        E1=float(stringlist.pop(0)) # ! dummy 
        E2=float(stringlist.pop(0)) # ! is 0 in file
        flux=float(stringlist.pop(0))
        toterrh=float(stringlist.pop(-1))
        toterrl=float(stringlist.pop(-1))
        flux=flux+toterrh-toterrl
        toterr=(toterrh+toterrl)/2.0
        flux=flux/10000.0
        toterr=toterr/10000.0
        HESSvals[E]=[flux,toterr,[E,E]]
    return HESSvals

def readhessnewvals(basepath='../'):
    hessfile=open(basepath+'sumdata/HESSelectron2017.dat','r')
    HESSvals={}
    while True:
        stringline = hessfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))
        if len(stringlist)>0:
            toterrh=float(stringlist.pop(0))-flux
        else:
            toterrh=0.0
        if len(stringlist)>0:
            toterrl=flux-float(stringlist.pop(0))
        else:
            toterrl=0.0
        
        flux=flux/10000.0*E**-3
        toterrl=toterrl/10000.0*E**-3
        toterrh=toterrh/10000.0*E**-3
        HESSvals[E]=[flux,[toterrl,toterrh],[E,E]]
    return HESSvals


def readhesssysvals(basepath='../'):
    hessfile=open(basepath+'sumdata/HESSelectron2017syserr.dat','r')
    HESSvalsx=[]
    HESSvalsy=[]
    while True:
        stringline = hessfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))
        flux=flux/10000.0
        HESSvalsx.append(E)
        HESSvalsy.append(flux)
    return (HESSvalsx,HESSvalsy)

def readhess2024vals_tnaru(basepath='../'):
    hessfile=open(basepath+'sumdata/HESSelectron2024.dat','r')
    HESSvals={}
    while True:
        stringline = hessfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))
        if len(stringlist)>0:
            toterrh=float(stringlist.pop(0))-flux
        else:
            toterrh=0.0
        if len(stringlist)>0:
            toterrl=flux-float(stringlist.pop(0))
        else:
            toterrl=0.0
        
        flux=flux/10000.0*E**-3
        toterrl=toterrl/10000.0*E**-3
        toterrh=toterrh/10000.0*E**-3
        HESSvals[E]=[flux,[toterrl,toterrh],[E,E]]
    return HESSvals
    
def readhess2024vals(basepath='../'):
    hessfile=open(basepath+'sumdata/HESSelectron2024_wlim.dat','r')
    HESSvals={}
    while True:
        stringline = hessfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))*1e3
        fluxv=float(stringlist.pop(0))
        fluxe=float(stringlist.pop(0))
        flux=fluxv*10**fluxe
                
        if len(stringlist)>0:
            lfluxv=float(stringlist.pop(0))
            lfluxe=float(stringlist.pop(0))
            lflux=lfluxv*10**lfluxe
            lerr=flux-lflux
        else:
            lerr=flux*0.5
        if len(stringlist)>0:
            hfluxv=float(stringlist.pop(0))
            hfluxe=float(stringlist.pop(0))
            hflux=hfluxv*10**hfluxe
            herr=hflux-flux
        else:
            herr=0.0
        corr=1e7
        flux=flux/corr
        lerr=lerr/corr
        herr=herr/corr
        HESSvals[E]=[flux,[lerr,herr],[E,E]]
    return HESSvals
    
def readhess2024err20vals(basepath='../'):
    hessfile=open(basepath+'sumdata/HESSelectron2024errbar20.dat','r')
    HESSvals={}
    while True:
        stringline = hessfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))
        if len(stringlist)>0:
            toterrh=float(stringlist.pop(0))-flux
        else:
            toterrh=0.0
        if len(stringlist)>0:
            toterrl=flux-float(stringlist.pop(0))
        else:
            toterrl=0.0
        
        flux=flux/10000.0*E**-3
        toterrl=toterrl/10000.0*E**-3
        toterrh=toterrh/10000.0*E**-3
        HESSvals[E]=[flux,[toterrl,toterrh],[E,E]]
    return HESSvals
    
def readhess24sysvals(basepath='../'):
    hessfile=open(basepath+'sumdata/HESSelectron2024syserr.dat','r')
    HESSvalsx=[]
    HESSvalsy=[]
    while True:
        stringline = hessfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))
        flux=flux/10000.0
        HESSvalsx.append(E)
        HESSvalsy.append(flux)
    return (HESSvalsx,HESSvalsy)
    
def readhess24uncervals(basepath='../'):
    hessfile=open(basepath+'sumdata/HESSelectron2024uncer.dat','r')
    HESSvalsx=[]
    HESSvalsy=[]
    while True:
        stringline = hessfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))
        flux=flux/10000.0
        HESSvalsx.append(E)
        HESSvalsy.append(flux)
    return (HESSvalsx,HESSvalsy)
    
def readhess24sysbluevals(basepath='../'):
    hessfile=open(basepath+'sumdata/HESSelectron2024sysblue.dat','r')
    HESSvalsx=[]
    HESSvalsy=[]
    while True:
        stringline = hessfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))
        flux=flux/10000.0
        HESSvalsx.append(E)
        HESSvalsy.append(flux)
    return (HESSvalsx,HESSvalsy)

def readhess24sys20vals(basepath='../'):
    hessfile=open(basepath+'sumdata/HESSelectron2024sys20%.dat','r')
    HESSvalsx=[]
    HESSvalsy=[]
    while True:
        stringline = hessfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))
        flux=flux/10000.0
        HESSvalsx.append(E)
        HESSvalsy.append(flux)
    return (HESSvalsx,HESSvalsy)
    
def readhess24sigma2upp(basepath='../'):
    hessfile=open(basepath+'sumdata/HESSelectron2024sigma2upp.dat','r')
    HESSvalsx=[]
    HESSvalsy=[]
    while True:
        stringline = hessfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))
        flux=flux/10000.0
        HESSvalsx.append(E)
        HESSvalsy.append(flux)
    return (HESSvalsx,HESSvalsy)    
    
def readhess24sigma2low(basepath='../'):
    hessfile=open(basepath+'sumdata/HESSelectron2024sigma2low.dat','r')
    HESSvalsx=[]
    HESSvalsy=[]
    while True:
        stringline = hessfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))
        flux=flux/10000.0
        HESSvalsx.append(E)
        HESSvalsy.append(flux)
    return (HESSvalsx,HESSvalsy)        
    
    

def readhesssysvals(basepath='../'):
    hessfile=open(basepath+'sumdata/HESSelectron2017syserr.dat','r')
    HESSvalsx=[]
    HESSvalsy=[]
    while True:
        stringline = hessfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))
        flux=flux/10000.0
        HESSvalsx.append(E)
        HESSvalsy.append(flux)
    return (HESSvalsx,HESSvalsy)


def readVeritasvals(basepath='../'):
    Veritasfile=open(basepath+'sumdata/Veritas.dat','r')
    Veritasvals={}
    FOV=0.45*math.pi*(3.5*math.pi/180.0/2.0)**2
    while True:
        stringline = Veritasfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))*1000.0
        E1=float(stringlist.pop(0))*1000.0 
        E2=float(stringlist.pop(0))*1000.0 
        N=float(stringlist.pop(0)) 
        elefrac=float(stringlist.pop(0)) 
        efracerr=float(stringlist.pop(0)) 
        fluxbase=float(stringlist.pop(0))
        fluxexp=float(stringlist.pop(0))
        errbase=float(stringlist.pop(0))
        errexp=float(stringlist.pop(0))
        flux=fluxbase*pow(10,fluxexp)*1e3*FOV
        err=errbase*pow(10,errexp)*1e3*FOV
        Veritasvals[E]=[flux,err,[E1,E2]]
    return Veritasvals


def readamsprelimvals(basepath='../'):
    amsfile=open(basepath+'sumdata/AMS-murata.dat','r')
    AMSvals={}
    while True:
        stringline = amsfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        dE=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        flux = flux/10000.0/E**(3.0) # m^2 => cm^2
        staterr = staterr/10000.0/E**(3.0)
        if staterr==0.0:
            continue
        AMSvals[E]=[flux,staterr,[E,E]]
    return AMSvals

def readppbvals(basepath='../'):
    ppbfile=open(basepath+'sumdata/PPB.dat','r')
    PPBvals={}
    while True:
        stringline = ppbfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        flux = flux/10000.0 # m^2 => cm^2
        staterr = staterr/10000.0
        binsize=0.0
        PPBvals[E]=[flux,staterr,[E,E]]
    return PPBvals

def readcalsimvals(basepath='../'):
    calfile=open(basepath+'sumdata/caletsample07.dat','r')
    CALvals={}
    while True:
        stringline = calfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        binsize=0.0
        CALvals[E]=[flux,staterr,[E,E]]
    return CALvals

def readcalWinoDecayvals(basepath='../'):
    calfile=open(basepath+'sumdata/caletWinoDecaysample.dat','r')
    CALvals={}
    while True:
        stringline = calfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        binsize=0.0
        CALvals[E]=[flux,staterr,[E,E]]
    return CALvals

#----------------------- SIMULATION -----------------------------------------------

def readDragonOutput(dragonfilename,dragonoutpath='/home/ljiayi/outputs/'):
    dragonfile=open(dragonoutpath+dragonfilename,'r')
    Dragonvals={}     
    stringline = dragonfile.readline()
    while True:
        stringline = dragonfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        secpos=float(stringlist.pop(0))
        priele=float(stringlist.pop(0))
        secele=float(stringlist.pop(0))
        extpos=float(stringlist.pop(0))
        terapr=float(stringlist.pop(0))
        secapr=float(stringlist.pop(0))
        secpro=float(stringlist.pop(0))
        pripro=float(stringlist.pop(0))
        totpos=(secpos+extpos)/10000.0
        totele=(priele+secele+extpos)/10000.0    
        bkgpos=(secpos)/10000.0
        bkgele=(priele+secele)/10000.0    
        totapr=(terapr+secapr)/10000.0    
        totpro=(pripro+secpro)/10000.0    
        bkgapr=(terapr+secapr)/10000.0
        bkgpro=(pripro+secpro)/10000.0    
        Dragonvals[E]=[totpos,totele,bkgpos,bkgele,totapr,totpro,False,False,bkgapr,bkgpro]
    dragonfile.close()
    return Dragonvals

def readDragonDMOut(dragonfilename,dragonoutpath='/nfs/RAID/home/motz/dragon-3.0.1/output/'):
    dragonfile=open(dragonoutpath+dragonfilename,'r')
    Dragonvals={}     
    stringline = dragonfile.readline()
    while True:
        stringline = dragonfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        secpos=float(stringlist.pop(0))
        DMele=float(stringlist.pop(0))
        priele=float(stringlist.pop(0))
        secele=float(stringlist.pop(0))
        stringlist.pop(0)
        DMapr=float(stringlist.pop(0))
        terapr=float(stringlist.pop(0))
        secapr=float(stringlist.pop(0))
        secpro=float(stringlist.pop(0))
        pripro=float(stringlist.pop(0))
        totpos=(secpos+DMele)/10000.0
        totele=(priele+secele+DMele)/10000.0    
        bkgpos=(secpos)/10000.0
        bkgele=(priele+secele)/10000.0    
        totapr=(terapr+secapr+DMapr)/10000.0
        totpro=(pripro+secpro+DMapr)/10000.0    
        bkgapr=(terapr+secapr)/10000.0
        bkgpro=(pripro+secpro)/10000.0    
        DMpos=DMele/10000.0
        DMele=DMele/10000.0
        Dragonvals[E]=[totpos,totele,bkgpos,bkgele,totapr,totpro,DMpos,DMele,bkgapr,bkgpro]
    dragonfile.close()
    return Dragonvals

def readDragonDMOutLite(dragonfilename,dragonoutpath='/nfs/RAID/home/motz/dragon-3.0.1/output/'):
    dragonfile=open(dragonoutpath+dragonfilename,'r')
    Dragonvals={}     
    stringline = dragonfile.readline()
    while True:
        stringline = dragonfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        DMpos=float(stringlist.pop(0))
        DMpos=DMpos/10000.0
        Dragonvals[E]=[DMpos]
    dragonfile.close()
    return Dragonvals

def readGalpropOut(galpropfilename,galpropoutpath='/nfs/RAID/home/motz/galprop2/fits/'):
    galpropfile=open(galpropoutpath+galpropfilename,'r')
    GPRPvals={}     
    while True:
        stringline = galpropfile.readline()
        if stringline=='':
            break
        elif stringline[0]=='n':
            continue
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        F=float(stringlist.pop(0))
        F=F*pow(E,-2.0)*1000.0
        E=E/1000.0
        if E in GPRPvals.keys():
            GPRPvals[E].append(F)
        else:
            GPRPvals[E]=[F]
    galpropfile.close()
    return GPRPvals

#nuleus no. 1 - n = 1 Z = 1 A = 0 K = 0     secondary positron
#nuleus no. 2 - n = 2 Z = -1 A = 0 K = 0     secondary electron
#nuleus no. 3 - n = 3 Z = -1 A = 0 K = 0     primary electron
#nuleus no. 4 - n = 4 Z = -1 A = 1 K = 0     tertiary antiproton
#nuleus no. 5 - n = 5 Z = -1 A = 1 K = 0     secondary antiproton
#nuleus no. 6 - n = 6 Z = 1 A = 1 K = 0     secondary proton
#nuleus no. 7 - n = 7 Z = 1 A = 1 K = 0     primary proton
#nuleus no. 8 - n = 8 Z = 1 A = 2 K = 0     deuterons (all zero)


#----------------- PROTON ---------------------------------------------

def readpamelaprovals(basepath='../'):
    pamelafile=open(basepath+'nucdata/protonpamela.dat','r')
    pamelavals={}
    while True:
         stringline=pamelafile.readline()
         if stringline=='':
             break
         stringlist=stringline.split()
         E1=float(stringlist.pop(0))
         E2=float(stringlist.pop(0))
         E=float(stringlist.pop(0))
         flux=float(stringlist.pop(0))
         staterr=float(stringlist.pop(0))
         syserr=float(stringlist.pop(0))
         if len(stringlist) > 0 :
            index = float(stringlist.pop(0))
            flux=flux*(10**(-index))
            staterr=staterr*(10**(-index))    
         binsize=E2-E1
         pamelavals[E]=[flux/10000.0,staterr/10000.0,binsize]
    return pamelavals 

def readpamelaaprvals(basepath='../'):
    pamelafile=open(basepath+'nucdata/apfracpamela.dat','r')
    pamelavals={}
    while True:
         stringline=pamelafile.readline()
         if stringline=='':
             break
         stringlist=stringline.split()
         E1=float(stringlist.pop(0))
         E2=float(stringlist.pop(0))
         E=float(stringlist.pop(0))
         nap=int(stringlist.pop(0))
         npr=int(stringlist.pop(0))
         frac=float(stringlist.pop(0))
         staterr=float(stringlist.pop(0))
         if len(stringlist) > 0 :
            index = float(stringlist.pop(0))
            frac=frac*(10**(-index))
            staterr=staterr*(10**(-index))    
         binsize=E2-E1
         pamelavals[E]=[frac,staterr,binsize]
    return pamelavals 


def readamsproflxvals(basepath='../',convtoE=True):
    amsfile=open(basepath+'nucdata/protonAMS02-2015.dat','r')
    AMSvals={}
    while True:
        stringline = amsfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        R1=float(stringlist.pop(0))
        R2=float(stringlist.pop(0))
        R= math.sqrt(R1*R2)
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        trigerr=float(stringlist.pop(0))
        accerr=float(stringlist.pop(0))
        unferr=float(stringlist.pop(0))
        scalerr=float(stringlist.pop(0))
        syserr=float(stringlist.pop(0))
        expo=int(stringlist.pop(0))
        sumflx=flux*pow(10,expo)/10000.0
        eflx,En1=RtoE(sumflx,R1,"p")
        eflx,En2=RtoE(sumflx,R2,"p")
        eflx,En=RtoE(sumflx,R,"p")
        sumerr=math.sqrt(staterr*staterr+syserr*syserr)*pow(10,expo)/10000.0
        eerrup,En=RtoE(flux+sumerr,R,"p")
        eerrdown,En=RtoE(flux-sumerr,R,"p")
        eerrup=eerrup-eflx
        eerrdown=-(eerrdown-eflx)
        eerr=0.5*(eerrup+eerrdown)
        if convtoE:
            AMSvals[En]=[eflx,eerr,[En1,En2],0]
        else:
            AMSvals[R]=[sumflx,sumerr,[R1,R2],0]
    return AMSvals


def readcalproflxvals(basepath='../',convtoR=False):
    calfile=open(basepath+'nucdata/protonCALET2019.dat','r')
    calvals={}
    while True:
        stringline = calfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        E=float(stringlist.pop(0))
        Eerrscale=float(stringlist.pop(0))
        Eerrsyst=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        scalerr=float(stringlist.pop(0))
        syserrup=float(stringlist.pop(0))
        syserrdown=float(stringlist.pop(0))
        syserr=(syserrup+syserrdown)*0.5
        expo=-int(stringlist.pop(0))
        sumflx=flux*pow(10,expo)/10000.0
        rflx,R1=EtoR(sumflx,E1,"p")
        rflx,R2=EtoR(sumflx,E2,"p")
        rflx,R=EtoR(sumflx,E,"p")
        sumerr=math.sqrt(staterr*staterr+scalerr*scalerr+syserr*syserr)*pow(10,expo)/10000.0
        rerrup,R=EtoR(sumflx+sumerr,E,"p")
        rerrdown,R=EtoR(sumflx-sumerr,E,"p")
        rerrup=rerrup-rflx
        rerrdown=-(rerrdown-rflx)
        rerr=0.5*(rerrup+rerrdown)
        if convtoR:
            calvals[R]=[rflx,rerr,[R1,R2],0]
        else:
            calvals[E]=[sumflx,sumerr,[E1,E2],0]
    return calvals
    

def readcal2021proflxvals(basepath='../',convtoR=False):
    calfile=open(basepath+'nucdata/protoncalet2021.dat','r')
    calvals={}
    while True:
        stringline = calfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))/10000.0/pow(E,2.7)
        Eerrlo=float(stringlist.pop(0))
        Eerrup=float(stringlist.pop(0))       
        staterrlo=float(stringlist.pop(0))/10000.0/pow(E,2.7)
        staterrup=float(stringlist.pop(0))/10000.0/pow(E,2.7)
        toterrlo=float(stringlist.pop(0))/10000.0/pow(E,2.7)
        toterrup=float(stringlist.pop(0))/10000.0/pow(E,2.7)
        E1=E-Eerrlo
        E2=E+Eerrup
        rflx,R1=EtoR(flux,E1,"p")
        rflx,R2=EtoR(flux,E2,"p")
        rflx,R=EtoR(flux,E,"p")
        rerrup,R=EtoR(flux+toterrup,E,"p")
        rerrlo,R=EtoR(flux-toterrlo,E,"p")
        rerrup=rerrup-rflx
        rerrlo=-(rerrlo-rflx)
        rerr=0.5*(rerrup+rerrlo)
        if convtoR:
            calvals[R]=[rflx,rerr,[R1,R2],0]
        else:
            calvals[E]=[flux,[toterrlo,toterrup],[E1,E2],0]
    return calvals    
    
def readcal2022proflxvals(basepath='../'):
    calfile=open(basepath+'nucdata/protoncalet2022.dat','r')
    calvals={}
    while True:
        stringline = calfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        Eb1=float(stringlist.pop(0))
        Eb2=float(stringlist.pop(0))
        Ebi=float(stringlist.pop(0))
        E1=Eb1*10**Ebi
        E2=Eb2*10**Ebi
        Er=float(stringlist.pop(0))
        Er1=float(stringlist.pop(0))
        Er2=float(stringlist.pop(0))
        Eri=float(stringlist.pop(0))
        E=Er*10**Eri
        
        Eerrlo=Er1*10**Eri
        Eerrhi=Er2*10**Eri
        
        rflux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        normerr=float(stringlist.pop(0))
        edeperrup=float(stringlist.pop(0))
        edeperrlo=float(stringlist.pop(0))
        flxindx=float(stringlist.pop(0))
        flux=rflux*10**(-flxindx)/10000.0
        
        toterrlo=math.sqrt(staterr*staterr+normerr*normerr+edeperrlo*edeperrlo)*10**(-flxindx)/10000.0
        toterrup=math.sqrt(staterr*staterr+normerr*normerr+edeperrup*edeperrup)*10**(-flxindx)/10000.0
        calvals[E]=[flux,[toterrlo,toterrup],[E1,E2],0]
    return calvals    
    
def readDAMPEproflxvals(basepath='../',convtoR=False):
    damfile=open(basepath+'nucdata/DAMPEproton.dat','r')
    damvals={}
    while True:
        stringline = damfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        anaerr=float(stringlist.pop(0))
        haderr=float(stringlist.pop(0))
        expo=int(stringlist.pop(0))
        sumflx=flux*pow(10,expo)/10000.0
        rflx,R1=EtoR(sumflx,E1,"p")
        rflx,R2=EtoR(sumflx,E2,"p")
        rflx,R=EtoR(sumflx,E,"p")
        sumerr=math.sqrt(staterr*staterr+anaerr*anaerr+haderr*haderr)*pow(10,expo)/10000.0
        rerrup,R=EtoR(sumflx+sumerr,E,"p")
        rerrdown,R=EtoR(sumflx-sumerr,E,"p")
        rerrup=rerrup-rflx
        rerrdown=-(rerrdown-rflx)
        rerr=0.5*(rerrup+rerrdown)
        if convtoR:
            damvals[R]=[rflx,rerr,[R1,R2],0]
        else:
            damvals[E]=[sumflx,sumerr,[E1,E2],0]
    return damvals    
    


def readvoyagerproflxvals(basepath='../'):
    datfile=open(basepath+'nucdata/voyagerproton.dat','r')
    vals={}
    headerline = datfile.readline()
    while True:
        stringline = datfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))/1000.0
        E2=float(stringlist.pop(0))/1000.0
        E=float(stringlist.pop(0))/1000.0
        flux=float(stringlist.pop(0))/10.0    
        staterr=float(stringlist.pop(0))/10.0    
        syserr=float(stringlist.pop(0))/10.0    
        toterr=math.sqrt(staterr**2+syserr**2)
        vals[E]=[flux,toterr,[E1,E2],0]
    return vals



def readcreamproflxvals(basepath='../',C3=False):
    if C3:
        datfile=open(basepath+'nucdata/cream3proton.dat','r')
    else:
        datfile=open(basepath+'nucdata/cream1proton.dat','r')
    vals={}
    while True:
        stringline = datfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))
        E1exp=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        E2exp=float(stringlist.pop(0))
        E1=E1*pow(10,E1exp)
        E2=E2*pow(10,E2exp)
        E=math.sqrt(E1*E2)
        flux=float(stringlist.pop(0))    
        uperr=float(stringlist.pop(0))    
        lowerr=float(stringlist.pop(0))    
        fluxexp=float(stringlist.pop(0))
        flux=flux*pow(10,fluxexp)/10000.0
        uperr=uperr*pow(10,fluxexp)/10000.0
        lowerr=lowerr*pow(10,fluxexp)/10000.0
        vals[E]=[flux,[lowerr,uperr],[E1,E2],0]
    return vals

def readamsaprvals(basepath='../',returnflux=False):
    amsfile=open(basepath+'nucdata/AMSantiprot.dat','r')
    AMSvals={}
    while True:
        stringline = amsfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        R1=float(stringlist.pop(0))
        R2=float(stringlist.pop(0))
        R=math.sqrt(R1*R2)
        Nevt=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))
        fstaterr=float(stringlist.pop(0))
        fsyserr=float(stringlist.pop(0))
        ten=int(stringlist.pop(0))
        fexpo=int(stringlist.pop(0))
        sumflx=flux*pow(ten,-fexpo)/10000.0
        fsumerr=math.sqrt(fstaterr*fstaterr+fsyserr*fsyserr)*pow(ten,-fexpo)/10000.0
        ratio=float(stringlist.pop(0))
        rstaterr=float(stringlist.pop(0))
        rsyserr=float(stringlist.pop(0))
        ten=int(stringlist.pop(0))
        rexpo=int(stringlist.pop(0))
        sumratio=ratio*pow(ten,-rexpo)
        rsumerr=math.sqrt(rstaterr*rstaterr+rsyserr*rsyserr)*pow(ten,-rexpo)
        binsize=R2-R1
        if returnflux:
            AMSvals[R]=[sumflx,fsumerr,[R1,R2],0]
        else:
            AMSvals[R]=[sumratio,rsumerr,binsize]

    return AMSvals



#----------------- HELIUM ---------------------------------------------


def readamsHEflxvals(basepath='../',convtoE=True):
    amsfile=open(basepath+'nucdata/heliumAMS02.dat','r')
    AMSvals={}
    while True:
        stringline = amsfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        R1=float(stringlist.pop(0))
        R2=float(stringlist.pop(0))
        R=math.sqrt(R1*R2)
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        trigerr=float(stringlist.pop(0))
        accerr=float(stringlist.pop(0))
        unferr=float(stringlist.pop(0))
        scalerr=float(stringlist.pop(0))
        syserr=float(stringlist.pop(0))
        ten=int(stringlist.pop(0))
        expo=int(stringlist.pop(0))
        sumflx=flux*pow(10,expo)/10000.0
        sumerr=math.sqrt(staterr*staterr+syserr*syserr)*pow(10,expo)/10000.0
        eflx,En1=RtoE(sumflx,R1,"He")
        eflx,En2=RtoE(sumflx,R2,"He")
        eflx,En=RtoE(sumflx,R,"He")
        eerrup,En=RtoE(flux+sumerr,R,"He")
        eerrdown,En=RtoE(flux-sumerr,R,"He")
        eerrup=eerrup-eflx
        eerrdown=-(eerrdown-eflx)
        eerr=0.5*(eerrup+eerrdown)
        if convtoE:
            AMSvals[En]=[eflx,eerr,[En1,En2],0]
        else:
            AMSvals[R]=[sumflx,sumerr,[R1,R2],0]
    return AMSvals
    

def readamsHE3fractvals(basepath='../'):
    amsfile=open(basepath+'nucdata/He3to4AMS.dat','r')
    AMSvals={}
    while True:
        stringline = amsfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        E=math.sqrt(E1*E2)
        He3flux=float(stringlist.pop(0))
        He3staterr=float(stringlist.pop(0))
        He3syserr=float(stringlist.pop(0))
        He3expo=int(stringlist.pop(0))
        He4flux=float(stringlist.pop(0))
        He4staterr=float(stringlist.pop(0))
        He4syserr=float(stringlist.pop(0))
        He4expo=int(stringlist.pop(0))
        H34fract=float(stringlist.pop(0))
        H34staterr=float(stringlist.pop(0))
        H34syserr=float(stringlist.pop(0))
        H34expo=int(stringlist.pop(0))
        fract=H34fract*pow(10,H34expo)
        fracterr=math.sqrt(H34staterr*H34staterr+H34syserr*H34syserr)*pow(10,H34expo)        
        AMSvals[E]=[fract,fracterr,[E1,E2],0]
    return AMSvals    


def readcalHEflxvals(basepath='../'):
    calfile=open(basepath+'nucdata/heliumprelimCALET.dat','r')
    calvals={}
    while True:
        stringline = calfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        E=float(stringlist.pop(0))
        Escaleerr=float(stringlist.pop(0))
        Eedeperr=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        normerr=float(stringlist.pop(0))
        systerrup=float(stringlist.pop(0))
        systerrlo=float(stringlist.pop(0))
        expo=-int(stringlist.pop(0))
        sumflx=flux*pow(10,expo)/10000.0
        sumerrup=math.sqrt(staterr*staterr+normerr*normerr+systerrup*systerrup)*pow(10,expo)/10000.0
        sumerrlo=math.sqrt(staterr*staterr+normerr*normerr+systerrlo*systerrlo)*pow(10,expo)/10000.0
        eerr=math.sqrt(Escaleerr*Escaleerr+Eedeperr*Eedeperr)
        calvals[E]=[sumflx,[sumerrup,sumerrlo],[E1,E2],0]
    return calvals
    
def readcal2021HEflxvals(basepath='../'):
    calfile=open(basepath+'nucdata/heliumICRC2021CALET.dat','r')
    calvals={}
    headerline = calfile.readline()
    while True:
        stringline = calfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))/10000.0/pow(E,2.6)
        Eerrlo=float(stringlist.pop(0))
        Eerrup=float(stringlist.pop(0))
        E1=E-Eerrlo
        E2=E+Eerrup
        staterrlo=float(stringlist.pop(0))/10000.0/pow(E,2.6)
        staterrup=float(stringlist.pop(0))/10000.0/pow(E,2.6)
        toterrlo=float(stringlist.pop(0))/10000.0/pow(E,2.6)
        toterrup=float(stringlist.pop(0))/10000.0/pow(E,2.6)
        calvals[E]=[flux,[toterrup,toterrlo],[E1,E2],0]
    #En. Flux Err.En.Low Err.En.High Stat.Err.Low Stat.Err.High Stat+syst.Err.Low Stat+syst.Err.High    
    return calvals
        
def readcal2022HEflxvals(basepath='../'):
    calfile=open(basepath+'nucdata/helium22paoloCALET.dat','r')
    calvals={}
    headerline = calfile.readline()
    while True:
        stringline = calfile.readline()
        if stringline=='':
            break
        if stringline[0]=='#':
            continue
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        flux=float(stringlist.pop(0))/10000.0/pow(E,2.6)
        lostaterr=float(stringlist.pop(0))/10000.0/pow(E,2.6)
        histaterr=float(stringlist.pop(0))/10000.0/pow(E,2.6)
        lototerr=float(stringlist.pop(0))/10000.0/pow(E,2.6)
        hitoterr=float(stringlist.pop(0))/10000.0/pow(E,2.6)    
        syserrrel=float(stringlist.pop(0))    
        calvals[E]=[flux,[hitoterr,lototerr],[E,E],0]
        #En. Flux Err.En.Low Err.En.High Stat.Err.Low Stat.Err.High Stat+syst.Err.Low Stat+syst.Err.High    
    return calvals    
    
def readcal2022PRLHEflxvals(basepath='../',convtopernuc=False):
    calfile=open(basepath+'nucdata/heliumcalet2022.dat','r')
    calvals={}
    headerline = calfile.readline()
    while True:
        stringline = calfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        E=math.sqrt(E1*E2)
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        normerr=float(stringlist.pop(0))
        systerrup=float(stringlist.pop(0))
        systerrlo=float(stringlist.pop(0))
        expo=-int(stringlist.pop(0))
        sumflx=flux*pow(10,expo)/10000.0
        sumerrup=math.sqrt(staterr*staterr+normerr*normerr+systerrup*systerrup)*pow(10,expo)/10000.0
        sumerrlo=math.sqrt(staterr*staterr+normerr*normerr+systerrlo*systerrlo)*pow(10,expo)/10000.0
        if convtopernuc:
            pnflx,en=PPtoPN(sumflx,E,"He")
            sumerrupn,e2n=PPtoPN(sumerrup,E2,"He")
            sumerrlon,e1n=PPtoPN(sumerrlo,E1,"He")
            calvals[en]=[pnflx,[sumerrupn,sumerrlon],[e1n,e2n],0]
        else:
            calvals[E]=[sumflx,[sumerrup,sumerrlo],[E1,E2],0]
    return calvals

def readDAMPEheflxvals(basepath='../'):
    damfile=open(basepath+'nucdata/DAMPEhelium.dat','r')
    damvals={}
    while True:
        stringline = damfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))*1e3
        E2=float(stringlist.pop(0))*1e3
        E=float(stringlist.pop(0))*1e3
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        anaerr=float(stringlist.pop(0))
        haderr=float(stringlist.pop(0))
        expo=int(stringlist.pop(0))
        sumflx=flux*pow(10,expo)/10000.0
        sumerr=math.sqrt(staterr*staterr+anaerr*anaerr+haderr*haderr)*pow(10,expo)/10000.0
        damvals[E]=[sumflx,sumerr,[E1,E2],0]
    return damvals    



def readvoyagerheflxvals(basepath='../'):
    datfile=open(basepath+'nucdata/voyagerhelium.dat','r')
    vals={}
    headerline = datfile.readline()
    while True:
        stringline = datfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))/1000.0
        E2=float(stringlist.pop(0))/1000.0
        E=float(stringlist.pop(0))/1000.0
        flux=float(stringlist.pop(0))/10.0    
        staterr=float(stringlist.pop(0))/10.0    
        syserr=float(stringlist.pop(0))/10.0    
        toterr=math.sqrt(staterr**2+syserr**2)
        vals[E]=[flux,toterr,[E1,E2],0]
    return vals


#----------------- LITHIUM ---------------------------------------------


def readamsLIflxvals(basepath='../',convtoE=True):
    amsfile=open(basepath+'nucdata/AMSlithium.dat','r')
    AMSvals={}
    while True:
        stringline = amsfile.readline()
        if stringline=='' or stringline=='\n':
            break
        stringlist=stringline.split()
        R1=float(stringlist.pop(0))
        R2=float(stringlist.pop(0))
        R=math.sqrt(R1*R2)
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        accerr=float(stringlist.pop(0))
        unferr=float(stringlist.pop(0))
        scalerr=float(stringlist.pop(0))
        syserr=float(stringlist.pop(0))
        ten=int(stringlist.pop(0))
        expo=int(stringlist.pop(0))
        sumflx=flux*pow(10,expo)/10000.0
        sumerr=math.sqrt(staterr*staterr+syserr*syserr)*pow(10,expo)/10000.0
        eflx,En1=RtoE(sumflx,R1,"Li")
        eflx,En2=RtoE(sumflx,R2,"Li")
        eflx,En=RtoE(sumflx,R,"Li")
        eerrup,En=RtoE(flux+sumerr,R,"Li")
        eerrdown,En=RtoE(flux-sumerr,R,"Li")
        eerrup=eerrup-eflx
        eerrdown=-(eerrdown-eflx)
        eerr=0.5*(eerrup+eerrdown)
        if convtoE:
            AMSvals[En]=[eflx,eerr,[En1,En2],0]
        else:
            AMSvals[R]=[sumflx,sumerr,[R1,R2],0]
    return AMSvals


#def readamsLIflxvals(basepath='../'):
#    amsfile=open(basepath+'nucdata/AMSlithium.dat','r')
#    AMSvals={}
#    while True:
#        stringline = amsfile.readline()
#        if stringline=='':
#            break
#        stringlist=stringline.split()
#       e R=float(stringlist.pop(0))
#        flux=float(stringlist.pop(0))
#        sumflx=flux/pow(R,2.7)/10000.0
#        AMSvals[R]=[sumflx]
#    return AMSvals

#----------------- BERYLLIUM ---------------------------------------------


def readamsBEflxvals(basepath='../',convtoE=True):
    amsfile=open(basepath+'nucdata/AMSberyllium.dat','r')
    AMSvals={}
    while True:
        stringline = amsfile.readline()
        if stringline=='' or stringline=='\n':
            break
        stringlist=stringline.split()
        R1=float(stringlist.pop(0))
        R2=float(stringlist.pop(0))
        R=math.sqrt(R1*R2)
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        accerr=float(stringlist.pop(0))
        unferr=float(stringlist.pop(0))
        scalerr=float(stringlist.pop(0))
        syserr=float(stringlist.pop(0))
        ten=int(stringlist.pop(0))
        expo=-int(stringlist.pop(0))
        sumflx=flux*pow(10,expo)/10000.0
        sumerr=math.sqrt(staterr*staterr+syserr*syserr)*pow(10,expo)/10000.0
        eflx,En1=RtoE(sumflx,R1,"Li")
        eflx,En2=RtoE(sumflx,R2,"Li")
        eflx,En=RtoE(sumflx,R,"Li")
        eerrup,En=RtoE(flux+sumerr,R,"Li")
        eerrdown,En=RtoE(flux-sumerr,R,"Li")
        eerrup=eerrup-eflx
        eerrdown=-(eerrdown-eflx)
        eerr=0.5*(eerrup+eerrdown)
        if convtoE:
            AMSvals[En]=[eflx,eerr,[En1,En2],0]
        else:
            AMSvals[R]=[sumflx,sumerr,[R1,R2],0]
    return AMSvals
    
def readpamelaBeRatios(basepath='../',Be9=False):
    pamfile=open(basepath+'nucdata/BeRatiosPamela.dat','r')
    pamvals={}
    while True:
        stringline = pamfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        E=math.sqrt(E1*E2)
        Be7frac=float(stringlist.pop(0))
        Be7staterr=float(stringlist.pop(0))
        Be7systerr=float(stringlist.pop(0))
        Be9frac=float(stringlist.pop(0))
        Be9staterr=float(stringlist.pop(0))
        Be9systerr=float(stringlist.pop(0))
        binsize=E2-E1
        Be7toterr=math.sqrt(Be7staterr*Be7staterr+Be7systerr*Be7systerr)
        Be9toterr=math.sqrt(Be9staterr*Be9staterr+Be9systerr*Be9systerr)
        if Be9:
            pamvals[E]=[Be9frac,Be9toterr,[E1,E2],0]
        else:
            pamvals[E]=[Be7frac,Be7toterr,[E1,E2],0]
    return pamvals    

#----------------- BORON ---------------------------------------------


def readamsBflxvals(basepath='../',convtoE=True):
    amsfile=open(basepath+'nucdata/AMSboron.dat','r')
    AMSvals={}
    while True:
        stringline = amsfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        R1=float(stringlist.pop(0))
        R2=float(stringlist.pop(0))
        R=math.sqrt(R1*R2)
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        accerr=float(stringlist.pop(0))
        unferr=float(stringlist.pop(0))
        scalerr=float(stringlist.pop(0))
        syserr=float(stringlist.pop(0))
        ten=int(stringlist.pop(0))
        expo=int(stringlist.pop(0))
        sumflx=flux*pow(10,expo)/10000.0
        sumerr=math.sqrt(staterr*staterr+syserr*syserr)*pow(10,expo)/10000.0
        eflx,En1=RtoE(sumflx,R1,"B")
        eflx,En2=RtoE(sumflx,R2,"B")
        eflx,En=RtoE(sumflx,R,"B")
        eerrup,En=RtoE(flux+sumerr,R,"B")
        eerrdown,En=RtoE(flux-sumerr,R,"B")
        eerrup=eerrup-eflx
        eerrdown=-(eerrdown-eflx)
        eerr=0.5*(eerrup+eerrdown)
        if convtoE:
            AMSvals[En]=[eflx,eerr,[En1,En2],0]
        else:
            AMSvals[R]=[sumflx,sumerr,[R1,R2],0]
    return AMSvals



#----------------- CARBON ---------------------------------------------


def readamsCflxvals(basepath='../',convtoE=True):
    amsfile=open(basepath+'nucdata/AMScarbon.dat','r')
    AMSvals={}
    while True:
        stringline = amsfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        R1=float(stringlist.pop(0))
        R2=float(stringlist.pop(0))
        R=math.sqrt(R1*R2)
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        accerr=float(stringlist.pop(0))
        unferr=float(stringlist.pop(0))
        scalerr=float(stringlist.pop(0))
        syserr=float(stringlist.pop(0))
        ten=int(stringlist.pop(0))
        expo=int(stringlist.pop(0))
        sumflx=flux*pow(10,expo)/10000.0
        sumerr=math.sqrt(staterr*staterr+syserr*syserr)*pow(10,expo)/10000.0
        eflx,En1=RtoE(sumflx,R1,"C")
        eflx,En2=RtoE(sumflx,R2,"C")
        eflx,En=RtoE(sumflx,R,"C")
        eerrup,En=RtoE(flux+sumerr,R,"C")
        eerrdown,En=RtoE(flux-sumerr,R,"C")
        eerrup=eerrup-eflx
        eerrdown=-(eerrdown-eflx)
        eerr=0.5*(eerrup+eerrdown)
        if convtoE:
            AMSvals[En]=[eflx,eerr,[En1,En2],0]
        else:
            AMSvals[R]=[sumflx,sumerr,[R1,R2],0]
    return AMSvals
    
def readcalCflxvals(basepath='../'):
    calfile=open(basepath+'nucdata/carbonCALET2020.dat','r')
    CALvals={}
    while True:
        stringline = calfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        E=math.sqrt(E1*E2)
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        normerrhi=float(stringlist.pop(0))
        normerrlo=float(stringlist.pop(0))
        syserrhi=float(stringlist.pop(0))
        syserrlo=float(stringlist.pop(0))
        expo=-int(stringlist.pop(0))
        sumflx=flux*pow(10,expo)/10000.0
        hierr=math.sqrt(staterr*staterr+normerrhi*normerrhi+syserrhi*syserrhi)*pow(10,expo)/10000.0
        loerr=math.sqrt(staterr*staterr+normerrlo*normerrlo+syserrlo*syserrlo)*pow(10,expo)/10000.0
        CALvals[E]=[sumflx,[loerr,hierr],[E1,E2],0]
    return CALvals    
    
def readvoyagercaflxvals(basepath='../'):
    datfile=open(basepath+'nucdata/voyagercarbon.dat','r')
    vals={}
    headerline = datfile.readline()
    while True:
        stringline = datfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))/1000.0
        E2=float(stringlist.pop(0))/1000.0
        E=math.sqrt(E1*E2)
        flux=float(stringlist.pop(0))/10.0    
        staterr=float(stringlist.pop(0))/10.0    
        syserr=float(stringlist.pop(0))/10.0    
        toterr=math.sqrt(staterr**2+syserr**2)
        vals[E]=[flux,toterr,[E1,E2],0]
    return vals
    
#----------------- OXYGEN ---------------------------------------------


def readamsOflxvals(basepath='../',convtoE=True):
    amsfile=open(basepath+'nucdata/AMSoxygen.dat','r')
    AMSvals={}
    while True:
        stringline = amsfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        R1=float(stringlist.pop(0))
        R2=float(stringlist.pop(0))
        R=math.sqrt(R1*R2)
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        accerr=float(stringlist.pop(0))
        unferr=float(stringlist.pop(0))
        scalerr=float(stringlist.pop(0))
        syserr=float(stringlist.pop(0))
        ten=int(stringlist.pop(0))
        expo=-int(stringlist.pop(0))
        sumflx=flux*pow(10,expo)/10000.0
        sumerr=math.sqrt(staterr*staterr+syserr*syserr)*pow(10,expo)/10000.0
        eflx,En1=RtoE(sumflx,R1,"C")
        eflx,En2=RtoE(sumflx,R2,"C")
        eflx,En=RtoE(sumflx,R,"C")
        eerrup,En=RtoE(flux+sumerr,R,"C")
        eerrdown,En=RtoE(flux-sumerr,R,"C")
        eerrup=eerrup-eflx
        eerrdown=-(eerrdown-eflx)
        eerr=0.5*(eerrup+eerrdown)
        if convtoE:
            AMSvals[En]=[eflx,eerr,[En1,En2],0]
        else:
            AMSvals[R]=[sumflx,sumerr,[R1,R2],0]
    return AMSvals
    
def readcalOflxvals(basepath='../'):
    calfile=open(basepath+'nucdata/oxygenCALET2020.dat','r')
    CALvals={}
    while True:
        stringline = calfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        E=math.sqrt(E1*E2)
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        normerrhi=float(stringlist.pop(0))
        normerrlo=float(stringlist.pop(0))
        syserrhi=float(stringlist.pop(0))
        syserrlo=float(stringlist.pop(0))
        expo=-int(stringlist.pop(0))
        sumflx=flux*pow(10,expo)/10000.0
        hierr=math.sqrt(staterr*staterr+normerrhi*normerrhi+syserrhi*syserrhi)*pow(10,expo)/10000.0
        loerr=math.sqrt(staterr*staterr+normerrlo*normerrlo+syserrlo*syserrlo)*pow(10,expo)/10000.0
        CALvals[E]=[sumflx,[loerr,hierr],[E1,E2],0]
    return CALvals        
    
def readcalCOratio(basepath='../'):
    calfile=open(basepath+'nucdata/COratioCALET2020.dat','r')
    CALvals={}
    while True:
        stringline = calfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        E=math.sqrt(E1*E2)
        ratio=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        syserrhi=float(stringlist.pop(0))
        syserrlo=float(stringlist.pop(0))
        hierr=math.sqrt(staterr*staterr++syserrhi*syserrhi)
        loerr=math.sqrt(staterr*staterr+syserrlo*syserrlo)
        CALvals[E]=[ratio,[loerr,hierr],[E1,E2],0]
    return CALvals            
    
def readvoyageroxflxvals(basepath='../'):
    datfile=open(basepath+'nucdata/voyageroxygen.dat','r')
    vals={}
    headerline = datfile.readline()
    while True:
        stringline = datfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))/1000.0
        E2=float(stringlist.pop(0))/1000.0
        E=math.sqrt(E1*E2)
        flux=float(stringlist.pop(0))/10.0    
        staterr=float(stringlist.pop(0))/10.0    
        syserr=float(stringlist.pop(0))/10.0    
        toterr=math.sqrt(staterr**2+syserr**2)
        vals[E]=[flux,toterr,[E1,E2],0]
    return vals
    
#----------------- NEON ---------------------------------------------


def readamsNEflxvals(basepath='../',convtoE=True):
    amsfile=open(basepath+'nucdata/AMSneon.dat','r')
    AMSvals={}
    while True:
        stringline = amsfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        R1=float(stringlist.pop(0))
        R2=float(stringlist.pop(0))
        R=math.sqrt(R1*R2)
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        accerr=float(stringlist.pop(0))
        unferr=float(stringlist.pop(0))
        scalerr=float(stringlist.pop(0))
        syserr=float(stringlist.pop(0))
        ten=int(stringlist.pop(0))
        expo=-int(stringlist.pop(0))
        sumflx=flux*pow(10,expo)/10000.0
        sumerr=math.sqrt(staterr*staterr+syserr*syserr)*pow(10,expo)/10000.0
        eflx,En1=RtoE(sumflx,R1,"C")
        eflx,En2=RtoE(sumflx,R2,"C")
        eflx,En=RtoE(sumflx,R,"C")
        eerrup,En=RtoE(flux+sumerr,R,"C")
        eerrdown,En=RtoE(flux-sumerr,R,"C")
        eerrup=eerrup-eflx
        eerrdown=-(eerrdown-eflx)
        eerr=0.5*(eerrup+eerrdown)
        if convtoE:
            AMSvals[En]=[eflx,eerr,[En1,En2],0]
        else:
            AMSvals[R]=[sumflx,sumerr,[R1,R2],0]
    return AMSvals    
    
    
#----------------- MAGNESIUM ---------------------------------------------


def readamsMNflxvals(basepath='../',convtoE=True):
    amsfile=open(basepath+'nucdata/AMSmagnesium.dat','r')
    AMSvals={}
    while True:
        stringline = amsfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        R1=float(stringlist.pop(0))
        R2=float(stringlist.pop(0))
        R=math.sqrt(R1*R2)
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        accerr=float(stringlist.pop(0))
        unferr=float(stringlist.pop(0))
        scalerr=float(stringlist.pop(0))
        syserr=float(stringlist.pop(0))
        ten=int(stringlist.pop(0))
        expo=-int(stringlist.pop(0))
        sumflx=flux*pow(10,expo)/10000.0
        sumerr=math.sqrt(staterr*staterr+syserr*syserr)*pow(10,expo)/10000.0
        eflx,En1=RtoE(sumflx,R1,"C")
        eflx,En2=RtoE(sumflx,R2,"C")
        eflx,En=RtoE(sumflx,R,"C")
        eerrup,En=RtoE(flux+sumerr,R,"C")
        eerrdown,En=RtoE(flux-sumerr,R,"C")
        eerrup=eerrup-eflx
        eerrdown=-(eerrdown-eflx)
        eerr=0.5*(eerrup+eerrdown)
        if convtoE:
            AMSvals[En]=[eflx,eerr,[En1,En2],0]
        else:
            AMSvals[R]=[sumflx,sumerr,[R1,R2],0]
    return AMSvals    
    
#----------------- SILICON ---------------------------------------------


def readamsSIflxvals(basepath='../',convtoE=True):
    amsfile=open(basepath+'nucdata/AMSsilicon.dat','r')
    AMSvals={}
    while True:
        stringline = amsfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        R1=float(stringlist.pop(0))
        R2=float(stringlist.pop(0))
        R=math.sqrt(R1*R2)
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        accerr=float(stringlist.pop(0))
        unferr=float(stringlist.pop(0))
        scalerr=float(stringlist.pop(0))
        syserr=float(stringlist.pop(0))
        ten=int(stringlist.pop(0))
        expo=-int(stringlist.pop(0))
        sumflx=flux*pow(10,expo)/10000.0
        sumerr=math.sqrt(staterr*staterr+syserr*syserr)*pow(10,expo)/10000.0
        eflx,En1=RtoE(sumflx,R1,"C")
        eflx,En2=RtoE(sumflx,R2,"C")
        eflx,En=RtoE(sumflx,R,"C")
        eerrup,En=RtoE(flux+sumerr,R,"C")
        eerrdown,En=RtoE(flux-sumerr,R,"C")
        eerrup=eerrup-eflx
        eerrdown=-(eerrdown-eflx)
        eerr=0.5*(eerrup+eerrdown)
        if convtoE:
            AMSvals[En]=[eflx,eerr,[En1,En2],0]
        else:
            AMSvals[R]=[sumflx,sumerr,[R1,R2],0]
    return AMSvals



#----------------- IRON ---------------------------------------------


def readcalFeflxvals(basepath='../'):
    calfile=open(basepath+'nucdata/ironCALET2021.dat','r')
    CALvals={}
    while True:
        stringline = calfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        E=math.sqrt(E1*E2)
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        normerrhi=float(stringlist.pop(0))
        normerrlo=float(stringlist.pop(0))
        syserrhi=float(stringlist.pop(0))
        syserrlo=float(stringlist.pop(0))
        expo=-int(stringlist.pop(0))
        sumflx=flux*pow(10,expo)/10000.0
        hierr=math.sqrt(staterr*staterr+normerrhi*normerrhi+syserrhi*syserrhi)*pow(10,expo)/10000.0
        loerr=math.sqrt(staterr*staterr+normerrlo*normerrlo+syserrlo*syserrlo)*pow(10,expo)/10000.0
        CALvals[E]=[sumflx,[loerr,hierr],[E1,E2],0]
    return CALvals


def readamsFEflxvals(basepath='../',convtoE=True):
    amsfile=open(basepath+'nucdata/AMSiron.dat','r')
    AMSvals={}
    while True:
        stringline = amsfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        R1=float(stringlist.pop(0))
        R2=float(stringlist.pop(0))
        R=math.sqrt(R1*R2)
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        accerr=float(stringlist.pop(0))
        unferr=float(stringlist.pop(0))
        scalerr=float(stringlist.pop(0))
        syserr=float(stringlist.pop(0))
        ten=int(stringlist.pop(0))
        expo=-int(stringlist.pop(0))
        sumflx=flux*pow(10,expo)/10000.0
        sumerr=math.sqrt(staterr*staterr+syserr*syserr)*pow(10,expo)/10000.0
        eflx,En1=RtoE(sumflx,R1,"C")
        eflx,En2=RtoE(sumflx,R2,"C")
        eflx,En=RtoE(sumflx,R,"C")
        eerrup,En=RtoE(flux+sumerr,R,"C")
        eerrdown,En=RtoE(flux-sumerr,R,"C")
        eerrup=eerrup-eflx
        eerrdown=-(eerrdown-eflx)
        eerr=0.5*(eerrup+eerrdown)
        if convtoE:
            AMSvals[En]=[eflx,eerr,[En1,En2],0]
        else:
            AMSvals[R]=[sumflx,sumerr,[R1,R2],0]
    return AMSvals


def readamsFEOratio(basepath='../'):
    amsfile=open(basepath+'nucdata/AMSFEOratio.dat','r')
    AMSvals={}
    headerline = amsfile.readline()
    while True:
        stringline = amsfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        R1=float(stringlist.pop(0))
        R2=float(stringlist.pop(0))
        fract=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        accerr=float(stringlist.pop(0))
        unferr=float(stringlist.pop(0))
        scaleerr=float(stringlist.pop(0))
        systerr=float(stringlist.pop(0))
        R = math.sqrt(R1*R2)
        binsize=R2-R1
        toterr=math.sqrt(staterr*staterr+systerr*systerr)
        AMSvals[R]=[fract,toterr,[R1,R2],0]
    return AMSvals
    


def readamsFESIratio(basepath='../'):
    amsfile=open(basepath+'nucdata/AMSFESIratio.dat','r')
    AMSvals={}
    headerline = amsfile.readline()
    while True:
        stringline = amsfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        R1=float(stringlist.pop(0))
        R2=float(stringlist.pop(0))
        fract=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        accerr=float(stringlist.pop(0))
        unferr=float(stringlist.pop(0))
        scaleerr=float(stringlist.pop(0))
        systerr=float(stringlist.pop(0))
        R = math.sqrt(R1*R2)
        binsize=R2-R1
        toterr=math.sqrt(staterr*staterr+systerr*systerr)
        AMSvals[R]=[fract,toterr,[R1,R2],0]
    return AMSvals    
    
def readamsFEHEratio(basepath='../'):
    amsfile=open(basepath+'nucdata/AMSFEHEratio.dat','r')
    AMSvals={}
    headerline = amsfile.readline()
    while True:
        stringline = amsfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        R1=float(stringlist.pop(0))
        R2=float(stringlist.pop(0))
        fract=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        accerr=float(stringlist.pop(0))
        unferr=float(stringlist.pop(0))
        scaleerr=float(stringlist.pop(0))
        systerr=float(stringlist.pop(0))
        ten=int(stringlist.pop(0))
        expo=-int(stringlist.pop(0))
        R = math.sqrt(R1*R2)
        binsize=R2-R1
        fract=fract*pow(10,expo)
        toterr=math.sqrt(staterr*staterr+systerr*systerr)*pow(10,expo)
        AMSvals[R]=[fract,toterr,[R1,R2],0]
    return AMSvals        
    

def readheaoFeSubFeratio(basepath='../'):
    hfile=open(basepath+'nucdata/HEAO3FeSubFeRatio.dat','r')
    hvals={}
    while True:
        stringline = hfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        ratio=float(stringlist.pop(0))
        loval=float(stringlist.pop(0))
        upval=float(stringlist.pop(0))
        errhi=upval-ratio
        errlo=ratio-loval
        hvals[E]=[ratio,[errlo,errhi],[E,E],0]
    return hvals
    
def readsanrikuFeSubFeratio(basepath='../'):
    hfile=open(basepath+'nucdata/SanrikuFeSubFeRatio.dat','r')
    hvals={}
    while True:
        stringline = hfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        ratio=float(stringlist.pop(0))
        loval=float(stringlist.pop(0))
        #upval=float(stringlist.pop(0))
        #errhi=upval-ratio
        errlo=ratio-loval
        hvals[E]=[ratio,[errlo,errlo],[E,E],0]
    return hvals

#============== Nickel ===============================

def readcalNiflxvals(basepath='../'):
    calfile=open(basepath+'nucdata/nickelCALET2021.dat','r')
    CALvals={}
    while True:
        stringline = calfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        E=math.sqrt(E1*E2)
        flux=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        normerrhi=float(stringlist.pop(0))
        normerrlo=float(stringlist.pop(0))
        syserrhi=float(stringlist.pop(0))
        syserrlo=float(stringlist.pop(0))
        expo=-int(stringlist.pop(0))
        sumflx=flux*pow(10,expo)/10000.0
        hierr=math.sqrt(staterr*staterr+normerrhi*normerrhi+syserrhi*syserrhi)*pow(10,expo)/10000.0
        loerr=math.sqrt(staterr*staterr+normerrlo*normerrlo+syserrlo*syserrlo)*pow(10,expo)/10000.0
        CALvals[E]=[sumflx,[loerr,hierr],[E1,E2],0]
    return CALvals
    
    

def readcalFeNiratio(basepath='../'):
    calfile=open(basepath+'nucdata/irontonickelratio.dat','r')
    CALvals={}
    while True:
        stringline = calfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        ratio=float(stringlist.pop(0))
        upval=float(stringlist.pop(0))
        loval=float(stringlist.pop(0))
        errhi=upval-ratio
        errlo=ratio-loval
        CALvals[E]=[ratio,[errlo,errhi],[E,E],0]
    return CALvals
    

def readheaoFeNiratio(basepath='../'):
    hfile=open(basepath+'nucdata/irontonickelratioHEAO.dat','r')
    hvals={}
    while True:
        stringline = hfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        ratio=float(stringlist.pop(0))
        upval=float(stringlist.pop(0))
        loval=float(stringlist.pop(0))
        errhi=upval-ratio
        errlo=ratio-loval
        hvals[E]=[ratio,[errlo,errhi],[E,E],0]
    return hvals

#============== B/C ===============================


def readamsBCratioold(basepath='../'):
    amsfile=open(basepath+'BCdata/AMS-BC-2014.dat','r')
    AMSvals={}
    headerline = amsfile.readline()
    while True:
        stringline = amsfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        N=int(stringlist.pop(0))
        fract=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        systerr=float(stringlist.pop(0))
        E = math.sqrt(E1*E2)
        binsize=E2-E1
        toterr=math.sqrt(staterr*staterr+systerr*systerr)
        AMSvals[E]=[fract,toterr,[E1,E2],N]
    return AMSvals


def readamsBCratio(basepath='../'):
    amsfile=open(basepath+'BCdata/AMS-BC-2016.dat','r')
    AMSvals={}
    headerline = amsfile.readline()
    while True:
        stringline = amsfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        fract=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        backerr=float(stringlist.pop(0))
        accerr=float(stringlist.pop(0))
        unferr=float(stringlist.pop(0))
        scaleerr=float(stringlist.pop(0))
        converr=float(stringlist.pop(0))
        systerr=float(stringlist.pop(0))
        E = math.sqrt(E1*E2)
        binsize=E2-E1
        toterr=math.sqrt(staterr*staterr+systerr*systerr)
        AMSvals[E]=[fract,toterr,[E1,E2],0]
    return AMSvals


def readpamelaBCratio(basepath='../'):
    pamfile=open(basepath+'BCdata/PAMELA-BC.dat','r')
    pamvals={}
    headerline = pamfile.readline()
    while True:
        stringline = pamfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        E=float(stringlist.pop(0))
        fract=0.1*float(stringlist.pop(0))
        staterr=0.1*float(stringlist.pop(0))
        systerr=0.1*float(stringlist.pop(0))
        binsize=E2-E1
        toterr=math.sqrt(staterr*staterr+systerr*systerr)
        pamvals[E]=[fract,toterr,[E1,E2],0]
    return pamvals
    
    
def readYAcalBCratio(basepath='../'):
    calfile=open(basepath+'BCdata/YAbcratio_210611.dat','r')
    calvals={}
    while True:
        stringline = calfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        if stringline[0]=='#':
            continue
        E=float(stringlist.pop(0))    
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        fract=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        #systerr=0.1*float(stringlist.pop(0))
        binsize=E2-E1
        toterr=staterr #math.sqrt(staterr*staterr+systerr*systerr)
        calvals[E]=[fract,toterr,[E1,E2],0]
    return calvals
    
def readcal2021BCratio(basepath='../'):
    calfile=open(basepath+'BCdata/CALET_bc_210629.dat','r')
    calvals={}
    while True:
        stringline = calfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        if stringline[0]=='#':
            continue
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        E=float(stringlist.pop(0))    
        fract=float(stringlist.pop(0))
        staterrlo=float(stringlist.pop(0))
        staterrhi=float(stringlist.pop(0))
        syserrlo=float(stringlist.pop(0))
        syserrhi=float(stringlist.pop(0))
        binsize=E2-E1
        toterrhi=math.sqrt(staterrhi*staterrhi+syserrhi*syserrhi)
        toterrlo=math.sqrt(staterrlo*staterrlo+syserrlo*syserrlo)
        calvals[E]=[fract,[toterrlo,toterrhi],[E1,E2],0]
    return calvals    

def readcal2022PBBCratio(basepath='../'):
    calfile=open(basepath+'BCdata/CALET_bc_22paolo.dat','r')
    calvals={}
    while True:
        stringline = calfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        if stringline[0]=='#':
            continue
        E=float(stringlist.pop(0))    
        E1=float(stringlist.pop(0))
        E2=float(stringlist.pop(0))
        fract=float(stringlist.pop(0))
        staterrlo=float(stringlist.pop(0))
        staterrhi=float(stringlist.pop(0))
        syserrlo=float(stringlist.pop(0))
        syserrhi=float(stringlist.pop(0))
        binsize=E2-E1
        toterrhi=math.sqrt(staterrhi*staterrhi+syserrhi*syserrhi)
        toterrlo=math.sqrt(staterrlo*staterrlo+syserrlo*syserrlo)
        calvals[E]=[fract,[toterrlo,toterrhi],[E1,E2],0]
    return calvals    


#============== Ulysses ===============================

def readUlyssesnucratio(Z1,Z2,basepath='../'):
    ufile=open(basepath+'nucdata/ulysses.dat','r')
    E=0.185
    while True:
        stringline = ufile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        Z=int(stringlist.pop(0))
        if Z==Z1:
            A1=float(stringlist.pop(0))
            Aerr1=float(stringlist.pop(0))
        elif Z==Z2:
            A2=float(stringlist.pop(0))
            Aerr2=float(stringlist.pop(0))
    ratio=A1/A2
    ratioerror=ratio*math.sqrt((Aerr1/A1)**2+(Aerr2/A2**2))
    Uvals={}
    Uvals[E]=[ratio,ratioerror]
    return Uvals
    
#============== Power Law index ===============================


def readAMSindexpos(basepath='../'):
    ifile=open(basepath+'indexdata/AMSpos.dat','r')
    ivals={}
    while True:
        stringline = ifile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        ind=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        binsize=0.0
        ivals[E]=[ind,staterr,[E,E]]
    return ivals


def readAMSindexele(basepath='../'):
    ifile=open(basepath+'indexdata/AMSele.dat','r')
    ivals={}
    while True:
        stringline = ifile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        E=float(stringlist.pop(0))
        ind=float(stringlist.pop(0))
        staterr=float(stringlist.pop(0))
        binsize=0.0
        ivals[E]=[ind,staterr,[E,E]]
    return ivals





## Additional loading function
def loadresults(rfn):
    sfile=open(rfn,'rb')
    loadthing=pickle.load(sfile)
    sfile.close()
    return loadthing
