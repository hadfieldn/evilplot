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

"""Helper functions for the evil plot library."""

from __future__ import division

from six.moves import xrange as range

def min_ifexists(a, b):
    if a is None:
        return b
    elif b is None:
        return a
    else:
        return min(a, b)

def max_ifexists(a, b):
    if a is None:
        return b
    elif b is None:
        return a
    else:
        return max(a, b)

def frange(start, stop, step):
    n = int((stop - start) / step)
    x = start
    for i in range(n-1):
        yield x
        x += step
    yield stop

def linspace(start, stop, n):
    """Yields `n` floats starting with `start` and ending with `stop`."""
    step = (stop - start) / (n - 1)
    x = start
    for i in range(n-1):
        yield x
        x += step
    yield stop

# vim: et sw=4 sts=4
