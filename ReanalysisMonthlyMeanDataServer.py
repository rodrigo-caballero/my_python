#!/usr/bin/env python

import os,sys
from numpy import *
from netCDF4 import Dataset as NetCDFFile
from progress import ProgressMeter
import time,datetime

HomeDir = os.getenv('HOME')

class DataServer:
    def __init__(self,
                 Field='U',
                 Source='ERA40'):
        
        self.FieldNames = {}
        if Source == 'ERA40':
            self.FieldNames['time']   = 'time'
            self.FieldNames['lev']    = 'lev'
            self.FieldNames['lat']    = 'lat'
            self.FieldNames['lon']    = 'lon'
        if Source == 'ERAInt':
            self.FieldNames['time']   = 'time'
            self.FieldNames['lev']    = 'lev'
            self.FieldNames['lat']    = 'latitude'
            self.FieldNames['lon']    = 'longitude'

        # open monthly mean file
        if Source == 'hadslp':
            self.File = NetCDFFile(HomeDir+'/obs/slp/HadSLP2/hadslp2.mon.mean.nc','r')
        else:
            self.File = NetCDFFile(HomeDir+'/obs/%s/monthly/%s.mon.mean.nc'\
                                   %(Source,Field),'r')
        self.FieldName = Field
        self.Field = self.File.variables[Field]
        # base year for time computation
        self.Year0 = self._getBaseYear(self.File)
        # time axis
        self.time = self.File.variables['time'][:]
        self.FirstYear = self.getDate(self.time[0])[0]
        self.LastYear  = self.getDate(self.time[-1])[0]
        # Print out info
        print 'Instantiated Reanalysis Monthly Mean Data Server'
        print 'Data source: %s' % Source
        print 'Field: %s' % Field
        print 'Year range: %s-%s (%s years)' %\
              (self.FirstYear,self.LastYear,self.LastYear-self.FirstYear+1)

        # Initialize coord axes
        lat = array(self.File.variables[self.FieldNames['lat']][:])*1.
        lat,self.InvertLatAxis = self._setupAxis(lat)
        lon = array(self.File.variables[self.FieldNames['lon']][:])*1.
        lon,self.InvertLonAxis = self._setupAxis(lon)
        try:
            lev = array(self.File.variables[self.FieldNames['lev']][:])*1.
            lev,self.InvertLevAxis = self._setupAxis(lev)
        except:
            pass

    def _setupAxis(self,axis):
        if axis[0] > axis[-1]:
            axis = axis[::-1]
            invert = True
        else: invert = False
        return axis,invert
        
    def getDate(self,Hours):
        # Given hours elapsed since midnight on 1 January Year0,
        # returns date (year, month, day, hour) 
        Date = datetime.datetime(self.Year0,1,1,0) + datetime.timedelta(Hours/24.)
        return Date.year,Date.month,Date.day,Date.hour

    def getHours(self,Year,Month,Day,Hour):
        # Given date (year, month, day, hour),

        # returns hours elapsed since midnight on 1 January Year0
        Days = datetime.datetime(Year,Month,Day,Hour) \
               - datetime.datetime(self.Year0,1,1,0)
        Hours = Days.days*24 + Days.seconds/3600
        return Hours

    def getMonth(self, Year, Month):
        # Return 1 month of data.
        assert self.FirstYear <= Year <= self.LastYear, \
               'Year %s not in dataset !!' % Year
        h = self.getHours(Year,Month,5,0)
        i = argmin(abs(self.time-h))
        ## try:
        ##     scale = self.Field.scale_factor
        ##     offset = self.Field.add_offset
        ##     x = self.Field[i]*scale+offset
        ## except:
        f = self.Field[i]
        # swap axes if necessary
        if len(f.shape) == 2:
            if self.InvertLatAxis: f = f[::-1,:]
            if self.InvertLonAxis: f = f[:,::-1]
        if len(f.shape) == 3:
            if self.InvertLatAxis: f = f[:,::-1,:]
            if self.InvertLonAxis: f = f[:,:,::-1]
            try:
                if self.InvertLevAxis: f = f[::-1,:,:]
            except:
                pass
        return f

    def getMonthlyClimatology(self,Month):
        f = []
        for Year in range(self.FirstYear,self.LastYear+1):
            f.append(self.getMonth(Year,Month))
        if hasattr(f[0],'mask'):
            return ma.array(f).mean(axis=0)
        else:
            return array(f).mean(axis=0)

    def getSeason(self, Year, Season):
        # Return 1 season of data.
        assert Season in ['DJF','MAM','JJA','SON'],\
               "Season must be one of 'DJF','MAM','JJA','SON'"
        if Season == 'DJF': Months = [12,1,2]
        if Season == 'MAM': Months = [3,4,5]
        if Season == 'JJA': Months = [6,7,8]
        if Season == 'SON': Months = [9,10,11]
        f = []
        for Month in Months:
            if Month == 12: x = self.getMonth(Year-1,Month)
            else:           x = self.getMonth(Year,Month)
            f.append(x)
        if hasattr(f[0],'mask'):
            return ma.array(f).mean(axis=0)
        else:
            return array(f).mean(axis=0)

    def getSeasonalClimatology(self,Season):
        f = []
        if Season == 'DJF':
            FirstYear = self.FirstYear+1
        else:
            FirstYear = self.FirstYear
        for Year in range(FirstYear,self.LastYear+1):
            f.append(self.getSeason(Year,Season))
        if hasattr(f[0],'mask'):
            return ma.array(f).mean(axis=0)
        else:
            return array(f).mean(axis=0)

    def _getBaseYear(self,File):
        # base year for time computation
        TimeUnits = File.variables[self.FieldNames['time']].units
        Year0 = TimeUnits.split()[2].split('-')[0]
        if len(Year0) != 4:
            Year0 = TimeUnits.split()[2].split('-')[-1]
        return int(Year0)


def CreateOutputFile(FileName,data):
    # Create file
    File = NetCDFFile(FileName,'w')
    # Define some global attribs
    File.Conventions='COARDS'
    # Time is record dimension
    File.createDimension('time',None)
    var = File.createVariable('time','d',('time',))
    var.long_name = 'time'
    var.units = 'year'
    # axes
    try:
        File.createDimension('level',data.File.dimensions['level'])
        var = File.createVariable('level','f',('level',))
        var.long_name = 'pressure level'
        var.units = 'mb'
        var[:] = data.File.variables['level'][:].astype('f')
    except: pass
    File.createDimension('lat',data.File.dimensions['lat'])
    var = File.createVariable('lat','f',('lat',))
    var.long_name = 'latitude'
    var.units = 'degrees_north'
    var[:] = data.File.variables['lat'][:]
    File.createDimension('lon',data.File.dimensions['lon'])
    var = File.createVariable('lon','f',('lon',))
    var.long_name = 'longitude'
    var.units = 'degrees_east'
    var[:] = data.File.variables['lon'][:]
    # create variables
    var = File.createVariable(Field,'f',\
                                  data.Field.dimensions)
    var.long_name = data.Field.long_name
    var.units = data.Field.units
    return File

def Seasonal(Field='U', Season='DJF', Source='ERA40', \
             YearStart=None, YearStop=None):
    # instatiate data server
    data = DataServer(Field=Field,Source=Source)
    if YearStart is None: YearStart = data.FirstYear
    if YearStop is None: YearStop = data.LastYear
    assert YearStart >= data.FirstYear,\
                       '\nFirst year in dataset is %s' % data.FirstYear
    assert YearStop <= data.LastYear,\
                       '\nLast year in dataset is %s' % data.LastYear
    # create output file
    FileName = '%s.%s.%s.%s-%s.nc' % (Field,Season,Source,YearStart,YearStop)
    File = CreateOutputFile(FileName,data)
    print 'Creating %s'%FileName
    TimeIndex = 0
    meter = ProgressMeter(total=YearStop-YearStart+1)
    for Year in range(YearStart,YearStop+1):
        meter.update(1)
        # get 1 season of data
        SeasonData = data.getSeason(Year,Season)
        File.variables['time'][TimeIndex]  = float(Year)
        File.variables[Field][TimeIndex] = SeasonData.astype('f')
        TimeIndex += 1
    File.close()

if __name__ == "__main__":
    for Season in ['DJF']:  
        for Field in ['slp']:
            Seasonal(Field=Field, Season=Season, Source='ERA40', \
                     YearStart=1959, YearStop=2001)


