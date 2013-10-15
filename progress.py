"""
Here is a silly example of its usage:

import progress
import time
import random

total = 1000
p = progress.ProgressMeter(total=total)

while total > 0:
    cnt = random.randint(1, 25)
    p.update(cnt)
    total -= cnt
    time.sleep(random.random())


Here is an example of its output:

[------------------------->                                   ] 41%  821.2/sec
"""
import time, sys, math

class ProgressMeter(object):
    ESC = chr(27)
    def __init__(self, **kw):
        # What time do we start tracking our progress from?
        self.timestamp = kw.get('timestamp', time.time())
        # What kind of unit are we tracking?
        self.unit = str(kw.get('unit', ''))
        # Number of units to process
        self.total = int(kw.get('total', 100))
        # Number of units already processed
        self.count = int(kw.get('count', 0))
        # Refresh rate in seconds
        self.rate_refresh = float(kw.get('rate_refresh', .5))
        # Number of ticks in meter
        self.meter_ticks = int(kw.get('ticks', 50))
        self.meter_division = float(self.total) / self.meter_ticks
        self.meter_value = int(self.count / self.meter_division)
        self.last_update = None
        self.rate_history_idx = 0
        self.rate_history_len = 10
        self.rate_history = [None] * self.rate_history_len
        self.rate_current = 0.0
        self.last_refresh = 0
        self._cursor = False
        self.reset_cursor()

    def reset_cursor(self, first=False):
        if self._cursor:
            sys.stdout.write(self.ESC + '[u')
        self._cursor = True
        sys.stdout.write(self.ESC + '[s')

    def update(self, count, **kw):
        now = time.time()
        # Caclulate rate of progress
        rate = 0.0
        # Add count to Total
        self.count += count
        self.count = min(self.count, self.total)
        if self.last_update:
            delta = now - float(self.last_update)
            if delta:
                rate = count / delta
            else:
                rate = count
            self.rate_history[self.rate_history_idx] = rate
            self.rate_history_idx += 1
            self.rate_history_idx %= self.rate_history_len
            cnt = 0
            total = 0.0
            # Average rate history
            for rate in self.rate_history:
                if rate == None:
                    continue
                cnt += 1
                total += rate
            rate = total / cnt
        self.rate_current = rate
        self.last_update = now
        # Device Total by meter division
        value = int(self.count / self.meter_division)
        if value > self.meter_value:
            self.meter_value = value
        if self.last_refresh:
            if (now - self.last_refresh) > self.rate_refresh or \
                (self.count >= self.total):
                    self.refresh()
        else:
            self.refresh()

    def get_meter(self, **kw):
        bar = '-' * self.meter_value
        pad = ' ' * (self.meter_ticks - self.meter_value)
        frac = (float(self.count) / float(self.total)) 
        perc = frac * 100.
        if self.rate_current > 0.:
            tot = self.total/self.rate_current
            eta = tot*(1.-frac)
        else:
            tot = -1.
            eta = -1.
        if tot < 60.:
            return '[%s>%s] %.1f of %.1f s left' % (bar, pad, eta, tot)
        else:
            tot_min = int(tot)/60
            tot_sec = int(tot-tot_min*60)
            eta_min = int(eta)/60
            eta_sec = int(eta-eta_min*60)
            return '[%s>%s] %sm%02is of %sm%02is left' % (bar, pad, eta_min, eta_sec, tot_min, tot_sec)

    def refresh(self, **kw):
        # Clear line
        sys.stdout.write(self.ESC + '[2K')
        self.reset_cursor()
        sys.stdout.write(self.get_meter(**kw))
        # Are we finished?
        if self.count >= self.total:
            sys.stdout.write('\n')
        sys.stdout.flush()
        # Timestamp
        self.last_refresh = time.time()

if __name__ == '__main__':
    import progress
    import time
    import random

    total = 100
    p = progress.ProgressMeter(total=total)

##     for i in range(total):
##         p.update(1)
##         time.sleep(.1)

    while total > 0:
        cnt = random.randint(1,10)
        p.update(cnt)
        total -= cnt
        time.sleep(random.random()*30.)
