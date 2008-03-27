#!/usr/bin/env python
"""Helper functions for the evil plot library."""


from __future__ import division

def min_ifexists(a, b):
    if a is None:
        return b
    elif b is None:
        return a
    else:
        return min(a, b)

