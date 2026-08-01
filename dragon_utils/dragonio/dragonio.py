import os, sys, time, math, pickle



def saveresults(rfn,results):
    sfile=open(rfn,'wb')
    pickle.dump(results, sfile,protocol=2)
    sfile.close()