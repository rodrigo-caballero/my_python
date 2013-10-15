from numpy import *
from scipy import stats

def regressWithConfInt(x,y,conf=0.05):
    a, b = stats.linregress(x,y)[0:2]
    n = len(x)
    err = y - (a*x+b)
    sig = sqrt( (err*err).sum()/(n-2) )
    sd_b = sig * sqrt(1./n + x.mean()**2/x.var()/(n-1)) 
    sd_a = sig * sqrt( 1./x.var()/(n-1) )
    t = stats.t(n-2) # students t
    percentile = 1.-conf/2.
    tp = t.ppf(percentile)
    err_a = sd_a*tp
    err_b = sd_b*tp
    return a,b,err_a,err_b
