import string,glob,os,time,datetime

SynopDir = '/home/rca/obs/Irish_station_data/synop'

class StationDataServer:

    def __init__(self,Station):
        self.Dir = SynopDir
        Stations = [os.path.basename(i) for i in glob.glob('%s/*'%self.Dir)]
        if Station in Stations:
            self.Station = Station
            self.data = self._readData()
        else:
            raise '\nstation %s unknown\n' % Station
        self.Year0 = 1

    def getData(self,Year,Month,Day,Hour,Field=None):
        timestamp = ('%04i'+'%02i'*3) % (Year,Month,Day,Hour)
        if Field is None:
            try:
                return self.data[timestamp]
            except:
                return (-999.,)*5
        elif Field in ['temp','windir','winspd','rh','precip']:
            try:
                if Field=='temp': return self.data[timestamp][0]
                if Field=='windir': return self.data[timestamp][1]
                if Field=='winspd': return self.data[timestamp][2]
                if Field=='rh': return self.data[timestamp][3]
                if Field=='precip': return self.data[timestamp][4]
            except:
                return -999.
        else: raise 'Field can only be one of temp, windir, winspd, rh, precip'
        
    def getDateRange(self):
        dates = self.data.keys()
        dates.sort()
        print '%s station contains data from %s to %s' % \
              (self.Station,
               time.strftime('%d-%b-%Y %H:%M:%S',time.strptime(dates[0],'%Y%m%d%H')),
               time.strftime('%d-%b-%Y %H:%M:%S',time.strptime(dates[-1],'%Y%m%d%H')))
        

    def _readData(self):
        print 'Reading data for %s station (this takes a little while) ...' % self.Station
        ss = open(os.path.join(self.Dir,self.Station)).readlines()
        data = {}
        for s in ss:
            try:
                s = s.split('|')
                int(s[1])
            except:
                continue
            #print s
            timestamp = time.strptime(s[2].strip(),'%d-%b-%Y %H:%M:%S')
            timestamp = time.strftime('%Y%m%d%H',timestamp)
            try:
                data[timestamp] = [float(s[i]) for i in range(3,8)]
            except:
                for i in range(3,8):
                    if s[i].strip() == '': s[i]=-999.
                data[timestamp] = [float(s[i]) for i in range(3,8)]
        return data
            
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
        self.Year0=1950
        if Year is not None:
            if Month is not None:
                if Day is not None:
                    if Hour is not None:
                        Nsnapshots = 1
                        h = self.getHours(Year,Month,Day,Hour)
                    else: 
                        Nsnapshots = 12
                        h = self.getHours(Year,Month,Day,0)
                else:
                    Nsnapshots = self.getNdaysInMonth(Year,Month)*24
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
                    Nsnapshots += self.getNdaysInMonth(Year,Month)*24
        Dates = []
        for i in range(Nsnapshots):
            Dates.append( self.getDate(h) )
            h += 1.
        return Dates


if __name__=='__main__':
    s = StationDataServer('Birr')
    s.getDateRange()
    dates = s.getDateList(Year=1993,Season='JJA')
    for date in dates:
        value = s.getData(*date)
        if value != -999.:
            print value
        else:
            continue
