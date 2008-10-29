#!/usr/bin/env python
"""Implementation of the plot, which can contain multiple plot items."""

# TODO: add an implicit_y to allow plotting more kinds of 2d objects in 3d.

from __future__ import division
from param import Param, ParamObj

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
            )

    # Note that xmin, xmax, ymin, ymax don't take any PlotItems into account.
    # Use self.domain if you want to see the actual domain we're going to use.

    def __init__(self, **kwds):
        self.given_dim = None
        ParamObj.__init__(self, **kwds)

    def write_items(self):
        """Write out data files for plot.

        For any PlotItems not set to output to stdout, write to the file
        that they are set to go to.
        """
        dim = self.dim
        domain = self.domain()
        for item in self:
            if (not item.external_datafile) and (item.filename != '-'):
                out = open(item.filename, 'w')
                try:
                    print >> out, item.data(dim, domain)
                finally:
                    out.close()

    def write(self, filename=None):
        """Write out the gnuplot file to a file.
        
        Open up a file (or stdout if no filename is specified) and write
        out the gnuplot file.
        """
        if len(self) == 0:
            return

        self.write_items()

        if filename:
            out = open(filename, 'w')
        else:
            import sys
            out = sys.stdout

        try:
            print >> out, self
        finally:
            if filename:
                out.close()

    def show(self):
        """Open a gnuplot process and plot to the screen.
        
        The window will persist.
        """
        from Gnuplot.gp import GnuplotProcess
        self.write_items()
        gp = GnuplotProcess(persist=True)
        gp.write(str(self))
        gp.flush()

    def __str__(self):
        """Return the entire gnuplot file as a string.
        """
        assert(len(self) != 0)

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
            s += 'set pm3d explicit\n'
        if self.title:
            s += 'set title "%s"\n' % self.title
        if self.xlabel:
            s += 'set xlabel "%s"\n' % self.xlabel
        if self.ylabel:
            s += 'set ylabel "%s"\n' % self.ylabel
        if self.xlogscale:
            s += 'set logscale x %s\n' % self.xlogscale
        if self.ylogscale:
            s += 'set logscale y %s\n' % self.ylogscale
        if self.key:
            s += 'set key %s\n' % self.key
        if self.xtics:
            # example: 'set xtics ("low" 0, "medium" 50, "high" 100)'
            ticstr = ', '.join('"%s" %s' % (val, key)
                    for key, val in self.xtics.iteritems())
            s += 'set xtics (%s)\n' % ticstr
        if self.ytics:
            # example: 'set ytics ("low" 0, "medium" 50, "high" 100)'
            ticstr = ', '.join('"%s" %s' % (val, key)
                    for key, val in self.ytics.iteritems())
            s += 'set ytics (%s)\n' % ticstr
        if self.boxwidth:
            s += 'set boxwidth %s\n' % (self.boxwidth)
        # We always want to plot lines between two points that are outside the
        # range of the graph:
        s += 'set clip two\n'
        if self.ratio:
            s += 'set size ratio %s\n' % (self.ratio)
        # The plot command:
        if dim == 2:
            s += 'plot [%s:%s] ' % domain[0:2]
        else:
            s += 'splot [%s:%s] [%s:%s] ' % domain
        # Specifying the range is optional.
        if rmin is not None or rmax is not None:
            s += '['
            if rmin is not None:
                s += str(rmin)
            s += ':'
            if rmax is not None:
                s += str(rmax)
            s += '] '
        s += ', '.join([item.command(dim) for item in self])
        s += '\n'
        for item in self:
            if item.filename == '-':
                s += item.data(dim, domain)
        return s

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
            from util import min_ifexists
            for item in self:
                if given_xmin is None:
                    xmin = min_ifexists(xmin, item.xmin)
                if given_xmax is None:
                    xmax = max(xmax, item.xmax)
                if item.dim == 3:
                    if given_ymin is None:
                        ymin = min_ifexists(ymin, item.ymin)
                    if given_ymax is None:
                        ymax = max(ymax, item.ymax)
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
