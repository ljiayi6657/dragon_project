from __future__ import print_function
import os, sys, time, math

#Read Data from DRAGON output
def readDragonBKGautoSiP(dragonfilename,dragonoutpath,corrfact,Dragonvals=False,weight=1.0,maxZ=14):
    dragonfile=open(dragonoutpath+dragonfilename,'r')
    if not Dragonvals:
        Dragonvals={}
    stringline = dragonfile.readline()
    nuclist=stringline.split()
    nuclist.remove('[GeV]')
    #print(nuclist)
    while True:
        D={}
        stringline = dragonfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        for nkey in nuclist:
            if nkey=="Energy":
                E=float(stringlist.pop(0))
            else:
                if corrfact and not corrfact==1.0 and nkey in corrfact.keys():
                    D[nkey]=float(stringlist.pop(0))/10000.0*corrfact[nkey][E]*weight
                else:
                    D[nkey]=float(stringlist.pop(0))/10000.0*weight
        proflx=D["Sec_p"]+D["Pri_p"]
        heflx=(D["NUC_2003"]+D["NUC_2004"])
        #if "Sec_e+" in D.keys():
            #secpos=D["Sec_e+"]
        #else:
            #secpos=False
        if "Pri_e-" in nuclist and "Sec_e-" in nuclist and "Sec_e+" in nuclist:
            prielflx=D["Pri_e-"]
            secelflx=D["Sec_e-"]
            secposflx=D["Sec_e+"]
            toteflx=D["Pri_e-"]+D["Sec_e-"]+D["Sec_e+"]
            if (D["Pri_e-"]+D["Sec_e-"]+D["Sec_e+"]) > 0.0:
                posfrac=D["Sec_e+"]/(D["Pri_e-"]+D["Sec_e-"]+D["Sec_e+"])
            else:
                posfrac=False
        else:
            prielflx=False
            secelflx=False 
            secposflx=False
            toteflx=False
            posfrac=False
        if "Sec_pbar" in nuclist and "Ter_pbar" in nuclist:
            secap=D["Sec_pbar"]
            terap=D["Ter_pbar"]
        else:
            secap=False
            terap=False
        if maxZ>2:
            li6flx=(D["NUC_3007"])
            li7flx=(D["NUC_3007"])
            be7flx=(D["NUC_4007"])
            be9flx=(D["NUC_4009"])
            be10flx=(D["NUC_4010"])
            b10flx=(D["NUC_5010"])
            b11flx=(D["NUC_5011"])
            c12flx=(D["NUC_6012"])
            c13flx=(D["NUC_6013"])
            c14flx=(D["NUC_6014"])
        else:
            li6flx=False
            li7flx=False
            be7flx=False
            be9flx=False
            be10flx=False
            b10flx=False
            b11flx=False
            c12flx=False
            c13flx=False
            c14flx=False
        if maxZ>6:
            nflx=(D["NUC_7014"]+D["NUC_7015"])
        else:
            nflx=False
        if maxZ>7:
            o16flx=(D["NUC_8016"])
            o17flx=(D["NUC_8017"])
            o18flx=(D["NUC_8018"])
        else:
            o16flx=False
            o17flx=False
            o18flx=False
        if maxZ>9:
            neflx=(D["NUC_10020"]+D["NUC_10021"]+D["NUC_10022"])
        else:
            neflx=False
        if maxZ>11:
            mgflx=(D["NUC_12024"]+D["NUC_12025"]+D["NUC_12026"])
        else:
            mgflx=False
        if maxZ>13:
            siflx=(D["NUC_14028"]+D["NUC_14029"]+D["NUC_14030"]+D["NUC_14032"])
        else:
            siflx=False
        if not E in Dragonvals.keys():
            Dragonvals[E]=[proflx,heflx,D["NUC_2003"],D["NUC_2004"],prielflx,secelflx,secposflx,secap,terap,li6flx,li7flx,be7flx,be9flx,be10flx,b10flx,b11flx,c12flx,c13flx,c14flx,nflx,o16flx,o17flx,o18flx,neflx,mgflx,siflx]
        else:
            Dragonvals[E]=[proflx+Dragonvals[E][0],
                           heflx+Dragonvals[E][1],
                           D["NUC_2003"]+Dragonvals[E][2],
                           D["NUC_2004"]+Dragonvals[E][3],
                           prielflx+Dragonvals[E][4],
                           secelflx+Dragonvals[E][5],
                           secposflx+Dragonvals[E][6],
                           secap+Dragonvals[E][7],
                           terap+Dragonvals[E][8],
                           li6flx+Dragonvals[E][9],
                           li7flx+Dragonvals[E][10],
                           be7flx+Dragonvals[E][11],
                           be9flx+Dragonvals[E][12],
                           be10flx+Dragonvals[E][13],
                           b10flx+Dragonvals[E][14],
                           b11flx+Dragonvals[E][15],
                           c12flx+Dragonvals[E][16],
                           c13flx+Dragonvals[E][17],
                           c14flx+Dragonvals[E][18],
                           nflx+Dragonvals[E][19],
                           o16flx+Dragonvals[E][20],
                           o17flx+Dragonvals[E][21],
                           o18flx+Dragonvals[E][22],
                           neflx+Dragonvals[E][23],
                           mgflx+Dragonvals[E][24],
                           siflx+Dragonvals[E][25]]
    dragonfile.close()
    return Dragonvals


# Calculate B/C ratio from DRAGON output
def BCratio(NUC_5010, NUC_5011, NUC_6012, NUC_6013, NUC_6014=0):
    B=NUC_5010+NUC_5011
    C=NUC_6012+NUC_6013+NUC_6014
    if not math.isfinite(B) or not math.isfinite(C) or B < 0 or C <= 0:
        raise ValueError("B/C requires finite boron and positive carbon flux")
    return B/C


def readDragonBKGauto(dragonfilename,dragonoutpath,corrfact,Dragonvals=False,weight=1.0,maxZ=28):
    dragonfile=open(dragonoutpath+dragonfilename,'r')
    if not Dragonvals:
        Dragonvals={}
    stringline = dragonfile.readline()
    nuclist=stringline.split()
    nuclist.remove('[GeV]')
    #print(nuclist)
    nidragonfilename=dragonfilename.replace(Btype,"SRBINiCr").replace("Fe","Ni")
    if os.path.isfile(dragonoutpath+nidragonfilename):
        nidragonfile=open(dragonoutpath+nidragonfilename,'r')
        nistringline = nidragonfile.readline()
        ninuclist=nistringline.split()
        ninuclist.remove('[GeV]')
    else:
        nidragonfilename=False
    ninorm=False
    while True:
        D={}
        stringline = dragonfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        for nkey in nuclist:
            if nkey=="Energy":
                E=float(stringlist.pop(0))
            else:
                if corrfact and not corrfact==1.0 and nkey in corrfact.keys():
                    D[nkey]=float(stringlist.pop(0))/10000.0*corrfact[nkey][E]*weight
                else:
                    D[nkey]=float(stringlist.pop(0))/10000.0*weight
        proflx=D["Sec_p"]+D["Pri_p"]
        heflx=(D["NUC_2003"]+D["NUC_2004"])
        if "Sec_e+" in D.keys():
            secpos=D["Sec_e+"]
        else:
            secpos=False
        if "Sec_pbar" in nuclist and "Ter_pbar" in nuclist:
            secap=D["Sec_pbar"]
            terap=D["Ter_pbar"]
        else:
            secap=False
            terap=False
        if maxZ>2:
            li6flx=(D["NUC_3007"])
            li7flx=(D["NUC_3007"])
            be7flx=(D["NUC_4007"])
            be9flx=(D["NUC_4009"])
            be10flx=(D["NUC_4010"])
            b10flx=(D["NUC_5010"])
            b11flx=(D["NUC_5011"])
            c12flx=(D["NUC_6012"])
            c13flx=(D["NUC_6013"])
            c14flx=(D["NUC_6014"])
        else:
            li6flx=False
            li7flx=False
            be7flx=False
            be9flx=False
            be10flx=False
            b10flx=False
            b11flx=False
            c12flx=False
            c13flx=False
            c14flx=False
        if maxZ>6:
            nflx=(D["NUC_7014"]+D["NUC_7015"])
        else:
            nflx=False
        if maxZ>7:
            o16flx=(D["NUC_8016"])
            o17flx=(D["NUC_8017"])
            o18flx=(D["NUC_8018"])
        else:
            o16flx=False
            o17flx=False
            o18flx=False
        if maxZ>9:
            neflx=(D["NUC_10020"]+D["NUC_10021"]+D["NUC_10022"])
        else:
            neflx=False
        if maxZ>11:
            mgflx=(D["NUC_12024"]+D["NUC_12025"]+D["NUC_12026"])
        else:
            mgflx=False
        if maxZ>13:
            siflx=(D["NUC_14028"]+D["NUC_14029"]+D["NUC_14030"]+D["NUC_14032"])
        else:
            siflx=False
        if maxZ>25:
            phflx=(D["NUC_15031"]+D["NUC_15032"]+D["NUC_15033"])                                                                             # P Phosphorus 19
            suflx=(D["NUC_16032"]+D["NUC_16033"]+D["NUC_16034"]+D["NUC_16035"]+D["NUC_16036"])                                                #S Sulfur 20
            clflx=(D["NUC_17035"]+D["NUC_17036"]+D["NUC_17037"])                                                                             #Cl Chlorine 21
            arflx=(D["NUC_18036"]+D["NUC_18037"]+D["NUC_18038"]+D["NUC_18039"]+D["NUC_18040"]+D["NUC_18042"])                                 #Ar Argon 22
            kaflx=(D["NUC_19039"]+D["NUC_19040"]+D["NUC_19041"])                                                                              #K  Potassium 23
            caflx=(D["NUC_20041"]+D["NUC_20041"]+D["NUC_20042"]+D["NUC_20043"]+D["NUC_20044"]+D["NUC_20045"]+D["NUC_20047"]+D["NUC_20048"])    # Ca Calcium 24
            scflx=(D["NUC_21044"]+D["NUC_21045"]+D["NUC_21046"]+D["NUC_21047"]+D["NUC_21048"])                                               #Sc Scandium 25
            tiflx=(D["NUC_22044"]+D["NUC_22046"]+D["NUC_22047"]+D["NUC_22048"]+D["NUC_22049"]+D["NUC_22050"])                                 #Ti Titanium 26
            vaflx=(D["NUC_23048"]+D["NUC_23049"]+D["NUC_23050"]+D["NUC_23050"]+D["NUC_23051"])                                               #V Vanadium 27
            crflx=(D["NUC_24051"]+D["NUC_24052"]+D["NUC_24053"]+D["NUC_24054"])                                                             #Cr Chromium  28
            mnflx=(D["NUC_25052"]+D["NUC_25053"]+D["NUC_25053"]+D["NUC_25054"]+D["NUC_25055"])                                               #Mn Manganse 29
            feflx=(D["NUC_26054"]+D["NUC_26055"]+D["NUC_26056"]+D["NUC_26057"]+D["NUC_26058"]+D["NUC_26059"]+D["NUC_26060"])                    #30
        else:
            feflx=False
            phflx=False
            suflx=False
            clflx=False
            arflx=False
            kaflx=False
            caflx=False
            scflx=False
            tiflx=False
            vaflx=False
            crflx=False
            mnflx=False
            feflx=False
        if nidragonfilename:
            ND={}
            nistringline = nidragonfile.readline()
            if nistringline=='':
                print("error, nickel file ended before general file" )
            nistringlist=nistringline.split()
            for nkey in ninuclist:
                if nkey=="Energy":
                    NE=float(nistringlist.pop(0))
                elif nkey in ND:
                    ND[nkey]=ND[nkey]+float(nistringlist.pop(0))/10000.0*corrfact
                else:
                    ND[nkey]=float(nistringlist.pop(0))/10000.0*corrfact
            if not ninorm and ND["NUC_26056"]>0:
                ninorm=D["NUC_26056"]/ND["NUC_26056"]
            #feflx=(ND["NUC_26054"]+ND["NUC_26055"]+ND["NUC_26056"]+ND["NUC_26057"]+ND["NUC_26058"]+ND["NUC_26059"]+ND["NUC_26060"])*ninorm
            niflx=(ND["NUC_28066"]+ND["NUC_28064"]+ND["NUC_28062"]+ND["NUC_28061"]+ND["NUC_28060"]+ND["NUC_28059"]+ND["NUC_28058"]+ND["NUC_28057"]+ND["NUC_28056"])*ninorm
            coflx=(ND["NUC_27060"]+ND["NUC_27059"]+ND["NUC_27058"]+ND["NUC_27057"]+ND["NUC_27056"])*ninorm
        else:
            niflx=False
            coflx=False
        if not E in Dragonvals.keys():
            Dragonvals[E]=[proflx,heflx,D["NUC_2003"],D["NUC_2004"],secpos,secap,terap,li6flx,li7flx,be7flx,be9flx,be10flx,b10flx,b11flx,c12flx,c13flx,c14flx,nflx,o16flx,o17flx,o18flx,neflx,mgflx,siflx,phflx,suflx,clflx,arflx,kaflx,caflx,scflx,tiflx,vaflx,crflx,mnflx,feflx,coflx,niflx]
        else:
            Dragonvals[E]=[proflx+Dragonvals[E][0],heflx+Dragonvals[E][1],D["NUC_2003"]+Dragonvals[E][2],D["NUC_2004"]+Dragonvals[E][3],secpos+Dragonvals[E][4],secap+Dragonvals[E][5],terap+Dragonvals[E][6],li6flx+Dragonvals[E][7],li7flx+Dragonvals[E][8],be7flx+Dragonvals[E][9],be9flx+Dragonvals[E][10],be10flx+Dragonvals[E][11],b10flx+Dragonvals[E][12],b11flx+Dragonvals[E][13],c12flx+Dragonvals[E][14],c13flx+Dragonvals[E][15],c14flx+Dragonvals[E][16],nflx+Dragonvals[E][17],o16flx+Dragonvals[E][18],o17flx+Dragonvals[E][19],o18flx+Dragonvals[E][20],neflx+Dragonvals[E][21],mgflx+Dragonvals[E][22],siflx+Dragonvals[E][23],phflx+Dragonvals[E][24],suflx+Dragonvals[E][25],clflx+Dragonvals[E][26],arflx+Dragonvals[E][27],kaflx+Dragonvals[E][28],caflx+Dragonvals[E][29],scflx+Dragonvals[E][30],tiflx+Dragonvals[E][31],vaflx+Dragonvals[E][32],crflx+Dragonvals[E][33],mnflx+Dragonvals[E][34],feflx+Dragonvals[E][35],coflx+Dragonvals[E][36],niflx+Dragonvals[E][37]]
    dragonfile.close()
    return Dragonvals




def readDragonfileauto(dragonfilename,dragonoutpath,corrfact,maxZ=28,nidragonfilename=False):
    dragonfile=open(dragonoutpath+dragonfilename,'r')
    Dragonvals={}
    stringline = dragonfile.readline()
    nuclist=stringline.split()
    nuclist.remove('[GeV]')
    print(nuclist)
    if nidragonfilename:
        nidragonfile=open(dragonoutpath+nidragonfilename,'r')
        nistringline = nidragonfile.readline()
        ninuclist=nistringline.split()
        ninuclist.remove('[GeV]')
        print(ninuclist)
    ninorm=False
    while True:
        D={}
        stringline = dragonfile.readline()
        if stringline=='':
            break
        stringlist=stringline.split()
        for nkey in nuclist:
            if nkey=="Energy":
                E=float(stringlist.pop(0))
            else:
                D[nkey]=float(stringlist.pop(0))/10000.0*corrfact
        #   D["Sec_e+"]       D["Pri_e-"]       D["Sec_e-"]       D["Ter_pbar"]     D["Sec_pbar"]     D["Sec_p"]        D["Pri_p"]
        if "Pri_e-" in nuclist and "Sec_e-" in nuclist and "Sec_e+" in nuclist:
            prielflx=D["Pri_e-"]
            secelflx=D["Sec_e-"]
            secposflx=D["Sec_e+"]
            toteflx=D["Pri_e-"]+D["Sec_e-"]+D["Sec_e+"]
            if (D["Pri_e-"]+D["Sec_e-"]+D["Sec_e+"]) > 0.0:
                posfrac=D["Sec_e+"]/(D["Pri_e-"]+D["Sec_e-"]+D["Sec_e+"])
            else:
                posfrac=0.0
        else:
            prielflx=0.0
            secelflx=0.0
            secposflx=0.0
            toteflx=0.0
            posfrac=0.0
        if "Sec_pbar" in nuclist and "Ter_pbar" in nuclist:
            apflx=D["Sec_pbar"]+D["Ter_pbar"]
            if (D["Sec_p"]+D["Pri_p"]+D["Sec_pbar"]+D["Ter_pbar"])>0.0:
                apfrac=(D["Sec_pbar"]+D["Ter_pbar"])/(D["Sec_p"]+D["Pri_p"])
                #apfrac=D["Sec_pbar"]/(D["Sec_p"]+D["Pri_p"])
            else:
                apfrac=0.0
        else:
            apflx=0.0
            apfrac=0.0
        proflx=D["Pri_p"]+D["Sec_p"]
        if maxZ>2:
            li6flx=(D["NUC_3007"])
            li7flx=(D["NUC_3007"])
            beflx=(D["NUC_4007"]+D["NUC_4009"]+D["NUC_4010"])
            bflx=(D["NUC_5010"]+D["NUC_5011"])
            cflx=(D["NUC_6012"]+D["NUC_6013"]+D["NUC_6014"])
        else:
            li6flx=False
            li7flx=False
            beflx=False
            bflx=False
            cflx=False
        #print(E,D["NUC_6012"],D["NUC_6013"],D["NUC_6014"])
        if maxZ>6:
            nflx=(D["NUC_7014"]+D["NUC_7015"])
        else:
            nflx=False
        if maxZ>7:
            oflx=(D["NUC_8016"]+D["NUC_8017"]+D["NUC_8018"])
        else:
            oflx=False
        if maxZ>9:
            neflx=(D["NUC_10020"]+D["NUC_10021"]+D["NUC_10022"])
        else:
            neflx=False
        if maxZ>11:
            mgflx=(D["NUC_12024"]+D["NUC_12025"]+D["NUC_12026"])
        else:
            mgflx=False
        if maxZ>13:
            siflx=(D["NUC_14028"]+D["NUC_14029"]+D["NUC_14030"]+D["NUC_14032"])
        else:
            siflx=False
        if maxZ>25:
            phflx=(D["NUC_15031"]+D["NUC_15032"]+D["NUC_15033"])                                                                             # P Phosphorus 19
            suflx=(D["NUC_16032"]+D["NUC_16033"]+D["NUC_16034"]+D["NUC_16035"]+D["NUC_16036"])                                                #S Sulfur 20
            clflx=(D["NUC_17035"]+D["NUC_17036"]+D["NUC_17037"])                                                                             #Cl Chlorine 21
            arflx=(D["NUC_18036"]+D["NUC_18037"]+D["NUC_18038"]+D["NUC_18039"]+D["NUC_18040"]+D["NUC_18042"])                                 #Ar Argon 22
            kaflx=(D["NUC_19039"]+D["NUC_19040"]+D["NUC_19041"])                                                                              #K  Potassium 23
            caflx=(D["NUC_20041"]+D["NUC_20041"]+D["NUC_20042"]+D["NUC_20043"]+D["NUC_20044"]+D["NUC_20045"]+D["NUC_20047"]+D["NUC_20048"])    # Ca Calcium 24
            scflx=(D["NUC_21044"]+D["NUC_21045"]+D["NUC_21046"]+D["NUC_21047"]+D["NUC_21048"])                                               #Sc Scandium 25
            tiflx=(D["NUC_22044"]+D["NUC_22046"]+D["NUC_22047"]+D["NUC_22048"]+D["NUC_22049"]+D["NUC_22050"])                                 #Ti Titanium 26
            vaflx=(D["NUC_23048"]+D["NUC_23049"]+D["NUC_23050"]+D["NUC_23050"]+D["NUC_23051"])                                               #V Vanadium 27
            crflx=(D["NUC_24051"]+D["NUC_24052"]+D["NUC_24053"]+D["NUC_24054"])                                                             #Cr Chromium  28
            mnflx=(D["NUC_25052"]+D["NUC_25053"]+D["NUC_25053"]+D["NUC_25054"]+D["NUC_25055"])                                               #Mn Manganse 29
            feflx=(D["NUC_26054"]+D["NUC_26055"]+D["NUC_26056"]+D["NUC_26057"]+D["NUC_26058"]+D["NUC_26059"]+D["NUC_26060"])                    #30
        else:
            feflx=False
            phflx=False
            suflx=False
            clflx=False
            arflx=False
            kaflx=False
            caflx=False
            scflx=False
            tiflx=False
            vaflx=False
            crflx=False
            mnflx=False
            feflx=False
        if nidragonfilename:
            ND={}
            nistringline = nidragonfile.readline()
            if nistringline=='':
                print("error, nickel file ended before general file" )
            nistringlist=nistringline.split()
            for nkey in ninuclist:
                if nkey=="Energy":
                    NE=float(nistringlist.pop(0))
                elif nkey in ND:
                    ND[nkey]=ND[nkey]+float(nistringlist.pop(0))/10000.0*corrfact
                else:
                    ND[nkey]=float(nistringlist.pop(0))/10000.0*corrfact
            if not ninorm:
                ninorm=D["NUC_26056"]/ND["NUC_26056"]
            feflx=(ND["NUC_26054"]+ND["NUC_26055"]+ND["NUC_26056"]+ND["NUC_26057"]+ND["NUC_26058"]+ND["NUC_26059"]+ND["NUC_26060"])*ninorm
            niflx=(ND["NUC_28066"]+ND["NUC_28064"]+ND["NUC_28062"]+ND["NUC_28061"]+ND["NUC_28060"]+ND["NUC_28059"]+ND["NUC_28058"]+ND["NUC_28057"]+ND["NUC_28056"])*ninorm
            coflx=(ND["NUC_27060"]+ND["NUC_27059"]+ND["NUC_27058"]+ND["NUC_27057"]+ND["NUC_27056"])*ninorm
        else:
            niflx=False
            coflx=False
        Dragonvals[E]=[posfrac,li6flx,D["NUC_2003"],proflx,apflx,prielflx,secelflx,secposflx,D["Sec_p"],D["NUC_2004"],li7flx,beflx,bflx,cflx,nflx,oflx,neflx,mgflx,siflx,phflx,suflx,clflx,arflx,kaflx,caflx,scflx,tiflx,vaflx,crflx,mnflx,feflx,coflx,niflx] #Rheflx,R]
    dragonfile.close()
    return Dragonvals
