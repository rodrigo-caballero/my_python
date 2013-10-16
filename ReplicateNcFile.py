#!/usr/bin/env python

import sys
from netCDF4 import Dataset as NetCDFFile

def replicate(OldFileName,NewFileName):
    # Creates a new NetCDF file with the same dimensions and variables as
    # the old file but no content
    OldFile = NetCDFFile(OldFileName,'r')
    NewFile = NetCDFFile(NewFileName,'w',format='NETCDF3_CLASSIC')

    Dims = OldFile.dimensions

    for key in Dims:
        NewFile.createDimension(key,len(Dims[key]))

    Vars = OldFile.variables
    for key in Vars:
        NewFile.createVariable(key,Vars[key].typecode(),Vars[key].dimensions)
        for key1 in OldFile.variables[key].__dict__:
            exec('NewFile.variables[key].%s = OldFile.variables[key].%s'%(key1,key1))
        if key in Dims and Dims[key] is not None:
            NewFile.variables[key][:] = OldFile.variables[key][:]
    return NewFile

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print '\nUsage: ReplicateNcFile.py OldFileName NewFileName\n'
        sys.exit()
    f = replicate(*sys.argv[1:3])
    f.close()
