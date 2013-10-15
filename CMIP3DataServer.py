#!/usr/bin/env python

import sys,glob
from numpy import *
from netCDF4 import Dataset as NetCDFFile
import datetime
from progress import ProgressMeter

class DataServer:

    def __init__(self, 
                 Field    = 'U', 
                 Source   = 'inmcm3_0',  
                 Scenario = '20c3m',
                 LevRange = (0.,1000.), 
                 LatRange = (-90.,90.), 
                 LonRange = (0.,360.)   ):

        Sources = [
         'bcc_cm1',
         'bccr_bcm2_0',
         'cccma_cgcm3_1',
         'cccma_cgcm3_1_t63',
         'cnrm_cm3',
         'csiro_mk3_0',
         'csiro_mk3_5',
         'gfdl_cm2_0',
         'gfdl_cm2_1',
         'giss_aom',
         'giss_model_e_h',
         'giss_model_e_r',
         'iap_fgoals1_0_g',
         'ingv_echam4',
         'inmcm3_0',
         'ipsl_cm4',
         'miroc3_2_hires',
         'miroc3_2_medres',
         'miub_echo_g',
         'mpi_echam5',
         'mri_cgcm2_3_2a',
         'ncar_ccsm3_0',
         'ncar_pcm1',
         'ukmo_hadcm3',
         'ukmo_hadgem1']

        if Source in Sources: self.Source = Source
        else: raise ValueError,'%s not a known source!'%Source

        # Initialize field names etc 
        self.FieldNames = {}
        self.FieldNames['time'] = 'time'
        self.FieldNames['lev'] = 'plev'
        self.FieldNames['lat'] = 'lat'
        self.FieldNames['lon'] = 'lon'
        self.FieldNames['U'] = 'ua'
        self.FieldNames['V'] = 'va'
        self.FieldNames['uas'] = 'uas'
        self.FieldNames['vas'] = 'vas'
        self.Field = Field
        self.FieldName= self.FieldNames[Field]
            
        # open files
        self.Files = []
        self.Dir = '/Volumes/gordo/cmip3/%s/atm/da/%s/%s'% \
                   (Scenario,self.FieldNames[Field],Source)
        FileNames = glob.glob(self.Dir+'/*.nc')        
        for FileName in FileNames:
            #print FileName
            self.Files.append(NetCDFFile(FileName,'r'))

        # Initialize coord axes
        File = self.Files[0]
        lat = File.variables[self.FieldNames['lat']][:]
        (self.lat, self.j0, self.j1, self.InvertLatAxis) = \
                   self._setupAxis(lat,LatRange)
        self.nlat = len(self.lat)
        lon = File.variables[self.FieldNames['lon']][:]
        (self.lon, self.i0, self.i1, self.InvertLonAxis) = \
                   self._setupAxis(lon,LonRange)
        self.nlon = len(self.lon)
        try:
            lev = File.variables[self.FieldNames['lev']][:]/100.
            (self.lev, self.k0, self.k1, self.InvertLevAxis) = \
                       self._setupAxis(lev,LevRange)
            self.nlev = len(self.lev)
        except:
            pass

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
            TimeUnits = File.variables[self.FieldNames['time']].units
            Year0 = int(TimeUnits.split()[2][0:4])
            time = File.variables[self.FieldNames['time']][:]
            YearStart.append(self.getDate(time[0],Year0)[0])
            YearStop.append(self.getDate(time[-1],Year0)[0])
        YearStart = array(YearStart).min()
        YearStop = array(YearStop).max()
        self.Years = range(YearStart,YearStop+1)
        self.Year0 = 1

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
            Date = datetime.datetime(Year0,1,1,0) + datetime.timedelta(Days)
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
            Days = (datetime.datetime(Year,Month,Day,0) - datetime.datetime(Year0,1,1,0)).days
            return Days
        else: raise ValueError, 'Calendar %s unknown!'%self.calendar

    def getNdaysInMonth(self, Year, Month):
        if self.calendar == '360_day':            
            return 30
        elif self.calendar in ['365_day','noleap']:            
            DaysInMonth = array([31,28,31,30,31,30,31,31,30,31,30,31])
            return DaysInMonth[int(Month)-1]
        elif self.calendar in ['standard','gregorian']:
            if Month==12:
                Ndays = 31
            else:
                h1 = self.getDays(Year,Month  ,1)
                h2 = self.getDays(Year,Month+1,1)
                Ndays = int((h2-h1))
            return Ndays
        else: raise ValueError, 'Calendar %s unknown!'%self.calendar

    def getDateList(self, Year=None, Month=None, Day=None, Season=None):
        if Year is not None:
            if Month is not None:
                if Day is not None:
                        Nsnapshots = 1
                        h = self.getDays(Year,Month,Day)
                else:
                    Nsnapshots = self.getNdaysInMonth(Year,Month)
                    h = self.getDays(Year,Month,1)
            if Season is not None:
                if Season == 'DJF':
                    Months = [12,1,2]
                    h = self.getDays(Year-1,12,1)
                if Season == 'MAM':
                    Months = [3,4,5]
                    h = self.getDays(Year,3,1)
                if Season == 'JJA':
                    Months = [6,7,8]
                    h = self.getDays(Year,6,1)
                if Season == 'SON':
                    Months = [9,10,11]
                    h = self.getDays(Year,9,1)
                Nsnapshots = 0
                for Month in Months:
                    Nsnapshots += self.getNdaysInMonth(Year,Month)
        Dates = []
        for i in range(Nsnapshots):
            Dates.append( self.getDate(h) )
            h += 1.
        return Dates

    def snapshot(self, Year=1958, Month=1, Day=1):
        # find file
        for File in self.Files:
            TimeUnits = File.variables[self.FieldNames['time']].units
            Year0 = int(TimeUnits.split()[2][0:4])
            now  = self.getDays(Year,Month,Day,Year0) + 0.5
            time = File.variables[self.FieldNames['time']][:]
            if now in time:
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
        if len(f.shape) == 2:
            if self.InvertLatAxis: f = f[::-1,:]
            if self.InvertLonAxis: f = f[:,::-1]
            f = f[self.j0:self.j1, self.i0:self.i1]
        if len(f.shape) == 3:
            if self.InvertLatAxis: f = f[:,::-1,:]
            if self.InvertLonAxis: f = f[:,:,::-1]
            try:
                if self.InvertLevAxis: f = f[::-1,:,:]
            except:
                pass
            f = f[self.k0:self.k1, self.j0:self.j1, self.i0:self.i1]
        # mask out missing values if necessary
        try: f = ma.array(f, mask=f==self.FillValue, fill_value=self.FillValue)
        except: pass
        # rescale if necessary
        try:
            scale = File.variables[self.FieldName].scale_factor
            offset = File.variables[self.FieldName].add_offset
            f = f*scale+offset
        except:
            pass
        # done
        return f


if __name__ == '__main__':
    d = DataServer(Field='uas',Source='ingv_echam4')
    dates = d.getDateList(Year=1962,Season='DJF')    
    print dates
    print d.snapshot(*dates[0])
