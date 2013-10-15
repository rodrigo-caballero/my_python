#!/usr/bin/env python

from numpy import *
from netCDF4 import Dataset as NetCDFFile
from interpol import vinterpol

class DataServer:

    def __init__(self, FileName):
        #  Open file
        self.File = NetCDFFile(FileName,'r') 
        #  Extract hybrid coord coefficients and ref press
        self.hyam = self.File.variables["hyam"][:]
        self.hybm = self.File.variables["hybm"][:]
        self.hyai = self.File.variables["hyai"][:]
        self.hybi = self.File.variables["hybi"][:]
        self.p0 = self.File.variables['P0'].getValue()
        # Extract lat, lon, time
        self.lat = self.File.variables['lat'][:]
        self.lon = self.File.variables['lon'][:]
        self.time = self.File.variables['time'][:]
        self.lev = self.File.variables['lev'][:]
        
    def getData(self,Field,l):
        # retrieve field at time l 
        if Field == 'p':
            ps  = self.File.variables['PS'][l]
            x = (self.hyam[:,None,None]*self.p0 + \
                 self.hybm[:,None,None]*ps[None,:,:])/100.
        elif Field == 'dp':
            ps  = self.File.variables['PS'][l]
            x = (self.hyai[:,None,None]*self.p0 + \
                 self.hybi[:,None,None]*ps[None,:,:])/100.
            x = x[1:,:,:] - x[:-1,:,:]
        else:
            x  = self.File.variables[Field][l]
        return x

    def getDataOnPressLevs(self,Field,lstart,p,lend=None,Extrapolate=False,FillValue=1.e20):
        if lend is None: lend = lstart
        x  = self.File.variables[Field][lstart:lend+1,:,:,:]
        ps = self.File.variables['PS'][lstart:lend+1,:,:]
        xi = []
        for l in range(0,lend-lstart+1):
            xi.append(self.hybToPress(x[l],p,ps[l],Extrapolate,FillValue))
        xi = array(xi)
        return ma.array(xi, mask = xi==FillValue).squeeze()

    def hybToPress(self,x,pnew,ps,Extrapolate,FillValue):
        # interpolate from hybrid levels to pressure levels p
        p = (self.hyam[:,None,None]*self.p0 + \
             self.hybm[:,None,None]*ps[None,:,:])/100.
        pnew = pnew[:,None,None] + ps[None,:,:]*0.
        xnew = vinterpol(p,x,pnew,Extrapolate=Extrapolate,FillValue=FillValue)
        return xnew

    def close(self):
        self.File.close()
