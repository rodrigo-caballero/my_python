#!/usr/bin/env python

import glob,os,sys
from numpy import *
from Scientific.IO.NetCDF import NetCDFFile
from mx.DateTime import *

Models = \
        """bccr_bcm2_0
        cccma_cgcm3_1
        cccma_cgcm3_1_t63
        cnrm_cm3
        csiro_mk3_0
        csiro_mk3_5
        gfdl_cm2_0
        gfdl_cm2_1
        giss_aom
        giss_model_e_h
        giss_model_e_r
        iap_fgoals1_0_g
        ingv_echam4
        inmcm3_0
        ipsl_cm4
        miroc3_2_hires
        miroc3_2_medres
        miub_echo_g
        mpi_echam5
        mri_cgcm2_3_2a
        ncar_ccsm3_0
        ncar_pcm1
        ukmo_hadcm3
        ukmo_hadgem1"""
Models = [s.strip() for s in Models.split('\n')]

class DataServer:

    def __init__(self, 
                 Field    = 'U', 
                 Model    = 'gfdl_cm2_1',  
                 Exp      = '20c3m',
                 Run      = 1,
                 LevRange = (0.,1000.), 
                 LatRange = (-90.,90.), 
                 LonRange = (0.,360.)   ):

        if Model in Models: self.Model = Model
        else: raise ValueError,'%s not a known source!'%Model

        # Initialize field names etc 
        self.FieldNames = {}
        self.FieldNames['time']   = 'time'
        self.FieldNames['lev']    = 'plev'
        self.FieldNames['lat']    = 'lat'
        self.FieldNames['lon']    = 'lon'
        self.FieldNames['U']      = 'ua'
        self.FieldNames['V']      = 'va'
        self.FieldNames['W']      = 'wap'
        self.FieldNames['ta']     = 'ta'
        self.FieldNames['ts']     = 'ts'
        self.FieldNames['temp']   = 'ta'
        self.FieldNames['U10']    = 'uas'
        self.FieldNames['V10']    = 'vas'
        self.FieldNames['cld']    = 'clt'
        self.FieldNames['rh']     = 'hur'
        self.FieldNames['slp']    = 'psl'
        self.FieldNames['taux']   = 'tauu'
        self.FieldNames['tauy']   = 'tauv'
        self.FieldNames['prec']   = 'pr'
        self.FieldNames['sst']    = 'tos'
        self.FieldNames['toalw']  = 'rlut'
        self.FieldNames['toanet'] = 'rtmt'
        self.Field = Field
        self.FieldName= self.FieldNames[Field]
            
        # open files
        self.Files = []
        FieldName = self.FieldNames[Field]
        self.Dir = '/Volumes/gordo/cmip3/%s/mo/%s/%s/run%s'% (Exp,FieldName,Model,Run)
        if not os.path.exists(self.Dir): raise ValueError, '%s does not exist!' % self.Dir
        FileNames = glob.glob(self.Dir+'/%s*.nc'%self.FieldNames[Field])        
        for FileName in FileNames: self.Files.append(NetCDFFile(FileName,'r'))

        # Initialize coord axes
        File = self.Files[-1]
        lat = File.variables[self.FieldNames['lat']][:]
        (self.lat, self.j0, self.j1, self.InvertLatAxis) = self._setupAxis(lat,LatRange)
        self.nlat = len(self.lat)
        lon = File.variables[self.FieldNames['lon']][:]
        (self.lon, self.i0, self.i1, self.InvertLonAxis) = self._setupAxis(lon,LonRange)
        self.nlon = len(self.lon)
        if 'plev' in File.variables.keys(): 
            lev = File.variables['plev'][:]
            if lev.max() > 2000.: lev = lev/100.
            (self.lev, self.k0, self.k1, self.InvertLevAxis) = self._setupAxis(lev,LevRange)
            self.nlev = len(self.lev)
        if 'lev' in File.variables.keys(): 
            lev = File.variables['lev'][:]
            p0 = File.variables['p0'].getValue()
            ps = File.variables['ps'][:,:,:].mean()
            a = File.variables['a'][:]
            b = File.variables['b'][:]
            lev = (a*p0 + ps*b)/100.
            (self.lev, self.k0, self.k1, self.InvertLevAxis) = self._setupAxis(lev,LevRange)
            self.nlev = len(self.lev)

        # Set fill value
        try:
            self.FillValue = File.variables[self.FieldName]._FillValue
        except: pass

        # Figure out which calendar to use
        self.calendar = File.variables['time'].calendar

        # Figure out year range
        YearStart = []
        YearStop  = []
        for File in self.Files:
            Year0 = self._getBaseYear(File)
            time = File.variables[self.FieldNames['time']][:]
            YearStart.append(self.getDate(time[0],Year0)[0])
            YearStop.append(self.getDate(time[-1],Year0)[0])
        YearStart = array(YearStart).min()
        YearStop = array(YearStop).max()
        self.Years = range(YearStart,YearStop+1)
        self.Year0 = 0

        # Print out info
        print 'Instantiated AR4 Monthly Mean Data Server'
        print 'Model: %s' % Model
        print 'Field: %s' % Field
        print 'Year range: %s-%s (%s years)' % (self.Years[0],self.Years[-1],self.Years[-1]-self.Years[0]+1)

    def _getBaseYear(self,File):
        # base year for time computation
        TimeUnits = File.variables[self.FieldNames['time']].units
        Year0 = TimeUnits.split()[2].split('-')[0]
        if len(Year0) != 4:
            Year0 = TimeUnits.split()[2].split('-')[-1]
        return int(Year0)

    def _setupAxis(self,axis,range):
        if axis[0] > axis[-1]:
            axis = axis[::-1]
            invert = True
        else: invert = False
        i0  = argmin(abs(axis-range[0]))
        i1  = argmin(abs(axis-range[1]))+1
        axis = axis[i0:i1]
        return axis,i0,i1,invert

    def closeFiles(self):
        for File in self.Files: File.close()
        
    def getDate(self, Days, Year0=None):
        # Given days elapsed since midnight on 1 January Year0,
        # returns date (year, month, day)
        Days = int(Days)
        if Year0 is None:
            Year0 = int(self.Year0)
        else:
            Year0 = int(Year0)
        if self.calendar == '360_day':
            Year  = Days/360
            Month = (Days - Year*360)/30 
            Day   = Days - Year*360 - Month*30 
            return Year+Year0, Month+1, Day+1
        elif self.calendar in ['365_day','noleap']:
            Year = Days/365
            DayInYear = Days-Year*365 + 1
            DaysInMonth = array([1,31,28,31,30,31,30,31,31,30,31,30,31])
            LowerBoundary = DaysInMonth[0:12].cumsum()
            UpperBoundary = DaysInMonth[1:13].cumsum()
            for Month in range(12):
                if DayInYear >= LowerBoundary[Month] and \
                   DayInYear <= UpperBoundary[Month]: break
            Day = DayInYear-LowerBoundary[Month]+1
            return Year+Year0, Month+1, Day
        elif self.calendar in ['standard','gregorian']:
            Date = DateTime(Year0) + DateTimeDelta(Days)
            return Date.year,Date.month,Date.day
        else: raise ValueError, 'Calendar %s unknown!'%self.calendar
        
    def getDays(self, Year, Month, Day, Year0=None):
        # Given date (year, month, day),
        # returns days elapsed since midnight on 1 January Year0
        Year = int(Year)
        Month = int(Month)
        Day = int(Day)
        if Year0 is None:
            Year0 = int(self.Year0)
        else:
            Year0 = int(Year0)
        if self.calendar == '360_day':            
            return (Year-Year0)*360 + (Month-1)*30 + Day-1
        elif self.calendar in ['365_day','noleap']:
            DaysInMonth = array([31,28,31,30,31,30,31,31,30,31,30,31])
            return (Year-Year0)*365 + DaysInMonth[0:Month-1].sum() + Day-1
        elif self.calendar in ['standard','gregorian']:
            Days = DateTime(Year,Month,Day,0).absdays \
                   - DateTime(Year0).absdays
            return Days
        else: raise ValueError, 'Calendar %s unknown!'%self.calendar

    def getMonthlyMean(self, Year=1958, Month=1):
        # find file
        for File in self.Files:
            Year0 = self._getBaseYear(File)
            now  = self.getDays(Year,Month,15,Year0) 
            time = File.variables[self.FieldNames['time']][:]
            y,m,d = self.getDate(time[0],Year0)
            start = self.getDays(y,m,1,Year0)
            y,m,d = self.getDate(time[-1],Year0)
            end = self.getDays(y,m,28,Year0)
            #print Year0, now, self.getDate(now,Year0)
            #print self.getDate(time[0],Year0),self.getDate(time[-1],Year0)
            if start <= now <= end:
                FoundFile = True
                break
            else:
                FoundFile = False
        if not FoundFile: raise ValueError,\
           '\nDate %s not found!\n' % str(self.getDate(now,Year0))
        # retrieve data
        l = argmin(abs(time-now))
        f = File.variables[self.FieldName][l]
        # swap axes if necessary and select slab
        if len(shape(f)) == 2:
            if self.InvertLatAxis: f = f[::-1,   :]
            if self.InvertLonAxis: f = f[:   ,::-1]
            f = f[self.j0:self.j1, self.i0:self.i1]
        else:
            if self.InvertLatAxis: f = f[:,::-1,:]
            if self.InvertLonAxis: f = f[:,:,::-1]
            if self.InvertLevAxis: f = f[::-1,:,:]
            f = f[self.k0:self.k1, self.j0:self.j1, self.i0:self.i1]
        # mask out missing values if necessary
        try:
            f = ma.array(f, mask=f==self.FillValue, fill_value=self.FillValue)
        except:
            pass
        # rescale if necessary
        try:
            scale = File.variables[self.FieldName].scale_factor
            offset = File.variables[self.FieldName].add_offset
            f = f*scale+offset
        except:
            pass
        # done
        return f

    def getSeasonalMean(self, Year=1959, Season='DJF'):
        # Return 1 season of data.
        assert Season in ['DJF','MAM','JJA','SON'],\
               "Season must be one of 'DJF','MAM','JJA','SON'"
        if Season == 'DJF': Months = [12,1,2]
        if Season == 'MAM': Months = [3,4,5]
        if Season == 'JJA': Months = [6,7,8]
        if Season == 'SON': Months = [9,10,11]
        Month = Months[0]
        if Month == 12:
            f = self.getMonthlyMean(Year-1,Month)
        else:
            f = self.getMonthlyMean(Year,Month)
        for Month in Months[1:]:
            ff = self.getMonthlyMean(Year,Month)
            f += self.getMonthlyMean(Year,Month)
        return f/3.

if __name__ == '__main__':
    for m in Models:
        try: d = DataServer(Exp='20c3m',Field='ts',Model=m,Run=1)
        except: pass
