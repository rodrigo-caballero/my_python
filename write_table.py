#!/usr/bin/env python

def write_table(x, FileName, mode='w', sep=' '):
    '''
    Write matrix x as a table of numbers in file FileName
    Numbers arranged in columns separated by sep (default space)
    '''
    import numpy as np
    import string
    x = np.array(x)
    if len(x.shape) != 2:
        raise ValueError,'Input matrix must be of rank 2, this one has rank %s' % len(x.shape)
    Nrows,Ncols = x.shape
    f = open(FileName,mode)
    format = ('%11.5e'+sep)*(Ncols-1) + '%11.5e\n'
    for i in range(Nrows):
        f.write(format % tuple(x[i]))
    f.close()

if __name__ == '__main__':
    write_table([[1,2],[3.4,500000]],'jim.txt',sep=',')
