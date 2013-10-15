#!/usr/bin/env python

def read_table(FileName, skip=0, sep=None, comments=None):
    '''
    Read a table of numbers in file FileName
    Numbers arranged in columns separated by sep (default space)
    Skip the first skip rows (default 0)
    Returns tuple with columns as NumPy arrays
    '''
    import numpy as np
    import string
    text = open(FileName,'r').readlines()
    for i in range(skip):
        text.pop(0)
    t = []
    for i in range(len(text)):
        if comments is not None and text[i][0] == comments:
            continue
        else:
            t.append([float(x.strip()) for x in text[i].split(sep)])
    x = np.array(t).transpose().tolist()
    x = [np.array(xx) for xx in x]
    return tuple(x)

if __name__ == '__main__':
    read_table('jim.txt')
