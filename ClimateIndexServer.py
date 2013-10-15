#!/usr/bin/env python

import glob,os,sys
from numpy import *
from netCDF4 import Dataset as NetCDFFile
from read_table import read_table

class Index:
    def getIndex(self, YearStart=None, YearStop=None, Season=None):
        if YearStart is None: YearStart = self.YearStart
        if YearStop is None:  YearStop  = self.YearStop
        if Season is None:
            Year0 = YearStart - self.YearStart
            Nyears = YearStop - YearStart+1
            return self.index[Year0:Year0+Nyears].flatten()
        elif Season == 'DJF':
            index = []
            YearStart = max(self.YearStart+1,YearStart)
            Nyears = YearStop-YearStart+1
            Year0 = YearStart-self.YearStart
            for Year in range(YearStart,YearStop+1):
                l = Year-self.YearStart
                index.append( (self.index[l-1,11]\
                               +self.index[l,0]\
                               +self.index[l,1])/3.)
            return array(index)
        elif '_' in Season:
            index = []
            YearStart = max(self.YearStart+1,YearStart)
            Nyears = YearStop-YearStart+1
            Year0 = YearStart-self.YearStart
            Months = [int(i) for i in Season.split('_')]
            for Year in range(YearStart,YearStop+1):
                l = Year-self.YearStart
                ind = 0.
                for m in Months: ind += self.index[l,m-1]
                index.append( ind/len(Months) )
            return array(index)

class WaveActivityIndex(Index):
    def __init__(self):
        FileName = '/Users/rca/hadley/eddy_stress/bruce/WaveActivityIndex.txt'
        year,index = read_table(FileName)
        self.YearStart = int(year[0])
        self.YearStop  = int(year[-1])
        self.index = index
        
class MasatoWBIndex(Index):
    def __init__(self,Cluster=1):
        FileName = '/Users/rca/hadley/eddy_stress/bruce/MasatoWBindices.txt'
        y = read_table(FileName)
        y = array(y).transpose()
        year = arange(1958,2002)
        self.YearStart = year[0]
        self.YearStop  = year[-1]
        self.index = y[Cluster-1]
        
class BruceSLPIndex(Index):
    def __init__(self, Index='SLPI'):
        if Index=='SLPI':
            File = open('/Users/rca/obs/BruceSLP/slp_index_DJF_norm.txt')
        elif Index =='CPI':
            File = open('/Users/rca/obs/BruceSLP/CPI.txt')
        print Index
        year = []
        index = []
        while 1:
            try:
                y,i = File.readline().split()
                year.append(int(y))
                index.append(float(i))
            except:
                break
        self.YearStart = year[0]
        self.YearStop  = year[-1]
        self.index = array(index)
        
class MDRIndex(Index):
    def __init__(self, Index='Kaplan'):
        File = open('/Users/rca/obs/hurricanes/MainDevelRegionSST.txt')
        year = []
        ind = []
        i = ['Blended','HadISST','Kaplan','NOAA'].index(Index) + 1
        while 1:
            try:
                s = File.readline()
                year.append(int(float(s.split()[0])))
                ind.append(float(s.split()[i]))
                print s.split()[i]
            except:
                break
        self.YearStart = year[0]
        self.YearStop  = year[-1]
        self.index = array(ind)
        
class EnsoIndex(Index):
    def __init__(self, Index='N34', Source='obs'):
        if Source == 'obs':
            File = open('/Users/rca/obs/ENSO/%s' % Index)
            (self.YearStart, self.YearStop) =\
                              [int(i) for i in File.readline().split()[0:2]]
            Nyears = self.YearStop-self.YearStart+1
            self.index = zeros((Nyears,12))*0.
            for l in range(Nyears):
                self.index[l,:] =\
                     array([float(i) for i in File.readline().split()])[1:]
        else:
            FileName = glob.glob('/Users/rca/obs/AR4/20c3m/atm/mo/ts/%s/%s.*'\
                                 %(Source,Index))[0]
            File = NetCDFFile(FileName)
            # Figure out which calendar to use
            self.calendar = File.variables['time'].calendar
            # Figure out year range
            TimeUnits = File.variables['time'].units
            self.Year0 = int(TimeUnits.split()[2][0:4])
            time = File.variables['time'][:]
            self.YearStart = self.getDate(time[0])[0]
            self.YearStop = self.getDate(time[-1])[0]
            Nyears = self.YearStop-self.YearStart+1
            self.index = File.variables['ts'][:].reshape((Nyears,12))

class NaoIndex(Index):
    def __init__(self, Index='NAO', Source='obs'):
        if Source == 'obs':
            File = open('/Users/rca/obs/NAO/%s' % Index)
            (self.YearStart,self.YearStop) =\
                              [int(i) for i in File.readline().split()[0:2]]
            Nyears = self.YearStop-self.YearStart+1
            self.index = zeros((Nyears,12))*0.
            for l in range(Nyears):
                self.index[l,:] =\
                     array([float(i) for i in File.readline().split()])[1:13]

class DailyNaoIndex(Index):
    def __init__(self, Index='NAO', Source='obs'):
        if Source == 'obs':
            File = open('/Users/rca/obs/NAO/norm.daily.nao.index.b500101.current.ascii')
            (self.YearStart,self.YearStop) =\
                              [int(i) for i in File.readline().split()[0:2]]
            Nyears = self.YearStop-self.YearStart+1
            self.index = zeros((Nyears,12))*0.
            for l in range(Nyears):
                self.index[l,:] =\
                     array([float(i) for i in File.readline().split()])[1:13]

class PnaIndex(Index):
    def __init__(self, Index='PNA', Source='obs'):
        if Source == 'obs':
            File = open('/Users/rca/obs/PNA/%s' % Index)
            (self.YearStart,self.YearStop) =\
                              [int(i) for i in File.readline().split()[0:2]]
            Nyears = self.YearStop-self.YearStart+1
            self.index = zeros((Nyears,12))*0.
            for l in range(Nyears):
                for m in range(12):
                    self.index[l,m] = float(File.readline().split()[2])

class QboIndex(Index):
    def __init__(self, Index='QBO'):
        File = open('/Users/rca/obs/QBO/QBO.txt')
        (self.YearStart,self.YearStop) =\
                          [int(i) for i in File.readline().split()[0:2]]
        Nyears = self.YearStop-self.YearStart+1
        self.index = zeros((Nyears,12))*0.
        for l in range(Nyears):
            self.index[l,:] = \
                     array([float(i) for i in File.readline().split()])[1:13]

def computeEnsoIndex():
    os.chdir('/Volumes/gordo/AR4/20c3m/atm/mo/ts')
    dirs = glob.glob('*')
    for dir in dirs:
        if 'mri' not in dir: continue
        print dir
        os.chdir(dir)
        for file in glob.glob('*nc'):
            if file[0:3] == 'N34': continue
            os.system('ncwa -d lon,190.,240. -d lat,-5.,5. -a lat,lon '+\
                      '%s N34.%s' % (file,file) )
        os.chdir('..')
    
if __name__ == '__main__':
    AR4Data = [\
               'giss_model_e_r',
               'inmcm3_0',
               'giss_model_e_h',
               'miub_echo_g',
               'cccma_cgcm3_1',
               'giss_aom',
               'ipsl_cm4',
               'miroc3_2_medres',
               'iap_fgoals1_0_g',
               'mri_cgcm2_3_2a',
               'cccma_cgcm3_1_t63',
               'gfdl_cm2_0',
               'cnrm_cm3',
               'bcc_cm1',
               'gfdl_cm2_1',
               'mpi_echam5',
               'bccr_bcm2_0',
               'csiro_mk3_0',
               'miroc3_2_hires',
               'ingv_echam4']

#    enso = EnsoIndex(Source=AR4Data[4])
#    index = enso.getIndex(Season='DJF')

    nao = NaoIndex()
    index = nao.getIndex(Season='1_2_3')


    year = arange(nao.YearStart+1,nao.YearStop+1)
    index = index-index.mean()
    index = index/index.std()
    for l in range(len(year)): print year[l],index[l]

