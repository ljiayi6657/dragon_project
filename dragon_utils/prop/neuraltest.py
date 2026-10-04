#!/usr/bin/python3

import os, sys, time, math, glob, random

import tensorflow as tf
import numpy as np
import pandas as pd
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.layers import IntegerLookup
from tensorflow.keras.layers import Normalization
from tensorflow.keras.layers import StringLookup
from sklearn.model_selection import train_test_split

import datetime

try:
   import pickle5 as pickle
except:
   import pickle


print("TensorFlow version:", tf.__version__)

datapath="../../astro/CALplots/"

eminstr=("-5.0")

propmod="YDLB"

def main():

    #example2()
    chisquarepredict()
    #getrandommodel()
    #example3()
    #reeval()
    return
    
    
def chisquarepredict():
    (hashdict,foundfiles,globpardict,pflxs,pfs,x2s,x2dict,vx2s,vx2dict,rx2s,rx2dict,px2s,px2dict,hx2s,hx2dict,fx2s,fx2dict,qx2s,qx2dict,vfx2s,vfx2dict,likes,likedict,mlikes,mlikedict,tlikes,tlikedict,qlikes,qlikedict,slikes,slikedict,mx2s,mx2dict,sx2s,sx2dict,tss,tsdict,faultfiles,faultpardict,corrfactlist) = loadresults(datapath+"fitspectra-HeP-conv_fitsave%s.dat"%eminstr)  
    globpardict["Y1"]=rx2s
    globpardict["Y2"]=fx2s
    globpardict["Y3"]=px2s
    globpardict["Y4"]=hx2s

    dataframe=pd.DataFrame.from_dict(globpardict)
    print(dataframe.shape)
    print(dataframe.head())
    
    x_train, x_test = train_test_split(dataframe, test_size = 0.2) 

    Y1_train = np.array(x_train["Y1"])
    Y2_train = np.array(x_train["Y2"])
    Y3_train = np.array(x_train["Y3"])
    Y4_train = np.array(x_train["Y4"])


    Y1_test = np.array(x_test["Y1"])
    Y2_test = np.array(x_test["Y2"])
    Y3_test = np.array(x_test["Y3"])
    Y4_test = np.array(x_test["Y4"])
    
    
    x_train = x_train.drop(["Y1","Y2","Y3","Y4"], axis = 1)
    x_test = x_test.drop(["Y1","Y2","Y3","Y4"], axis = 1)
    
    x_train_norm = (x_train-x_train.mean())/x_train.std()
    x_test_norm = (x_test-x_test.mean())/x_test.std()
    
    input_layer = layers.Input(shape=(len(x_train.columns)))
    dense_layer_1 = layers.Dense(units = 128, activation = "linear")(input_layer) 
    dense_layer_2 = layers.Dense(units = 128, activation = "exponential")(dense_layer_1)
    norm_layer=layers.GroupNormalization()(dense_layer_1)
    dense_layer_3 = layers.Dense(units = 512, activation = "sigmoid")(norm_layer)
    dense_layer_l = layers.Dense(units = 128, activation = "softmax")(dense_layer_3)
    dense_layer_fa = layers.Dense(units = 32, activation = "softmax",kernel_constraint=keras.constraints.non_neg())(dense_layer_l)
    dense_layer_fb = layers.Dense(units = 32, activation = "softmax",kernel_constraint=keras.constraints.non_neg())(dense_layer_l)
    dense_layer_fc = layers.Dense(units = 32, activation = "softmax",kernel_constraint=keras.constraints.non_neg())(dense_layer_l)
    dense_layer_fd = layers.Dense(units = 32, activation = "softmax",kernel_constraint=keras.constraints.non_neg())(dense_layer_l)

    #Y1 output
    y1_output = layers.Dense(units = 1, activation = "linear", name = "y1_output")(dense_layer_fa)

    #Y2 output
    y2_output = layers.Dense(units = 1, activation = "linear", name = "y2_output")(dense_layer_fb)
    
    #Y3 output
    y3_output = layers.Dense(units = 1, activation = "linear", name = "y3_output")(dense_layer_fc)

    #Y4 output
    y4_output = layers.Dense(units = 1, activation = "linear", name = "y4_output")(dense_layer_fd)
    
    strategy = tf.distribute.MirroredStrategy()
    print('Number of devices: {}'.format(strategy.num_replicas_in_sync))
    

    #Define the model with the input layer and a list of outputs
    model = keras.Model(inputs = input_layer, outputs = [y1_output, y2_output,  y3_output,  y4_output])
    #model = keras.Model(inputs = input_layer, outputs = [y1_output])

    #specify the optimizer and compile with the loss function for both outputs
    #optimizer = keras.optimizers.RMSprop(learning_rate=0.1)
    optimizer = keras.optimizers.Nadam()
    

    model.compile(optimizer = optimizer,loss = {'y1_output':keras.losses.MeanSquaredError() , 'y2_output':keras.losses.MeanSquaredError() , 'y3_output':keras.losses.MeanSquaredError() , 'y4_output':keras.losses.MeanSquaredError()},metrics = {'y1_output':tf.keras.metrics.MeanAbsolutePercentageError(),'y2_output':tf.keras.metrics.MeanAbsolutePercentageError(),'y3_output':tf.keras.metrics.MeanAbsolutePercentageError(),'y4_output':tf.keras.metrics.MeanAbsolutePercentageError()})
    #model.compile(optimizer = optimizer,loss = {'y1_output':keras.losses.MeanAbsoluteError()},metrics = {'y1_output':tf.keras.metrics.MeanAbsolutePercentageError()})
    
    #plot_model(model, show_shapes = True)
    #training process
    model.fit(x_train_norm, (Y1_train, Y2_train, Y3_train, Y4_train), epochs = 10000, batch_size = 2048,validation_data = (x_test_norm, (Y1_test, Y2_test, Y3_test, Y4_test)), verbose = 0)       
    #model.fit(x_train_norm, Y1_train, epochs = 10000, batch_size = 128,validation_data = (x_test_norm, Y1_test), verbose = 1)       
    
    model.save(datapath+"ANN_RX_test.ann")    
    return
    
def reeval():
    model = keras.models.load_model(datapath+"ANN_RX_test.ann")
    (hashdict,foundfiles,globpardict,pflxs,pfs,x2s,x2dict,vx2s,vx2dict,rx2s,rx2dict,px2s,px2dict,hx2s,hx2dict,fx2s,fx2dict,qx2s,qx2dict,vfx2s,vfx2dict,likes,likedict,mlikes,mlikedict,tlikes,tlikedict,qlikes,qlikedict,slikes,slikedict,mx2s,mx2dict,sx2s,sx2dict,tss,tsdict,faultfiles,faultpardict,corrfactlist) = loadresults(datapath+"fitspectra-HeP-conv_fitsave%s.dat"%eminstr)
    
    dataframe=pd.DataFrame.from_dict(globpardict)
    x_test = dataframe
    x_test_norm = (x_test-x_test.mean())/x_test.std()
   
    evalres=model.predict(x_test_norm,batch_size=128)
    #print(evalres)
        
    for pr,rx2 in zip(list(evalres[0]),rx2s): 
        if pr[0]<10:
            print(pr[0],rx2,pr[0]-rx2)
        elif rx2<10:
            print(pr[0],rx2,pr[0]-rx2)
    
    return

def getrandommodel(): 
    model = keras.models.load_model(datapath+"ANN_RX_test.ann")
    (hashdict,foundfiles,globpardict,pflxs,pfs,x2s,x2dict,vx2s,vx2dict,rx2s,rx2dict,px2s,px2dict,hx2s,hx2dict,fx2s,fx2dict,qx2s,qx2dict,vfx2s,vfx2dict,likes,likedict,mlikes,mlikedict,tlikes,tlikedict,qlikes,qlikedict,slikes,slikedict,mx2s,mx2dict,sx2s,sx2dict,tss,tsdict,faultfiles,faultpardict,corrfactlist) = loadresults(datapath+"fitspectra-HeP-conv_fitsave%s.dat"%eminstr)
        
    totpardict={}
    for keystr in globpardict.keys():
        totpardict[keystr]=globpardict[keystr]+faultpardict[keystr]
    orderlist=rx2s
    orderdict=rx2dict
    print("found files:")
    for rc2 in sorted(rx2dict.keys(),reverse=True):
        nf=rx2dict[rc2]
        ff=foundfiles[nf-1].rpartition("/")[2]
        pf=pfs[nf-1]
        ts=tss[nf-1]
        totc2=x2s[nf-1]
        pc2=px2s[nf-1]
        hc2=hx2s[nf-1]
        vc2=vx2s[nf-1]
        qc2=qx2s[nf-1]
        fc2=fx2s[nf-1]
        vfc2=vfx2s[nf-1]
        print('\033[1m'+str(nf)+'\033[0m',ff,"\nx: ",totc2," r: ",rc2," q: ", qc2," vf: ",vfc2," f: ",fc2," v: ",vc2," p: ",pc2," h: ",hc2,"\ndate:",time.ctime(ts)," ",pf[3],pf[4])      
    inp=input("select file number\n")
    while True:
        try:
            if inp=="a":
                analyzeps=True
                break   
            else:     
                iinp=int(inp)
                if iinp > 0 and iinp not in orderdict.values():
                    raise ValueError
                break
        except:
            inp=input("input a number up to %d please\n"%max(orderdict.values()))   
    dragfileBKG=foundfiles[iinp-1].rpartition("/")[2]
    x2minp=input("enter maximum chi-square for determining randomization step size (global minimum: %2.4f ; global maximum: %2.4f)\n"%(min(orderlist),max(orderlist))) 
    
    while True:
        try:
            x2m=float(x2minp)
            if x2m < min(orderlist):
                raise ValueError
            break
        except:
            x2minp=input("input a number larger than the minimum chi-square please\n")                  
    parspsize=parameterspacesize(globpardict,orderdict,orderlist,x2m)    
    parsptotsize=math.sqrt(sum([1.0 for x in parspsize.values() if x>0])) 
    
    rssinp=input("enter relative randomization step size (percent of scanned parameter range)\n") 
    while True:
        try:
            randstep=float(rssinp)/100.0
            break
        except:
            rssinp=input("input a number please\n")
    rmdinp=input("enter minimum distance to other models (percent of scanned parameter space size: %d)\n"%parsptotsize) 
    while True:
        try:
            randmindist=parsptotsize*float(rmdinp)/100.0
            break
        except:
            rmdinp=input("input a number please\n") 
    gpb=extractparamsfromfilename(dragfileBKG,globpardict.keys()) 
    randmods={}
    for pn in globpardict.keys():
        randmods[pn]=[]        
    rmodlist=[]
    for i in range(1000): 
        randdist=0    
        while randdist<randmindist:
            gpr={}
            for pn in globpardict.keys(): 
                gpr[pn]=gpb[pn]+random.uniform(-parspsize[pn]*randstep,parspsize[pn]*randstep)
                print(pn,"base value: ",gpb[pn]," random value: ",gpr[pn]," stepsize: ",parspsize[pn]*randstep)
            indxlst,nearlst=findnearestmodels(gpr,totpardict,orderdict,orderlist,x2m)
            randdist=nearlst[indxlst[1]]
            if randdist<randmindist:
                if indxlst[1]+1 not in orderlist:
                    print("model too close to a faulty model - distance %2.4f < minimum distance %2.4f - rejecting"%(randdist,randmindist))
                else:     
                    print("model too close to model no %d - distance %2.4f < minimum distance %2.4f - rejecting"%(indxlst[1]+1,randdist,randmindist))
            else:
                print("model accepted - distance to model %d : %2.4f > minimum distance %2.4f"%(indxlst[1]+1,randdist,randmindist))                
        #printmodel(gpr)
        for pn,pv in gpr.items():
            randmods[pn].append(pv)
        rmodlist.append(gpr)
    evalmods=pd.DataFrame.from_dict(randmods)
    
    prediction=model.predict(evalmods)
    plist=[]
    for p in prediction:
        plist.append(p[0])       
    print(plist)
    minx2=min(plist)
    print("best random model with rx = %f:"%minx2)
    bestmodid=plist.index(minx2)
    printmodel(rmodlist[bestmodid])
    return


def example3():


    data_path = "./ENB2012_data.csv"

    df = pd.read_csv(data_path)
 
    #Train test split
    x_train, x_test = train_test_split(df, test_size = 0.2)

    #train values
    Y1_train = np.array(x_train["Y1"])
    Y2_train = np.array(x_train["Y2"])

    #test values
    Y1_test = np.array(x_test["Y1"])
    Y2_test = np.array(x_test["Y2"])

    #remove the target values from the dataset
    x_train = x_train.drop(["Y1","Y2"], axis = 1)
    x_test = x_test.drop(["Y1","Y2"], axis = 1)

    #Normalizing the data set
    x_train_norm = (x_train-x_train.mean())/x_train.std()
    x_test_norm = (x_test-x_test.mean())/x_test.std()
        
    #show the first 5 rows
    print(df.head())
    # defining layers
    input_layer = layers.Input(shape=(len(x_train.columns)))
    dense_layer_1 = layers.Dense(units = 128, activation = "relu")(input_layer) 
    dense_layer_2 = layers.Dense(units = 128, activation = "relu")(dense_layer_1)
    dense_layer_3 = layers.Dense(units = 64, activation = "relu")(dense_layer_2)

    #Y1 output
    y1_output = layers.Dense(units = 1, activation = "linear", name = "y1_output")(dense_layer_2)

    #Y2 output
    y2_output = layers.Dense(units = 1, activation = "linear", name = "y2_output")(dense_layer_3)

    #Define the model with the input layer and a list of outputs
    model = keras.Model(inputs = input_layer, outputs = [y1_output, y2_output])

    #specify the optimizer and compile with the loss function for both outputs
    optimizer = tf.keras.optimizers.SGD(lr=0.001)

    model.compile(optimizer = optimizer,loss = {'y1_output':'mse', 'y2_output':'mse'},metrics = {'y1_output':tf.keras.metrics.RootMeanSquaredError(),'y2_output':tf.keras.metrics.RootMeanSquaredError()})
    #plot_model(model, show_shapes = True)
    #training process
    model.fit(x_train_norm, (Y1_train, Y2_train), epochs = 2000, batch_size = 10,validation_data = (x_test_norm, (Y1_test, Y2_test)), verbose = 2)
    return

def example2():
    dataframe = pd.read_csv("./heart.csv")
    print(dataframe.shape)
    print(dataframe.head())
    val_dataframe = dataframe.sample(frac=0.2, random_state=1337)
    train_dataframe = dataframe.drop(val_dataframe.index)

    print("Using %d samples for training and %d for validation"% (len(train_dataframe), len(val_dataframe)))
    
    train_ds = dataframe_to_dataset(train_dataframe)
    val_ds = dataframe_to_dataset(val_dataframe)
    for x, y in train_ds.take(1):
        print("Input:", x)
        print("Target:", y)
    
    train_ds = train_ds.batch(32)
    val_ds = val_ds.batch(32)
    
    # Categorical features encoded as integers
    sex = keras.Input(shape=(1,), name="sex", dtype="int64")
    cp = keras.Input(shape=(1,), name="cp", dtype="int64")
    fbs = keras.Input(shape=(1,), name="fbs", dtype="int64")
    restecg = keras.Input(shape=(1,), name="restecg", dtype="int64")
    exang = keras.Input(shape=(1,), name="exang", dtype="int64")
    ca = keras.Input(shape=(1,), name="ca", dtype="int64")

    # Categorical feature encoded as string
    thal = keras.Input(shape=(1,), name="thal", dtype="string")

    # Numerical features
    age = keras.Input(shape=(1,), name="age")
    trestbps = keras.Input(shape=(1,), name="trestbps")
    chol = keras.Input(shape=(1,), name="chol")
    thalach = keras.Input(shape=(1,), name="thalach")
    oldpeak = keras.Input(shape=(1,), name="oldpeak")
    slope = keras.Input(shape=(1,), name="slope")

    all_inputs = [sex,cp,fbs,restecg,exang,ca,thal,age,trestbps,chol,thalach,oldpeak,slope]

    # Integer categorical features
    sex_encoded = encode_categorical_feature(sex, "sex", train_ds, False)
    cp_encoded = encode_categorical_feature(cp, "cp", train_ds, False)
    fbs_encoded = encode_categorical_feature(fbs, "fbs", train_ds, False)
    restecg_encoded = encode_categorical_feature(restecg, "restecg", train_ds, False)
    exang_encoded = encode_categorical_feature(exang, "exang", train_ds, False)
    ca_encoded = encode_categorical_feature(ca, "ca", train_ds, False)

    # String categorical features
    thal_encoded = encode_categorical_feature(thal, "thal", train_ds, True)

    # Numerical features
    age_encoded = encode_numerical_feature(age, "age", train_ds)
    trestbps_encoded = encode_numerical_feature(trestbps, "trestbps", train_ds)
    chol_encoded = encode_numerical_feature(chol, "chol", train_ds)
    thalach_encoded = encode_numerical_feature(thalach, "thalach", train_ds)
    oldpeak_encoded = encode_numerical_feature(oldpeak, "oldpeak", train_ds)
    slope_encoded = encode_numerical_feature(slope, "slope", train_ds)

    all_features = layers.concatenate([sex_encoded,cp_encoded,fbs_encoded,restecg_encoded,exang_encoded,slope_encoded,ca_encoded,thal_encoded,age_encoded,trestbps_encoded,chol_encoded,thalach_encoded,oldpeak_encoded])
    x = layers.Dense(32, activation="relu")(all_features)
    x = layers.Dropout(0.5)(x)
    output = layers.Dense(1, activation="sigmoid")(x)
    model = keras.Model(all_inputs, output)
    model.compile("adam", "binary_crossentropy", metrics=["accuracy"])
    #keras.utils.plot_model(model, show_shapes=True, rankdir="LR")
    
    model.fit(train_ds, epochs=50, validation_data=val_ds)
    return

def example1():

    mnist = tf.keras.datasets.mnist

    (x_train, y_train), (x_test, y_test) = mnist.load_data()
    x_train, x_test = x_train / 255.0, x_test / 255.0

    model = tf.keras.models.Sequential([tf.keras.layers.Flatten(input_shape=(28, 28)),tf.keras.layers.Dense(128, activation='relu'),tf.keras.layers.Dropout(0.2),tf.keras.layers.Dense(10)])

    predictions = model(x_train[:1]).numpy()
    print(predictions)
    
    tf.nn.softmax(predictions).numpy()

    loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)

    loss_fn(y_train[:1], predictions).numpy()

    model.compile(optimizer='adam',loss=loss_fn,metrics=['accuracy'])

    model.fit(x_train, y_train, epochs=5)

    model.evaluate(x_test,  y_test, verbose=2)

    probability_model = tf.keras.Sequential([model,tf.keras.layers.Softmax()])

    print(probability_model(x_test[:5]))

def dataframe_to_dataset(dataframe):
    dataframe = dataframe.copy()
    labels = dataframe.pop("target")
    ds = tf.data.Dataset.from_tensor_slices((dict(dataframe), labels))
    ds = ds.shuffle(buffer_size=len(dataframe))
    return ds

def encode_numerical_feature(feature, name, dataset):
    # Create a Normalization layer for our feature
    normalizer = Normalization()

    # Prepare a Dataset that only yields our feature
    feature_ds = dataset.map(lambda x, y: x[name])
    feature_ds = feature_ds.map(lambda x: tf.expand_dims(x, -1))

    # Learn the statistics of the data
    normalizer.adapt(feature_ds)

    # Normalize the input feature
    encoded_feature = normalizer(feature)
    return encoded_feature

def encode_categorical_feature(feature, name, dataset, is_string):
    lookup_class = StringLookup if is_string else IntegerLookup
    # Create a lookup layer which will turn strings into integer indices
    lookup = lookup_class(output_mode="binary")

    # Prepare a Dataset that only yields our feature
    feature_ds = dataset.map(lambda x, y: x[name])
    feature_ds = feature_ds.map(lambda x: tf.expand_dims(x, -1))

    # Learn the set of possible string values and assign them a fixed integer index
    lookup.adapt(feature_ds)

    # Turn the string input into integer indices
    encoded_feature = lookup(feature)
    return encoded_feature

def parameterspacesize(gpd,od,ol,maxc2):
        sizes={}
        for pn in gpd.keys():
            redlist=[x for x,c in zip(gpd[pn],ol) if c<maxc2] 
            sizes[pn]=max(redlist)-min(redlist)
        return sizes

def extractparamsfromfilename(filename,paramlist):
    fks=filekeys["conv"]
    lgp={}    
    for keystr in paramlist:        
       if fks[keystr][3]:
            if len(fks[keystr])>4:
                fnentr=filename.partition(fks[keystr][3])[2].partition(fks[keystr][0])[2].partition(fks[keystr][4])[0].partition(fks[keystr][1])[0].replace("d",".")
            else:
                fnentr=filename.partition(fks[keystr][3])[2].partition(fks[keystr][0])[2].partition(fks[keystr][1])[0].replace("d",".")
       else:
            if len(fks[keystr])>4:
                fnentr=filename.partition(fks[keystr][0])[2].partition(fks[keystr][4])[0].partition(fks[keystr][1])[0].replace("d",".")
            else:
                fnentr=filename.partition(fks[keystr][0])[2].partition(fks[keystr][1])[0].replace("d",".")                
       if fnentr=='' or "R" in fnentr:
            fnentr=fks[keystr][2]    
       lgp[keystr]=float(fnentr)  
    return lgp
    
def findfarthestmodels(gpb,gpd,od,ol,maxc2):
        return findnearestmodels(gpb,gpd,od,ol,maxc2,inverse=True)
        
def findnearestmodels(gpb,gpd,od,ol,maxc2,inverse=False):
        parspsize=parameterspacesize(gpd,od,ol,maxc2)
        distdict={}
        for pn in gpb.keys():
            if parspsize[pn]>0:
                distdict[pn]=[((x-gpb[pn])/parspsize[pn])**2 for x in gpd[pn]] 
            else:
                distdict[pn]=[0 for x in gpd[pn]] 
        totdistlist=False
        for pn in gpb.keys():
            if not totdistlist:
                totdistlist=list(distdict[pn])
            else:
                totdistlist=[a+b for a,b in zip(totdistlist,distdict[pn])]
        totdistlist=[math.sqrt(a) for a in totdistlist]
        orderdistlist=sorted(totdistlist)       
        if inverse:
            orderdistlist.reverse()
        indxlist=[totdistlist.index(a) for a in orderdistlist] 
        return indxlist,totdistlist          
    
def printmodel(fgp,gp):
    print("---------------------------------------------------")
    #print("ncut=%d"%int(round(fgp["nuccut"])))
    print("ncut=%1.4f"%fgp["nuccut"])          
    print("deltscan=[%1.4f]"%fgp["diffexp"])             
    print("Dscan=[%1.4f]"%fgp["diffnorm"])               
    print("reaccscan=[%1.4f]"%fgp["alvel"])            
    print("indxscan=[%1.4f]"%fgp["sindex"])            
    print("lowindex=%1.4f"%fgp["lowindx"])            
    print("lowbreak=%1.4f"%fgp["lowbreak"])            
    print("lowsoft=%1.4f"%fgp["lowsoft"])            
    print("diffscaleheight=%1.4f"%fgp["DE"])            
    print("diffscaleradius=%1.4f"%fgp["DR"]) 
    print("highdelt=%1.4f"%(max(fgp["highexp"],1e-4))) 
    print("deltbreak=%1.4f"%fgp["diffbreak"]) 
    print("dbreaksoft=%1.4f"%fgp["diffbreaksoft"])
    if "LB" in gp["propmod"]:
        print("lowdelt=%1.4f"%fgp["lowexp"]) 
        print("lowdeltbreak=%1.4f"%fgp["lowdiffbreak"]) 
        print("lowdbreaksoft=%1.4f"%fgp["lowdiffbreaksoft"])
    print("SW=%1.4f"%(max(fgp["spiralwidth"],1e-4)))        
    print("convel=%1.4f"%(max(fgp["convel"],1e-4)))
    print("---------------------------------------------------")
    return   

def saveresults(rfn,results):
    sfile=open(rfn,'wb')   
    pickle.dump(results, sfile,protocol=-1)
    sfile.close

def loadresults(rfn):
    sfile=open(rfn,'rb')   
    loadthing=pickle.load(sfile)
    sfile.close
    return loadthing
    
    
filekeys={}

filekeys["conv"]={}
filekeys["conv"]["diffexp"]=("-d","B",False,False)
filekeys["conv"]["sindex"]=("-g","-",2.8,False)
filekeys["conv"]["diffnorm"]=("-D","-",False,False)
filekeys["conv"]["DE"]=("-DE","N",False,False)
filekeys["conv"]["DR"]=("R","B",False,"-DE")
filekeys["conv"]["alvel"]=("-R","-",0.0,False)
filekeys["conv"]["diffL"]=("-L","-",6.0,False)
filekeys["conv"]["nuccut"]=("-NC","-",False,False)
filekeys["conv"]["spiralwidth"]=("-SW","-",0.3,False)
filekeys["conv"]["highexp"]=("H","S",False,"-d") 
filekeys["conv"]["diffbreak"]=("B","H",False,"-d") 
filekeys["conv"]["diffbreaksoft"]=("S","LB",False,"-d") 
filekeys["conv"]["lowexp"]=("L","S",False,"LB") 
filekeys["conv"]["lowdiffbreak"]=("LB","L",False,"-d") 
filekeys["conv"]["lowdiffbreaksoft"]=("S","-",False,"LB") 
filekeys["conv"]["lowindx"]=("-li","b",False,False,"s")
filekeys["conv"]["lowbreak"]=("b","s",9.0,"-li")
filekeys["conv"]["lowsoft"]=("s","-",False,"-li")
filekeys["conv"]["convel"]=("-C","-",0.0,False)  


if __name__ == '__main__':
    sys.exit(main())    
