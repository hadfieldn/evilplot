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

"""Implementation of the plot, which can contain multiple plot items."""

# TODO: add an implicit_y to allow plotting more kinds of 2d objects in 3d.

from __future__ import division
from __future__ import print_function

import os
import sys

from .param import Param, ParamObj
from . import util

try:
    from itertools import izip as zip
except ImportError:
    pass

# Normally we try to get the domain from the user or from PlotItems.  However,
# if nothing is specified, we should at least try something.  Recall that
# a domain is (xmin, xmax, ymin, ymax).
DEFAULT_DOMAIN = (0.0, 1.0) * 2


class Plot(ParamObj, list):
    """A plot which can be output and which is container of plot items.

    It's a list--add PlotItems to it.  Use plot.write("filename.gpi") to print
    to a file or plot.write() to send to standard out.  Use plot.show() to
    open an x11 window in Gnuplot.
    """
    _params = dict(dim=Param(doc='Dimensionality: 2D->plot, 3D->splot,'
                                + 'None->Autodetect.'),
            title=Param(doc='Title of the plot'),
            color=Param(doc='Whether to use color (vs. B&W)', default=True),
            xlabel=Param(doc='Label for the x axis'),
            ylabel=Param(doc='Label for the y axis'),
            xmin=Param(doc='Minimum x value'),
            xmax=Param(doc='Maximum x value'),
            ymin=Param(doc='Minimum y value'),
            ymax=Param(doc='Maximum y value'),
            zmin=Param(doc='Minimum z value'),
            zmax=Param(doc='Maximum z value'),
            xtics=Param(doc='Dictionary mapping ints to labels for x axis'),
            ytics=Param(doc='Dictionary mapping ints to labels for y axis'),
            boxwidth=Param(doc='Box width when style is boxes'),
            xlogscale=Param(doc='Use this log scale for x (0 for normal scale)', default=0),
            ylogscale=Param(doc='Use this log scale for y (0 for normal scale)', default=0),
            key=Param(doc='Move the key.  Example: key="bottom right"'),
            ratio=Param(doc='Size ratio (relative scale): set to 1 for square'),
            width=Param(doc='Width (only used in pgfplots)', default='2.6in'),
            height=Param(doc='Width (only used in pgfplots)', default='2.2in'),
            )

    # Note that xmin, xmax, ymin, ymax don't take any PlotItems into account.
    # Use self.domain if you want to see the actual domain we're going to use.

    def __init__(self, **kwds):
        self.given_dim = None
        ParamObj.__init__(self, **kwds)

    def write_items_gpi(self):
        """Write out data files for plot.

        For any PlotItems not set to output to stdout, write to the file
        that they are set to go to.
        """
        dim = self.dim
        domain = self.domain()
        for item in self:
            if (not item.external_datafile) and (item.filename):
                out = open(item.filename, 'w')
                try:
                    print(item.data(dim, domain), file=out)
                finally:
                    out.close()

    def write_gpi(self, filename):
        """Write out a gnuplot file.

        Open up a file and write out the gnuplot file.
        """
        if len(self) == 0:
            return

        self.write_items_gpi()

        with open(filename, 'w') as f:
            self._write_gpi_file(f)

    # DEPRECATED:
    def write(self, filename=None):
        """Write out a gnuplot file. (DEPRECATED)

        Open up a file (or stdout if no filename is specified) and write
        out the gnuplot file.
        """
        if len(self) == 0:
            return

        self.write_items_gpi()

        if filename:
            out = open(filename, 'w')
        else:
            out = sys.stdout

        try:
            self._write_gpi_file(out)
        finally:
            if filename:
                out.close()

    def show(self):
        """Open a gnuplot process and plot to the screen.

        The window will persist.
        """
        from .Gnuplot.gp import GnuplotProcess
        self.write_items_gpi()
        gp = GnuplotProcess(persist=True)
        self._write_gpi_file(gp)
        gp.flush()

    def print_page(self):
        """Create a postscript file and send it to lpr for printing."""
        from subprocess import Popen, PIPE
        self.write_items_gpi()
        gp = Popen(('gnuplot'), stdin=PIPE, stdout=PIPE)
        lpr = Popen(('lpr'), stdin=gp.stdout, close_fds=True)
        gp.stdin.write('set terminal postscript\n')
        self._write_gpi_file(gp.stdin)
        gp.stdin.close()
        gp.wait()

    def _write_gpi_file(self, f):
        """Return the entire gnuplot file as a string.
        """
        assert(len(self) != 0), 'No plot items have been added.'

        dim = self.dim
        assert(dim == 2 or dim == 3)

        domain = self.domain()
        xmin, xmax, ymin, ymax = domain

        # If we still don't have a min and max at this point, it's over.
        if dim == 3:
            rmin, rmax = self.zmin, self.zmax
        else:
            domain = (domain[0], domain[1], None, None)
            dmin, dmax = (xmin, None), (xmax, None)
            rmin, rmax = self.ymin, self.ymax

        s = ''
        if dim == 3:
            print('set pm3d explicit', file=f)
        if self.title:
            print('set title "%s"' % self.title, file=f)
        if self.xlabel:
            print('set xlabel "%s"' % self.xlabel, file=f)
        if self.ylabel:
            print('set ylabel "%s"' % self.ylabel, file=f)
        if self.xlogscale:
            print('set logscale x %s' % self.xlogscale, file=f)
        if self.ylogscale:
            print('set logscale y %s' % self.ylogscale, file=f)
        if self.key:
            print('set key %s' % self.key, file=f)
        if self.xtics:
            # example: 'set xtics ("low" 0, "medium" 50, "high" 100)'
            ticstr = ', '.join('"%s" %s' % (val, key)
                    for key, val in self.xtics.iteritems())
            print('set xtics (%s)' % ticstr, file=f)
        if self.ytics:
            # example: 'set ytics ("low" 0, "medium" 50, "high" 100)'
            ticstr = ', '.join('"%s" %s' % (val, key)
                    for key, val in self.ytics.iteritems())
            print('set ytics (%s)' % ticstr, file=f)
        if self.boxwidth:
            print('set boxwidth %s' % (self.boxwidth), file=f)
        # We always want to plot lines between two points that are outside the
        # range of the graph:
        print('set clip two', file=f)
        if self.ratio:
            print('set size ratio %s' % (self.ratio), file=f)
        # The plot command:
        if dim == 2:
            print('plot [%s:%s]' % domain[0:2], end='', file=f)
        else:
            print('splot [%s:%s] [%s:%s]' % domain, end='', file=f)
        # Specifying the range is optional.
        if rmin is not None or rmax is not None:
            min_str = str(rmin) if (rmin is not None) else ''
            max_str = str(rmax) if (rmax is not None) else ''
            print('[%s:%s]' % (min_str, max_str), end='', file=f)
        print(', '.join([item.gpi_command(dim) for item in self]), file=f)
        for item in self:
            if not item.filename:
                print(item.data(dim, domain), file=f)
                print('e', file=f)

    def write_items_dat(self, basename):
        """Write out data files for plot.

        The specified basename (e.g., 'path/to/file') is used to generate
        filenames (e.g., 'path/to/file-1.dat').

        Returns a list of filenames.
        """
        dim = self.dim
        domain = self.domain()
        filenames = []
        for i, item in enumerate(self):
            if item.external_datafile:
                filenames.append(item.filename)
            else:
                filename = item.filename
                if not filename:
                    filename = '%s-%s.dat' % (basename, i)
                filenames.append(filename)

                with open(filename, 'w') as f:
                    print(item.data(dim, domain), file=f)
        return filenames

    def _write_pgf_file(self, f, datafiles):
        """Write out a PGF/TikZ (TeX) file."""

        assert(len(self) != 0), 'No plot items have been added.'

        dim = self.dim
        assert dim == 2, 'Only 2D plots currently supported in PGF mode.'

        xmin, xmax, ymin, ymax = self.domain()

        print(r'\begin{tikzpicture}', file=f)
        print(r'\begin{axis}[', file=f)

        params = []
        params.append('small,')
        params.append('width=%s,' % self.width)
        params.append('height=%s,' % self.height)
        if self.xlabel:
            params.append('xlabel={\small %s},' % self.xlabel)
        if self.ylabel:
            params.append('ylabel={\small %s},' % self.ylabel)
        if xmin is not None:
            params.append('xmin=%s,' % xmin)
        if xmax is not None:
            params.append('xmax=%s,' % xmax)
        if ymin is not None:
            params.append('ymin=%s,' % ymin)
        if ymax is not None:
            params.append('ymax=%s,' % ymax)
        if not self.color:
            params.append('cycle list name=linestyles, % black and white')
        if self.key:
            params.append('legend pos=%s,' % self.key)
        else:
            params.append('%legend pos=north west,')
        params.append('legend cell align=left,')
        if self.xtics:
            ticks = []
            labels = []
            for key, value in self.xtics.iteritems():
                ticks.append(str(key))
                labels.append(str(value))
            params.append('xtick={%s},' % ','.join(ticks))
            params.append('xticklabels={%s},' % ','.join(labels))
        if self.ytics:
            ticks = []
            labels = []
            for key, value in self.ytics.iteritems():
                ticks.append(str(key))
                labels.append(str(value))
            params.append('ytick={%s},' % ','.join(ticks))
            params.append('yticklabels={%s},' % ','.join(labels))
        params.append('xlabel near ticks,')
        params.append('ylabel near ticks,')
        if self.xlogscale:
            params.append('xmode=log,')
            params.append('log basis x=%s,' % self.xlogscale)
        if self.ylogscale:
            params.append('ymode=log,')
            params.append('log basis y=%s,' % self.ylogscale)
        params.append(']')
        print('   ', '\n    '.join(params), file=f)
        print(file=f)

        for item, datafile in zip(self, datafiles):
            print(item.pgf_command(dim, datafile), file=f)

        print(r'\end{axis}', file=f)
        print(r'\end{tikzpicture}', file=f)

    def write_pgf(self, filename):
        """Write out a PGF/TikZ (TeX) file.

        If `filename` is not specified, then the Plot's `name` attribute is
        used to autogenerate filenames.
        """
        if len(self) == 0:
            return

        basename, _ = os.path.splitext(filename)
        datafiles = self.write_items_dat(basename)

        with open(filename, 'w') as f:
            self._write_pgf_file(f, datafiles)

    def get_dim(self):
        if self.given_dim is not None:
            return self.given_dim
        else:
            dim = 2
            for item in self:
                if item.dim == 3:
                    dim = 3
                    break
            return dim

    def set_dim(self, value):
        self.given_dim = value

    dim = property(fget = get_dim, fset = set_dim)

    def domain(self):
        """Return domain, i.e. the tuple: (xmin, xmax, ymin, ymax)

        If one of these values was specified for the plot, return that value
        as is.  Otherwise, get the value by looking at all of the PlotItems.
        """
        xmin, xmax, ymin, ymax = \
            given_xmin, given_xmax, given_ymin, given_ymax = \
            self.xmin, self.xmax, self.ymin, self.ymax
        if xmin is None or xmax is None or ymin is None or ymax is None:
            for item in self:
                if given_xmin is None:
                    xmin = util.min_ifexists(xmin, item.xmin)
                if given_xmax is None:
                    xmax = util.max_ifexists(xmax, item.xmax)
                if item.dim == 3:
                    if given_ymin is None:
                        ymin = util.min_ifexists(ymin, item.ymin)
                    if given_ymax is None:
                        ymax = util.max_ifexists(ymax, item.ymax)
        if xmin is None:
            xmin = DEFAULT_DOMAIN[0]
        if xmax is None:
            xmax = DEFAULT_DOMAIN[1]
        if ymin is None:
            ymin = DEFAULT_DOMAIN[2]
        if ymax is None:
            ymax = DEFAULT_DOMAIN[3]
        return xmin, xmax, ymin, ymax


########################################################################
### TESTING

if __name__ == '__main__':
    from plotitems import Function
    p = Plot(title='x**2', xmin=-4, xmax=4)
    p.append(Function(lambda x: x**2))
    p.show()
    p.write(filename='plottest.gpi')


__all__ = ['Plot']

# vim: et sw=4 sts=4
