#!/usr/bin/python
from __future__ import print_function
import os, sys, time, math, glob,random

#print(sys.path

import datetime



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
nucdat["P"]=(15,30.974,30.974*dalton)
nucdat["S"]=(16,32.06,32.06*dalton)
nucdat["Cl"]=(17,35.45,35.45*dalton)
nucdat["Ar"]=(18,39.948,39.948*dalton)
nucdat["K"]=(19,39.0983,39.0983*dalton)
nucdat["Ca"]=(20,40.078,40.078*dalton)
nucdat["Sc"]=(21,44.956,44.956*dalton)
nucdat["Ti"]=(22,47.867,47.867*dalton)
nucdat["V"]=(23,50.9415,50.9415*dalton)
nucdat["Cr"]=(24,51.996,51.996*dalton)
nucdat["Mn"]=(25,54.938,54.938*dalton)
nucdat["Fe"]=(26,55.845,55.845*dalton)



def rig(En,nuc):
    z,a,rm=nucdat[nuc]
    #E=En*a
    R=(a/z)*math.sqrt(En**2+2*En*rm)
    #R=rm*math.sqrt( ( ((E/rm)+1.0)**2)-1.0)/z
    return R

def ekin(R,nuc):
    z,a,rm=nucdat[nuc]
    E=(math.sqrt(z**2*R**2+rm**2)-rm)
    En=E/a
    return En
   
ein=50   
print(rig(ein,"B"))
#rin=50.0   
#print(ekin(rin,"B"))
    
#print(rig(ekin(rin,"B"),"B"))

