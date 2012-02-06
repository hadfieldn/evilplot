# EvilPlot
# Copyright 2008 Brigham Young University
#
# This file is part of EvilPlot.
#
# EvilPlot is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# EvilPlot is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# EvilPlot.  If not, see <http://www.gnu.org/licenses/>.
#
# Inquiries regarding any further use of the Materials contained on this site,
# please contact the Copyright Licensing Office, Brigham Young University,
# 3760 HBLL, Provo, UT 84602, (801) 422-9339 or 422-3821, e-mail
# copyright@byu.edu.

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

from . import plot
from .plot import *
from . import plotitems
from .plotitems import *

if __name__ == '__main__':
    import doctest
    doctest.testmod()


__all__ = plot.__all__ + plotitems.__all__

# vim: et sw=4 sts=4
