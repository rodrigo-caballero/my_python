#!/usr/bin/env python
'''
Adds the line (x,y) colored by the values of t
'''
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection,CircleCollection
from matplotlib.colors import ListedColormap, BoundaryNorm

def addMultiColorLine(x,y,t,
                      lw=None,
                      ms=None,
                      ColorMap=None,
                      Colorbar = True,
                      ColorbarLabel=None,
                      NormRange = None,
                      Stride=1):

    # define colormap and norm
    if ColorMap is None:
        cmap=plt.get_cmap('jet')
    else:
        cmap=plt.get_cmap(ColorMap)
    if NormRange is None:
        norm=plt.Normalize(t.min(), t.max())
    else:
        norm=plt.Normalize(NormRange[0], NormRange[1])

    # draw multicolored line (as collection of line segments)
    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    lc = LineCollection(segments, cmap=cmap, norm=norm)
    lc.set_array(t)
    lc.set_linewidth(lw)
    plt.gca().add_collection(lc)

    # add dots if required
    if ms is not None:
        stride = Stride
        plt.scatter(x[::stride], y[::stride], c=t[::stride],
                    s=ms, marker='o', cmap=cmap, norm=norm,
                    linewidths=0)

    # add colorbar if req
    if Colorbar:
        cb = plt.colorbar(lc)
        if ColorbarLabel is not None: cb.set_label(ColorbarLabel)

if __name__ == '__main__':
    fig = plt.figure()
    t = np.linspace(0, 10, 100)
    x = np.cos(1.9*np.pi * t/10.)
    y = np.sin(1.9*np.pi * t/10.)

    addMultiColorLine(x,y,t, ColorMap='jet', lw=3, ms=50)

    plt.xlim(x.min(), x.max())
    plt.ylim(y.min(), y.max())
    plt.show()
