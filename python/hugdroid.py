#!/usr/bin/python

import pylab
import math
import numpy
import time
import os
import subprocess


def execCmd(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while(True):
        retc = p.poll()
        line = p.stdout.readline()
        yield line
        if(retc is not None):
            break


def toxyY(X, Y, Z):
    return X/(X+Y+Z), Y/(X+Y+Z)

def getXYZ():
    
    dataout = [0]
    while len(dataout) != 5:
        dataout = list(execCmd(['colorhug-cmd', 'take-readings-xyz', '0']))
        if len(dataout) != 5:
            print 'retrying getXYZ()'
    
    X = float(dataout[2].split(' ')[0].split(':')[1])
    Y = float(dataout[2].split(' ')[1].split(':')[1])
    Z = float(dataout[2].split(' ')[2].split(':')[1])

    return X, Y, Z

def getXYZxy():
    dataout = list(execCmd(['colorhug-cmd', 'take-readings-xyz', '0']))
    
    X = float(dataout[2].split(' ')[0].split(':')[1])
    Y = float(dataout[2].split(' ')[1].split(':')[1])
    Z = float(dataout[2].split(' ')[2].split(':')[1])
    
    x, y = toxyY(X, Y, Z)
    
    return X, Y, Z, x, y

def setAndroidColor(R, G, B):
    #adb shell 'am start -n de.rbrune.hugdroid/.MainActivity -e color "#445566"'
    subprocess.call(['adb', 'shell', 'am', 'start', '-n', 'de.rbrune.hugdroid/.MainActivity', '-e', 'color', '"#%02x%02x%02x"' % (round(R*2.55), round(G*2.55), round(B*2.55)), "--activity-clear-top", '>/dev/null'])
    time.sleep(0.750)

def setAndroidBrightness(brightness):
    # adb shell 'am start -n de.rbrune.hugdroid/.MainActivity -e brightness "0.5"'
    subprocess.call(['adb', 'shell', 'am', 'start', '-n', 'de.rbrune.hugdroid/.MainActivity', '-e', 'brightness', '"%f"' % (brightness), "--activity-clear-top", '>/dev/null'])
    time.sleep(0.750)


def setAndroidWhitePoint(R, G, B):
    # shell@android:/sys/devices/platform/kcal_ctrl.0 # echo 255 155 255 > kcal
    #shell@android:/sys/devices/platform/kcal_ctrl.0 $ echo 255 55 75 > kcal        
    #shell@android:/sys/devices/platform/kcal_ctrl.0 $ echo 1 >  kcal_ctrl
    subprocess.call(['adb', 'shell', 'echo', '%d %d %d' % (R,G,B), '>', '/sys/devices/platform/kcal_ctrl.0/kcal'])
    subprocess.call(['adb', 'shell', 'echo', '1', '>', '/sys/devices/platform/kcal_ctrl.0/kcal_ctrl'])
    time.sleep(0.750)

def gammaChksum(tmpg):
    chk=0
    for i in range(len(tmpg)-1):
        chk += tmpg[i+1]
    chk = chk % 256
    return chk

def setAndroidGamma(gR, gG, gB):
    gR[0] = gammaChksum(gR)
    gG[0] = gammaChksum(gG)
    gB[0] = gammaChksum(gB)
    subprocess.call(['adb', 'shell', 'echo', '%d %d %d %d %d %d %d %d %d %d' % (gR[0], gR[1], gR[2], gR[3], gR[4], gR[5], gR[6], gR[7], gR[8], gR[9]), '>', '/sys/devices/platform/mipi_lgit.1537/kgamma_r'])
    subprocess.call(['adb', 'shell', 'echo', '%d %d %d %d %d %d %d %d %d %d' % (gG[0], gG[1], gG[2], gG[3], gG[4], gG[5], gG[6], gG[7], gG[8], gG[9]), '>', '/sys/devices/platform/mipi_lgit.1537/kgamma_g'])
    subprocess.call(['adb', 'shell', 'echo', '%d %d %d %d %d %d %d %d %d %d' % (gB[0], gB[1], gB[2], gB[3], gB[4], gB[5], gB[6], gB[7], gB[8], gB[9]), '>', '/sys/devices/platform/mipi_lgit.1537/kgamma_b'])
    #subprocess.call(['adb', 'shell', 'am', 'start', '-n', 'de.rbrune.hugdroid/.MainActivity', '-e', 'sleep', '"now"'])
    subprocess.call(['adb', 'shell', 'input', 'keyevent', '26'])
    time.sleep(1.0)

def Labf(t):
    if t > math.pow(6.0/29.0, 3.0):
        return math.pow(t, 1.0/3.0)
    return (1.0/3.0)*math.pow(29.0/6.0, 2.0)*t + 4.0/29.0
    
def toLab(X, Y, Z, Xn, Yn, Zn):
    L = 116.0*Labf(Y/Yn) - 16.0
    a = 500.0*(Labf(X/Xn) - Labf(Y/Yn))
    b = 200.0*(Labf(Y/Yn) - Labf(Z/Zn))
    return L, a, b

def distLab(xL, xa, xb, yL, ya, yb):
    return math.sqrt(math.pow(xL-yL, 2.0) + math.pow(xa-ya, 2.0) + math.pow(xb-yb, 2.0))


def measurePatch(chart, whiteind, ind):
    wR, wG, wB, wX, wY, wZ = chart[whiteind]    
    R, G, B, tX, tY, tZ = chart[ind]    
    setAndroidColor(R, G, B)
    X, Y, Z = getXYZ()
    tL, ta, tb = toLab(tX, tY, tZ, wX, wY, wZ)
    L, a, b = toLab(X, Y, Z, wX, wY, wZ)

    return distLab(L, a, b, tL, ta, tb)

def parseTi1():
    fp = open("D6500-2.2.ti1")
    chart = []
    go = 0
    for line in fp:
        if line == 'END_DATA':
            go = 0

        if go == 1:
            dataraw = line.split(' ')
            R = float(dataraw[1])
            G = float(dataraw[2])
            B = float(dataraw[3])
            X = float(dataraw[4])
            Y = float(dataraw[5])
            Z = float(dataraw[6])
            chart.append([R, G, B, X, Y, Z])

        if line == 'BEGIN_DATA\n':
            go = 1
    fp.close()
    return chart



def profile():
    
    pylab.figure()
    pylab.ion()
    
    for i, ccol in enumerate(chart):
        R, G, B, tX, tY, tZ = ccol
        tx, ty = toxyY(tX, tY, tZ)
        
        setAndroidColor(R, G, B)
        
        X, Y, Z, x, y = getXYZxy()
        
        print i, len(chart)
        print R, G, B, tX, tY, tZ, X, Y, Z
        
        pylab.plot(tx, ty, 'go')
        pylab.plot(x, y, 'rx')
        pylab.xlim([0, 0.8])
        pylab.ylim([0, 0.9])
        pylab.axis('scaled')
        pylab.draw()
        pylab.show()
        
    
    pylab.ioff()
    pylab.show()



def measurePatchRange(chart, whiteind, minind, maxind):
    error = 0
    for i in range(minind, maxind):
        
        newerror = measurePatch(chart, whiteind, i)
        print minind, i, maxind, newerror
        error += newerror

    return error


def djbhash(a):
    h = 5381L
    for i in a:
        t = (h * 33) & 0xffffffffL
        h = t ^ i
    return h

def setPresetLG():
    setAndroidBrightness(40.0/255.0)
    setAndroidWhitePoint(255, 255, 255)
    setAndroidGamma(gammaLG_r, gammaLG_g, gammaLG_b)

def setPresetGoogle():
    setAndroidBrightness(40.0/255.0)
    setAndroidWhitePoint(255, 255, 255)
    setAndroidGamma(gammaGO_r, gammaGO_g, gammaGO_b)

def setPresetParanoid():
    setAndroidBrightness(48.0/255.0)
    setAndroidWhitePoint(245, 244, 240)
    setAndroidGamma(gammaPA_r, gammaPA_g, gammaPA_b)

def setOptValues(tgamma):
    #use value [0] as brightness
    print(tgamma)
    brightness = tgamma[0]
    setAndroidBrightness(brightness/255.0)
    setAndroidGamma(tgamma, tgamma, tgamma)
    tgamma[0] = brightness
    

hashdict = {}

def setAndMeasure(tgamma, chart, whiteind, minind, maxind):
    ngammavec = [tgamma[0], tgamma[1] + tgamma[2]*16, tgamma[3] + tgamma[4]*16, tgamma[5] + tgamma[6]*16, tgamma[7] + tgamma[8]*16, tgamma[9] + tgamma[10]*16, tgamma[11] + tgamma[12]*16, tgamma[13] + tgamma[14]*16, tgamma[15] + tgamma[16]*16, tgamma[17] + tgamma[18]*16]
    hsh = djbhash(ngammavec)
    if hsh in hashdict:
        return hashdict[hsh]
    setOptValues(ngammavec)
    err = measurePatchRange(chart, whiteind, minind, maxind)
    hashdict[hsh] = err
    return err


gammaLG_r = [208, 114,  21, 118,   0,   0,   0,  80,  48,   2]
gammaLG_g = [210, 114,  21, 118,   0,   0,   0,  80,  48,   2]
gammaLG_b = [212, 114,  21, 118,   0,   0,   0,  80,  48,   2]

gammaGO_r = [208,  64,  44, 118,   1,   0,   0,  48,  32,   1]
gammaGO_g = [210,  64,  44, 118,   1,   0,   0,  48,  32,   1]
gammaGO_b = [212,  32,  35, 116,   0,  31,  16,  80,  51,   3]


gammaPA_r = [208,  64,  68, 118,   0,  26,   0,  72,  48,   2]
gammaPA_g = [210,  64,  68, 118,   0,  26,   0,  72,  48,   2]
gammaPA_b = [212,  64,  68, 118,   0,  26,   0,  72,  48,   2]


#gamma_min = [  1,  32,  21, 116,   0,   0,   0,  48,  32,   1]
#gamma_max = [255, 114,  68, 118,   1,  31,  16,  80,  51,   3]

#gamma_step= [  4,   2,   2,   1,   1,   1,   1,   2,   2,   1]

gamma_min = [  1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
gamma_max = [255,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15]
gamma_step= [  4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

# seems to be necessary at times before reading xyz works
subprocess.call(['colorhug-cmd', 'take-reading-array', '>/dev/null'])

    
chart = parseTi1()

#setAndroidBrightness(40.0/255.0)
#setPresetLG()
#gamma_opt = [ 36, 114,  29, 118,   0,   1,   0,  76,  48,   2]
#setOptValues(gamma_opt)
#profile()



def optimize():
    max_patch = len(chart)
    #max_patch = 12
    #from min
    #gamma_opt = [  72,  46,  23, 118,   1,   5,   4,  52,  32,   1]
    #lg
    #gamma_opt = [ 40, 114,  21, 118,   0,   0,   0,  80,  48,   2]
    #from lg
    gamma_opt = [ 48, 112,  25, 117,   0,   1,   0,  76,  48,   2]
    gamma_opt = [44, 14, 4, 6, 6, 7, 1, 0, 0, 8, 0, 4, 0, 2, 0, 0, 0, 1, 0]
    #setOptValues(gamma_opt)
    #curerror = measurePatchRange(chart, 0, 0, max_patch)
    curerror = setAndMeasure(gamma_opt, chart, 0, 0, max_patch)
    while curerror > max_patch*10:
        
        for curind in range(1, 19):
            curdir = 1
            hitminmax = 0
            dirimp = 0
            while curdir != 0:
                
                print gamma_opt
                gamma_opt[curind] += curdir * gamma_step[curind]
                if gamma_opt[curind] > gamma_max[curind]:
                    gamma_opt[curind] = gamma_max[curind]
                    hitminmax = 1
                if gamma_opt[curind] < gamma_min[curind]:
                    gamma_opt[curind] = gamma_min[curind]
                    hitminmax = 1
                print gamma_opt
                
                #setOptValues(gamma_opt)
                #newerror = measurePatchRange(chart, 0, 0, max_patch)
                newerror = setAndMeasure(gamma_opt, chart, 0, 0, max_patch)
                print newerror
                
                
                if newerror < curerror:
                    curerror = newerror
                    dirimp = 1
                    if hitminmax==1:
                        curdir = 0
                else:
                    if hitminmax==0:
                        gamma_opt[curind] -= curdir * gamma_step[curind]
                    
                    if curdir == 1:
                        curdir = -1
                        if dirimp == 1:
                            curdir = 0
                    else:
                        curdir = 0
                
                print "--------------------------------------------------------"
                print curind
                print gamma_opt
                print curerror
                print "--------------------------------------------------------"


optimize()
#profile()
#print measurePatchRange(chart, 0, 0, 12)

#print measurePatchRange(chart, 0, 0, len(chart))

def findBrightness():
    brightness = 64
    setAndroidBrightness(brightness/255.0)
    curerror = measurePatchRange(chart, 0, 0, 2)
    ldir = 4
    while ldir != 0:
        brightness += ldir
        
        if brightness > 255 or brightness < 1:
            error = 2*curerror
        else:
            setAndroidBrightness(brightness/255.0)
            error = measurePatchRange(chart, 0, 0, 2)
    
        if error < curerror:
            curerror = error
        else:
            brightness -= ldir
            if ldir > 0:
                ldir = -4
            else:
                ldir = 0
                
        print 'current:', brightness, curerror


#findBrightness()





