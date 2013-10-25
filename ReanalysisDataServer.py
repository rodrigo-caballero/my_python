#!/usr/bin/env python

import os,sys,glob
from numpy import *
from netCDF4 import Dataset
import time,datetime
from interpol import vinterpol
from progress import ProgressMeter

ObsDir = '/qnap/obs'

class DataServer:
    def __init__(self, 
                 Field    = 'U', 
                 Source   = 'ERAInt',
                 LevType  = None,
                 HybToPress = True,
                 PLevs    = None,
                 LevRange = (0.,1000.), 
                 LatRange = (-90.,90.), 
                 LonRange = (0.,360.)   ):

        if Source[0:3] == 'ERA':
            # list of all data holdings
            FieldNames = {}
            FieldNames['time']  = ['time','coord']
            FieldNames['lev']   = ['levelist','coord']
            FieldNames['lat']   = ['latitude','coord']
            FieldNames['lon']   = ['longitude','coord']
            FieldNames['U']     = ['u','plev']
            FieldNames['V']     = ['v','plev']
            FieldNames['W']     = ['w','plev']
            FieldNames['Z']     = ['z','plev']
            FieldNames['T']     = ['t','plev']
            FieldNames['q']     = ['q','plev']
            FieldNames['lnsp']  = ['lnsp','modlev']
            FieldNames['slp']   = ['msl','surface_analysis']
            FieldNames['T2']    = ['t2m','surface_analysis']
            FieldNames['TS']    = ['skt','surface_analysis']
            FieldNames['U10']   = ['u10','surface_analysis']
            FieldNames['V10']   = ['v10','surface_analysis']
            FieldNames['pw']    = ['tcw','surface_analysis']
            FieldNames['pwv']   = ['tcwv','surface_analysis']
            FieldNames['cld']   = ['cld','surface_analysis']
            FieldNames['ci']    = ['ci','surface_analysis']
            FieldNames['precc'] = ['cp','surface_forecast']
            FieldNames['precl'] = ['lsp','surface_forecast']
            FieldNames['flds']  = ['strd','surface_forecast']
            FieldNames['flns']  = ['str','surface_forecast']
            # set up field name and directory
            self.Field = Field
            self.FieldName = FieldNames[Field][0]
            if LevType is None:
                self.LevType = FieldNames[Field][1]
            else:
                self.LevType = LevType
            Dir = ObsDir+'/%s/6hourly/%s/%s'%(Source,self.LevType,self.FieldName)
            # dictionary of files
            Handles = [Dataset(Name,'r') for Name in glob.glob(Dir+'/*')]
            Times   = [Handle.variables['time'][:] for Handle in Handles]
            self.Files = dict(zip(range(len(Handles)),Handles))
            self.Times = dict(zip(range(len(Times)),Times))
            # base year for time computation
            self.time_units = Handles[0].variables['time'].units
            Year0 = self.time_units.split()[2]
            self.Year0 = Year0.split('-')[0]
            if len(self.Year0) != 4: self.Year0 = Year0.split('-')[-1]
            self.Year0 = int(self.Year0)
            # period covered
            self.MinHour = array([Time[0] for Time in Times]).min()
            self.MaxHour = array([Time[-1] for Time in Times]).max()
            self.MinDate = self.getDate(self.MinHour)
            self.MaxDate = self.getDate(self.MaxHour)
            print 'DataServer: Setting up, data from ',Dir
            #print 'DataServer: spanning ',self.MinDate,' to ',self.MaxDate
            # set up interpolation from hybrid to pressure coords if needed
            self.Interpolate = False
            if self.LevType =='modlev':
                d = Dataset(ObsDir+'/ERAInt/ERA-Interim_coordvars.nc','r')
                self.hyam = d.variables['a_model_alt'][:]
                self.hybm = d.variables['b_model_alt'][:]
                d.close()
                self.FillValue = 1.e20
                if PLevs is None:
                    self.p = (self.hyam+self.hybm*105000.)/100.
                else:
                    self.p = PLevs
                if HybToPress:
                    self.Interpolate = True
                    self.ps_data = DataServer(Field='lnsp',Source=Source, \
                                              LevType='modlev',HybToPress=False)                
                
        elif Source == 'NCEP':
            ########## NEEDS UPDATING !!
            self.Year0 = 1
            self.Years = range(1948,2007)
            self.Storage = 'ByYear'
            FieldNames = {}
            FieldNames['time'] = 'time'
            FieldNames['lev'] = 'level'
            FieldNames['lat'] = 'lat'
            FieldNames['lon'] = 'lon'
            FieldNames['U'] = 'uwnd'
            FieldNames['V'] = 'vwnd'
            FieldNames['W'] = 'omega'
            FieldNames['T'] = 'air'
            Dir = ObsDir+'/obs/NCEP/6hourly/%s'% FieldNames[Field]
            self.Files = {}        
            for Year in self.Years:
                FileName = '%s/%s.%s.nc' % \
                           (Dir,FieldNames[Field],Year)
                self.Files[Year] =  NetCDFFile(FileName,'r')

        else: raise ValueError, 'Source %s not known!'%Source

        # Initialize field
        self.units = Handles[0].variables[self.FieldName].units
        self.long_name = Handles[0].variables[self.FieldName].long_name

        # Initialize coord axes
        lat = array(Handles[0].variables[FieldNames['lat'][0]][:])*1.
        (self.lat, self.j0, self.j1, self.InvertLatAxis) = \
                   self._setupAxis(lat,LatRange)
        self.nlat = len(self.lat)
        lon = array(Handles[0].variables[FieldNames['lon'][0]][:])*1.
        (self.lon, self.i0, self.i1, self.InvertLonAxis) = \
                   self._setupAxis(lon,LonRange)
        self.nlon = len(self.lon)
        try:
            lev = array(Handles[0].variables[FieldNames['lev'][0]][:])*1.
            (self.lev, self.k0, self.k1, self.InvertLevAxis) = \
                       self._setupAxis(lev,LevRange)
            self.nlev = len(self.lev)
        except:
            pass

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
        for File in self.Files.values(): File.close()
        
    def getDate(self,Hours):
        # Given hours elapsed since midnight on 1 January Year0,
        # returns date (year, month, day, hour) 
        Date = datetime.datetime(self.Year0,1,1,0) + datetime.timedelta(Hours/24.)
        return Date.year,Date.month,Date.day,Date.hour

    def getHours(self,Year,Month,Day,Hour):
        # Given date (year, month, day, hour),
        # returns hours elapsed since midnight on 1 January Year0
        Days = datetime.datetime(int(Year),int(Month),int(Day),int(Hour)) \
               - datetime.datetime(self.Year0,1,1,0)
        Hours = Days.days*24 + Days.seconds/3600
        return Hours
    
    def getNdaysInMonth(self,Year,Month):
        if Month==12:
            Ndays = 31
        else:
            h1 = self.getHours(Year,Month  ,1,0)
            h2 = self.getHours(Year,Month+1,1,0)
            Ndays = int((h2-h1)/24)
        return Ndays

    def getDateList(self,Year=None, Month=None, Day=None, Hour=None, \
                    Season=None):
        if Year is not None:
            if Month is not None:
                if Day is not None:
                    if Hour is not None:
                        Nsnapshots = 1
                        h = self.getHours(Year,Month,Day,Hour)
                    else: 
                        Nsnapshots = 4
                        h = self.getHours(Year,Month,Day,0)
                else:
                    Nsnapshots = self.getNdaysInMonth(Year,Month)*4
                    h = self.getHours(Year,Month,1,0)
            if Season is not None:
                if Season == 'DJF':
                    Months = [12,1,2]
                    h = self.getHours(Year-1,12,1,0)
                if Season == 'MAM':
                    Months = [3,4,5]
                    h = self.getHours(Year,3,1,0)
                if Season == 'JJA':
                    Months = [6,7,8]
                    h = self.getHours(Year,6,1,0)
                if Season == 'SON':
                    Months = [9,10,11]
                    h = self.getHours(Year,9,1,0)
                Nsnapshots = 0
                for Month in Months:
                    Nsnapshots += self.getNdaysInMonth(Year,Month)*4
        Dates = []
        for i in range(Nsnapshots):
            Dates.append( self.getDate(h) )
            h += 6.
        return Dates

    def snapshot(self, Year=0, Month=1, Day=1, Hour=0):
        """
        # Extracts a single snapshot of Field.
        # Note that netCDF4 will automatically
        # - scale/offset values
        # - output a masked array if nc file has fill value specify
        """
        # select file and time index
        now  = self.getHours(Year,Month,Day,Hour)
        if now < self.MinHour or now > self.MaxHour:
            raise ValueError('Date '+str(self.getDate(now))+' not in dataset!!')
        Found = False
        for key in self.Files:
            if now in self.Times[key]:
                File = self.Files[key]
                l    = argmin(abs(self.Times[key]-now))
                Found = True
                break
        if not Found:
            raise ValueError('Date '+str(self.getDate(now))+str(now)+' not found!!')
        # retrieve variable
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
        # interpolate from model to pressure coords if required
        if self.Interpolate:
            lnsp = self.ps_data.snapshot(Year,Month,Day,Hour)
            ps = exp(lnsp)
            f = self.interpolate(f,ps,self.p)
        # scale field to get units of s**-1 in forecast variables
        if self.LevType == 'surface_forecast':
            if Hour in [6,18]:
                factor = 1./60./60./6. 
            else:
                factor = 1./60./60./12.
        else:
            factor = 1.
        return f*factor

    def hybToPress(self, xold, ps, p=None):
        # interpolate from hybrid levels to pressure levels p
        if p is None: p = self.p
        if len(xold.shape) == 3:
            xnew = self.interpolate(xold,ps,p)
        if len(xold.shape) == 4:
            nt,nz,ny,nx = xold.shape
            nz = len(p)
            xnew = ma.zeros((nt,nz,ny,nx),dtype=float)
            for l in range(nt):
                xnew[l] = self.interpolate(xold[l],ps[l],p)
        return xnew

    def interpolate(self,xold,ps,p):
        pnew = p[:,None,None] + ps[None,:,:]*0.
        pold = (self.hyam[:,None,None]+self.hybm[:,None,None]*ps[None,:,:])/100.
        xnew = vinterpol(pold,xold,pnew,Extrapolate=False,FillValue=self.FillValue)
        return xnew
        
    def getDay(self, Year=1958, Month=1, Day=1, Daily=None, TimeZoneOffset=0):
        # Return 1 day of data. TimeZoneOffset = -XX means time zone
        # is XX hours behind (earlier) than UTC
        f = []
        if TimeZoneOffset > 0 and (Year,Month,Day) == (1958,1,1): \
           TimeZoneOffset = 0
        if TimeZoneOffset < 0 and (Year,Month,Day) == (2001,12,31): \
           TimeZoneOffset = 0 
        dates = self.getDateList(Year,Month,Day)
        for date in dates:
            h    = self.getHours(*date) - TimeZoneOffset
            date = self.getDate(h)
            f.append(self.snapshot(*date))
        f = array(f)
        if   Daily is None:  return f
        elif Daily == 'max': return f.max(axis=0)
        elif Daily == 'min': return f.min(axis=0)
        elif Daily == 'avg': return f.mean(axis=0)
        else: raise ValueError,'operation %s not recognized' % Daily

    def getMonth(self, Year=1958, Month=1, Daily=None, TimeZoneOffset=0):
        # Return 1 month of data.
        # Keep iterating over day of month until exception
        # occurs, marking end of month
        print 'Getting %s %s %s' %(self.Field,Year,Month)
        Ndays = self.getNdaysInMonth(Year,Month)
        meter = ProgressMeter(total=Ndays)        
        f = []
        for Day in range(1,Ndays+1):
            meter.update(1)
            x = self.getDay(Year,Month,Day,Daily,TimeZoneOffset)
            if Daily is None: f.extend( x.tolist() )
            else: f.append(x)
        return array(f)

    def getSeason(self, Year=1959, Season='DJF'):
        if Season == 'DJF':
            DateStart = (Year-1,12,1,0)
            DateEnd   = (Year,2,28,18)
        if Season == 'MAM': 
            DateStart = (Year,3,1,0)
            DateEnd   = (Year,5,31,18)
        if Season == 'JJA': 
            DateStart = (Year,6,1,0)
            DateEnd   = (Year,8,31,18)
        if Season == 'SON': 
            DateStart = (Year,9,1,0)
            DateEnd   = (Year,11,30,18)
        return self.getTimeSlice(DateStart,DateEnd)        

    def getData(self, Year=1958, Month=1, Day=None, Hour=None, Season=None,\
                TimeZoneOffset=0, Daily=None):
        if Season is not None:
            return self.getSeason(Year,Season,Daily,TimeZoneOffset)
        if Hour is None:
            if Day is None:
                return self.getMonth(Year,Month,Daily,TimeZoneOffset)
            else:
                return self.getDay(Year,Month,Day,Daily=Daily)
        else:
            return self.snapshot(Year,Month,Day,Hour)
        
    def getTimeSlice(self, DateStart = (1958,1,1,0), DateEnd = (1958,12,31,18) ):
        print 'DataServer: Getting timeslice %s to %s' % (DateStart,DateEnd)
        h0 = self.getHours(*DateStart)
        h1 = self.getHours(*DateEnd)        
        N = int((h1-h0)/6+1)
        f = self.snapshot(*self.getDate(h0))
        shape = (N,) + f.shape
        if hasattr(f,'mask'):
            f = ma.zeros(shape,dtype=float)
        else:
            f = zeros(shape,dtype=float)
        meter = ProgressMeter(total=N)
        for l in range(N):
            meter.update(1)
            f[l] = self.snapshot(*self.getDate(h0)) 
            h0 += 6
        return f

if __name__ == '__main__':
    d = DataServer(Field='T', LevType='modlev')
    f=d.snapshot(Year=1980, Month=2, Day=1, Hour=0)
    import matplotlib.pyplot as plt
    plt.contourf(f[:,:,0])
    plt.colorbar()
    plt.show()

