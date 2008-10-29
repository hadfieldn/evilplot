"""A dastardly library that interfaces with Gnuplot.

In other words, Andrew McNabb's plotting module, written for the sole purpose
of making his life more simple.  This is a work in progress.  This module is
designed to be used in conjunction with Chris's Makefile.

Sample usage.  Note that parameters like `title` and `xmin` can be specified
either as arguments during instantiation or as attributes at a later time.

>>> p = Plot(title='Sample Plot')
>>> p.title
'Sample Plot'
>>> f = Function(lambda x: x**2)
>>> f.xmin = -2
>>> f.xmax = 2
>>> p.append(f)
>>> p.show()
>>>

"""

import plot
from plot import *
import plotitems
from plotitems import *

if __name__ == '__main__':
    import doctest
    doctest.testmod()


__all__ = plot.__all__ + plotitems.__all__

# vim: et sw=4 sts=4
