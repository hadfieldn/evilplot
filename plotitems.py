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

"""Individual items that can be plotted."""

from __future__ import division
from __future__ import print_function

from six.moves import xrange as range
import sys

from .param import Param, ParamObj
from .util import linspace, min_ifexists, max_ifexists

try:
    from itertools import imap as map
except ImportError:
    pass


class PlotItem(ParamObj):
    """
    This is a basic PlotItem class that needs to be extended to be useful.
    """
    _params = dict(filename=Param(default='', doc="Where to write data; '' is automatic"),
            dim=Param(doc="Dimensionality; either 2 or 3"),
            title=Param(doc='Title in the key for this PlotItem'),
            xmin=Param(doc='Minimum x value'),
            xmax=Param(doc='Maximum x value'),
            ymin=Param(doc='Minimum y value, if 3D'),
            ymax=Param(doc='Maximum y value, if 3D'),
            style=Param(doc='Gnuplot plotting style', default='points'),
            smooth=Param(doc='Smoothing style'),
            linewidth=Param(default=4, doc="Width of lines"),
            pointsize=Param(default=1.5, doc="Size of points"),
            pointtype=Param(doc="Type of points"),
            )

    def __init__(self, **kwds):
        ParamObj.__init__(self, **kwds)
        self.external_datafile = False

    def gpi_command(self, dim):
        """Return the gnuplot command to plot this PlotItem."""
        s = "'%s'" % (self.filename if self.filename else '-')
        try:
            s += ' ' + self.using
        except AttributeError:
            pass
        if dim == 2 and self.smooth:
            s += ' smooth %s' % self.smooth
        if self.title:
            s += ' title "%s"' % self.title
        else:
            s += ' notitle'
        s += ' with %s' % self.style
        if self.style in ('lines', 'linespoints', 'errorbars'):
            s += ' lw %s' % self.linewidth
        if self.style in ('linespoints', 'points', 'errorbars'):
            s += ' ps %s' % self.pointsize
        if self.pointtype:
            s += ' pt %s' % self.pointtype
        return s

    def pgf_command(self, dim, filename, opts=None, indices=None):
        """Return the PGF command to plot this PlotItem.

        Note that only a subset of options are currently supported.
        """
        assert dim == 2, 'Only 2D currently supported in PGF mode'

        lines = []

        s = "'%s'" % (self.filename if self.filename else '-')

        if not opts:
            opts = []
            if self.smooth:
                opts.append('smooth')

            if self.style == 'lines':
                opts.append('mark=none')

        if not indices:
            indices = ['x index=0', 'y index=1']

        opts = ','.join(opts)
        indices = ','.join(indices)
        line = r'\addplot +[%s] table[%s] {%s};' % (opts, indices, filename)
        lines.append(line)

        # Legend
        if self.title:
            legend = r'\small %s' % self.title
            #legend = r'\footnotesize %s' % self.title
            #legend = self.title
            lines.append(r'\addlegendentry{%s}' % legend)

        return '\n'.join(lines)

    def samples(self, dim, domain):
        """Return a list of sample points for a given domain min/max.

        xmin, xmax, ymin, ymax = domain

        If the plot should be 2D, then ymin and ymax are None.
        """
        return []

    def data(self, dim, domain):
        """Return all of the data as a string.
        """
        datalines = []
        for values in self.samples(dim, domain):
            if values is not None:
                line = ' '.join(map(str, values))
            else:
                line = ''
            datalines.append(line)
        return '\n'.join(datalines)

    def write(self, dim, domain, filename=None):
        """Write out the data to a file.

        Open up a file (or stdout if no filename is specified) and write
        out the data to a file.
        """
        if filename:
            out = open(filename, 'w')
        else:
            out = sys.stdout

        try:
            for values in self.samples(dim, domain):
                if values is not None:
                    print(' '.join(map(str, values)), file=out)
        finally:
            if filename:
                out.close()


class Function(PlotItem):
    """
    This is a PlotItem that can be passed to a plot object.  It takes a
    continuous function on a real-valued interval, which it will sample from.

    f = function(thefunction, xmin=-1.0, xmax=1.0)

    Note that you probably want style='pm3d' if you have a 3D function.

    TODO: Discontinuities (add a blank line in samples)
    """
    _params = dict(style=Param(default='lines'),
            resolution=Param(doc='Number of samples in each dim', default=100),
            smooth=Param(default='csplines'),
            )

    def __init__(self, func, **kwds):
        super(Function, self).__init__(**kwds)
        self.f = func

        # Find out the dimensionality of the function.
        if hasattr(func, 'dimensions') and hasattr(func, 'constraints'):
            # Chris-style function
            self.pass_as_tuple = True
            self.dim = func.dimensions + 1
            self.xmin, self.xmax = func.constraints[0]
            if self.dim == 3:
                self.ymin, self.ymax = func.constraints[1]
        else:
            self.pass_as_tuple = False
            import inspect
            try:
                args = inspect.getargspec(self.f)[0]
                im_self = getattr(self.f, 'im_self', None)
                if im_self is None:
                    argcount = len(args)
                else:
                    argcount = len(args) - 1
            except TypeError:
                try:
                    args = inspect.getargspec(self.f.__call__)[0]
                    argcount = len(args) - 1
                except TypeError:
                    raise TypeError('Function PlotItem was given a non-function arg.')
            self.dim = argcount + 1
        if self.dim not in (2, 3):
            raise TypeError('Wrong dimensionality. Function must be f(x) or f(x,y)')

    def samples(self, dim, domain):
        # Note that self.dim is a property of the function and dim is a
        # property of the plot.
        xmin = max_ifexists(domain[0], self.xmin)
        xmax = min_ifexists(domain[1], self.xmax)
        ymin = max_ifexists(domain[2], self.ymin)
        ymax = min_ifexists(domain[3], self.ymax)

        data = []
        # Gnuplot requires that we loop through y before x.
        if dim == 2:
            for x in linspace(xmin, xmax, self.resolution):
                if self.pass_as_tuple:
                    sample = x, self.f((x))
                else:
                    sample = x, self.f(x)
                data.append(sample)
        elif dim == 3:
            for y in linspace(ymin, ymax, self.resolution):
                for x in linspace(xmin, xmax, self.resolution):
                    if self.dim == 2:
                        if self.pass_as_tuple:
                            sample = x, y, self.f((x))
                        else:
                            sample = x, y, self.f(x)
                    else:
                        if self.pass_as_tuple:
                            sample = x, y, self.f((x, y))
                        else:
                            sample = x, y, self.f(x, y)
                    data.append(sample)
                data.append(None)
        return data


class Histogram(PlotItem):
    """
    Histogram is a PlotItem that can be added to a plot object.  It takes a
    list of real-valued samples and adds them to a specified number of
    buckets.  Note that the plot should probably have ymin=0, or else the
    scaling will look wrong.

    h = histogram(samples, nbuckets)
    """

    _params = dict(
            style=Param(default='boxes'),
            normalize=Param(default=False, doc="Normalize (as probabilities)"),
            )

    def __init__(self, samples, nbuckets, **kwds):
        super(Histogram, self).__init__(**kwds)
        self.datalist = samples
        self.nbuckets = nbuckets

        self.xmin = min(samples)
        self.xmax = max(samples)

    def samples(self, dim, domain):
        assert(dim == 2)
        xmin = domain[0]
        xmax = domain[1]

        width = (xmax - xmin) / float(self.nbuckets)

        buckets = [0 for i in range(self.nbuckets)]
        for x in self.datalist:
            if x >= xmin and x <= xmax:
                i = int((x-xmin)/width)
                # borderline case that shouldn't make much of a difference
                #    (only happens when x==max):
                if i == self.nbuckets:
                    i -= 1
                buckets[i] += 1

        if self.normalize:
            scale = 1 / (width * len(self.datalist))
        else:
            scale = 1

        minbucketcenter = xmin + width/2
        return [(minbucketcenter + i * width, buckets[i] * scale, width) \
                    for i in range(self.nbuckets)]


class Density(PlotItem):
    """
    Density is a PlotItem that can be added to a plot object.  It takes a list
    of real-valued samples from a probability distribution and smooths them to
    make a pretty pdf.  Note that this "hides the warts," so in many
    situations it may be ideal to plot the density on top of the histogram.

    d = density(samples)
    """
    _params = dict(
            bandwidth=Param(doc='Relative KDE Bandwidth: 1 is for xmax-xmin', default=1/17),
            smooth=Param(default='csplines'),
            style=Param(default='lines'),
            resolution=Param(doc='Number of samples in plot', default=100),
            )
    def __init__(self, draws, **kwds):
        super(Density, self).__init__(**kwds)
        try:
            import numpy
            self.draws = numpy.array(draws)
        except:
            import Numeric
            self.draws = Numeric.array(draws)

        if 'xmin' not in kwds:
            self.xmin = min(draws)
        if 'xmax' not in kwds:
            self.xmax = max(draws)

    def samples(self, dim, domain):
        assert(dim == 2)
        xmin = domain[0]
        xmax = domain[1]
        from scipy.stats.kde import gaussian_kde
        xvalues = list(linspace(xmin, xmax, self.resolution))
        pdf = gaussian_kde(self.draws)
        yvalues = pdf(xvalues)
        return list(zip(xvalues, yvalues))


class Points(PlotItem):
    """
    Just print some simple points.  Give me a list of tuples.
    """
    def __init__(self, pointlist, **kwds):
        super(Points, self).__init__(**kwds)
        self.pointlist = pointlist

        self.dim = len(pointlist[0])
        assert(self.dim == 2 or self.dim == 3)

        if 'xmin' not in kwds:
            self.xmin = min(x[0] for x in self.pointlist)
        if 'xmax' not in kwds:
            self.xmax = max(x[0] for x in self.pointlist)
        if self.dim == 3:
            if 'ymin' not in kwds:
                self.ymin = min(x[1] for x in self.pointlist)
            if 'ymax' not in kwds:
                self.ymax = max(x[1] for x in self.pointlist)

    def samples(self, dim, domain):
        xmin, xmax, ymin, ymax = domain
        assert(dim == self.dim)
        l = []
        if dim == 2:
            for x in self.pointlist:
                if x[0] >= xmin and x[0] <= xmax:
                    l.append(x)
        elif dim == 3:
            for x in self.pointlist:
                if x[0] >= xmin and x[0] <= xmax and x[1] >= ymin and x[1] <= ymax:
                    l.append(x)
        return l


class RawData(PlotItem):
    """A plot item for arbitrary 2D data.

    RawData is especially useful for specialized styles such as errorbars or
    candlesticks.

    Not that error bars should be plotted _before_ the associated plot to
    ensure that the same colors get used in PGFPlots.
    """
    def __init__(self, pointlist, **kwds):
        super(RawData, self).__init__(**kwds)
        self.pointlist = pointlist

        if 'xmin' not in kwds:
            self.xmin = min(x[0] for x in self.pointlist)
        if 'xmax' not in kwds:
            self.xmax = max(x[0] for x in self.pointlist)

    def samples(self, dim, domain):
        xmin, xmax, ymin, ymax = domain
        return [x for x in self.pointlist if (x[0] >= xmin and x[0] <= xmax)]

    def pgf_command(self, dim, filename):
        opts = ['forget plot', 'mark=none', 'error bars/.cd', 'y explicit']
        indices = ['x index=0', 'y index=1']

        plus_opts = opts + ['y dir=plus']
        plus_indices = indices + [r'y error expr=\thisrowno{3}-\thisrowno{1}']
        plus_str = super(RawData, self).pgf_command(dim, filename, plus_opts,
                plus_indices)

        minus_opts = opts + ['y dir=minus']
        minus_indices = indices + [r'y error expr=\thisrowno{1}-\thisrowno{2}']
        minus_str = super(RawData, self).pgf_command(dim, filename, minus_opts,
                minus_indices)

        return '%s\n%s' % (plus_str, minus_str)


class Vectors(PlotItem):
    """Plots a set of vectors based on (x1, y1, x2, y2) tuples.

    If endpoints is specified, x2 and y2 indicate the tip of the arrow.
    Otherwise, x2 and y2 indicate the delta.

    todo: look more at "set clip" and at "arrowstyle"
    """
    _params = dict(
            heads=Param(doc='Number of heads (0, 1, or 2)', default=1),
            endpoints=Param(doc='Specify endpoints instead of start and delta', 
                default=False),
            style=Param(default='vectors')
            )
    def __init__(self, pointlist, **kwds):
        super(Vectors, self).__init__(**kwds)
        self.pointlist = pointlist

        self.dim = 2

        if 'xmin' not in kwds:
            if self.endpoints:
                from itertools import chain
                self.xmin = min(chain(
                    (x[0] for x in self.pointlist),
                    (x[2] for x in self.pointlist)))
            else:
                self.xmin = min(x[0] for x in self.pointlist)
        if 'xmax' not in kwds:
            if self.endpoints:
                from itertools import chain
                self.xmax = max(chain(
                    (x[0] for x in self.pointlist),
                    (x[2] for x in self.pointlist)))
            else:
                self.xmax = max(x[0] for x in self.pointlist)

    def gpi_command(self, dim):
        s = super(Vectors, self).gpi_command(dim)
        if self.heads == 0:
            s += ' nohead'
        elif self.heads == 1:
            s += ' head'
        else:
            s += ' heads'

        return s

    def samples(self, dim, domain):
        # right now we don't do any clipping (we ignore domain)
        assert(dim == self.dim)
        if self.endpoints:
            return [(x1, y1, x2-x1, y2-y1) for x1, y1, x2, y2 in self.pointlist]
        else:
            return self.pointlist


class External(PlotItem):
    """A PlotItem for plotting data from an external data file.

    Right now we assume that dims = 2
    """

    _params = dict(
        fields=Param(default=None,
            doc='Which fields of the file to use (using). note: 1-indexed')
        )

    def __init__(self, filename, **kwds):
        super(External, self).__init__(**kwds)
        self.dims = 2
        self.external_datafile = True
        self.filename = filename
        self.reload()

    def get_using(self):
        if self.fields is not None:
            return 'using %s' % ':'.join(str(f) for f in self.fields)
        else:
            return ''
    using = property(fget=get_using)

    def reload(self):
        """We should parse the file and calculate dims, xmin, xmax,
        ymin, ymax, etc.  Be careful about:
        - quoted strings, which are a single field, even if there
          are spaces inside them (currently ignored)
        - Gnuplot will assume that the data have 2 dimensions, even if
          there is just one field.
        """
        if self.fields is None:
            xfield = 0
            yfield = 1
        else:
            xfield = self.fields[0] - 1
            yfield = self.fields[1] - 1
        xmin = xmax = None
        ymin = ymax = None
        for line in open(self.filename):
            stripped_line = line.strip()
            if stripped_line != '' and stripped_line[0] != '#':
                data = [float(x) for x in stripped_line.split()]
                if xmin is None:
                    xmin = xmax = data[xfield]
                    ymin = ymax = data[yfield]
                else:
                    xmin = min(data[xfield], xmin)
                    xmax = max(data[xfield], xmax)
                    ymin = min(data[yfield], ymin)
                    ymax = max(data[yfield], ymax)
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax


########################################################################
### TESTING

if __name__ == '__main__':
    p = plot(title='x**2', xmin=-4, xmax=4)
    p.append(function(lambda x: x**2))
    p.show()
    p.write(gpifilename='plottest.gpi')


__all__ = ['Function', 'Histogram', 'Density', 'Points', 'RawData', 'Vectors',
        'External']

# vim: et sw=4 sts=4
