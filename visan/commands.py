# Copyright (C) 2002-2021 S[&]T, The Netherlands.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""
VISAN command line functions and procedures
"""

__all__ = ['histogramplot', 'plot', 'wplot', 'executescript', 'browseproduct', 'version']

import os
import sys
import numpy
import harp
from .harpplot import PlotDataForProduct, WorldPlotDataForProduct


def histogramplot(data, bins, *args, **kwargs):
    """ Draw a histogram plot.

    This is a convenience function that creates a histogram in a plot window.

    >>> histogramplot(data, bins)

    will create a histogramplot where 'data' is the output of the histogram()
    function and 'bins' is the bins parameter that was used to create the
    histogram.

    Both 'data' and 'bins' should be rank-1 arrays and the array length of
    'data' should be one less than the length of 'bins'.

    For customizing the plot you can use the same additional options as are
    available for the plot() function.
    """

    data = numpy.asarray(data)
    bins = numpy.asarray(bins)
    x = numpy.transpose(numpy.reshape(numpy.concatenate([bins[:-1], bins[1:]]), (2, len(bins) - 1))).ravel()
    y = numpy.transpose(numpy.reshape(numpy.concatenate([data, data]), (2, len(data)))).ravel()
    plot(x, y, *args, **kwargs)


def plot(*args, **kwargs):
    """ Display a 2-dimensional plot of a dataset.

    The plot() function has several different usage modes, and
    can take a large number of optional keywords. For a full
    reference guide, please consult the VISAN documentation at:

        <http://www.stcorp.nl/beat/>

    Basic usage:

    >>> plot(ydata)

    where 'ydata' is a one-dimensional Python list or numpy array,
    will plot the 'ydata' values on the vertical axis against an
    index array [0..len(data)] on the horizontal axis, in a
    single plot frame.

    >>> plot(xdata, ydata)

    where 'xdata' and 'ydata' are both one-dimensional, will plot
    the 'ydata' values on the vertical axis against the
    corresponding 'xdata' values on the horizontal axis.

    If 'ydata', or 'xdata' and 'ydata' are two-dimensional n x m
    arrays, a sequence of n plot frames will be created. Each
    frame f will show a plot of the ydata[f,:] values against the
    xdata[f,:] values. Initially, only the first frame is shown.
    The user can start an animation sequence which will cycle
    through the successive frames in the plot window.

    >>> plot(harpproduct)

    where 'harpproduct' is an object of type harp.Product (see
    also the documentation for the HARP python interface), will
    display a specific 2D plot associated with the type of data
    contained in 'harpproduct'.

    >>> plot(harpproduct, value='variablename')

    will create a 2D plot for the specified variable of the HARP
    product.

    >>> w = plot(data1)
    >>> plot(data2, window=w)

    will plot data2 in the same window 'w' as used for data1,
    instead of opening a separate window.

    In addition to the 'window' keyword, the plot() function also
    accepts a number of other, comma-separated optional
    properties of the form 'property=value'. Their order is
    arbitrary, but they must always appear after any data
    arguments to the plot() function.

    Available plot() properties are:
    window, windowtitle, size, pos, title, xrange, yrange,
    xmin, xmax, ymin, ymax, xlog, ylog, xbase, ybase, xlabel,
    ylabel, xnumticks, ynumticks, numticks, showanimationtoolbar,
    showpropertypanel,
    value, name, lines, linewidth, stipplepattern, points,
    pointsize, color, opacity.

    """
    import wx
    from . import windowhandler as WindowHandler
    from visan.plot import PlotFrame

    # validate all arguments

    defaultProperties = dict()
    dataSetAttributes = dict()
    dataSetLocation = []
    xdata = None
    ydata = None
    value = None
    try:
        value = kwargs["value"]
    except KeyError:
        pass

    if len(args) > 0:
        if isinstance(args[0], harp.Product):
            if len(args) != 1:
                raise ValueError("plot() does not allow additional data arguments when the first argument "
                                 "is a HARP product")
            xdata, ydata, dataSetAttributes, dataSetLocation, defaultProperties = PlotDataForProduct(args[0], value)
        else:
            if value is not None:
                raise ValueError("parameter 'value' (%s) is only allowed when plotting a HARP product" % value)
            if len(args) > 2:
                raise ValueError("plot() takes at most two data arguments (%d given)" % len(args))
            elif len(args) > 1:
                xdata = args[0]
                if isinstance(xdata, harp.Variable):
                    xdata = xdata.data
                ydata = args[1]
                if isinstance(ydata, harp.Variable):
                    ydata = ydata.data
            else:
                ydata = args[0]
                if isinstance(ydata, harp.Variable):
                    ydata = ydata.data
    elif value is not None:
        raise ValueError("parameter 'value' (%s) is only allowed when plotting a HARP product" % value)

    knownproperties = ["value", "window", "windowtitle", "size", "pos", "title", "xrange", "yrange", "xmin", "xmax",
                       "ymin", "ymax", "xlog", "ylog", "xbase", "ybase", "xlabel", "ylabel", "xnumticks", "ynumticks",
                       "numticks", "showanimationtoolbar", "showpropertypanel", "name", "lines", "linewidth",
                       "stipplepattern", "points", "pointsize", "color", "opacity"]

    unknowns = [k for k in list(kwargs.keys()) if k not in knownproperties]

    if len(unknowns) == 1:
        raise TypeError("Invalid keyword: %s\n(Supported keywords are: %s)" %
                        (unknowns[0], ', '.join(knownproperties)))
    elif len(unknowns) > 1:
        raise TypeError("Invalid keywords: %s\n(Supported keywords are: %s)" %
                        (', '.join(unknowns), ', '.join(knownproperties)))

    # window
    window = kwargs.get("window")
    if window is not None:
        if not isinstance(window, PlotFrame):
            raise ValueError("parameter 'window' (%s) does not refer to a plot window" % window)
        if not window:
            raise ValueError("parameter 'window' refers to a window that no longer exists")

    # windowtitle
    windowtitle = kwargs.get("windowtitle")
    if windowtitle is not None:
        try:
            windowtitle = str(windowtitle)
        except TypeError:
            raise ValueError("parameter 'windowtitle' should be a string")

    # size
    size = kwargs.get("size")
    if size is not None:
        try:
            size = tuple(size)
        except TypeError:
            raise TypeError("parameter 'size' should be a 2-element sequence of numbers (was: '%s')" % str(size))
        try:
            x = float(size[0])
            y = float(size[1])
        except TypeError:
            raise TypeError("parameter 'size' should be a 2-element sequence of numbers (was: '%s')" % str(size))
        if x <= 0 or y <= 0:
            raise ValueError("parameter 'size' must contain positive numbers (was: '%s')" % str(size))
        xmax = wx.SystemSettings_GetMetric(wx.SYS_SCREEN_X)
        if x > xmax:
            raise ValueError("x component of 'size' parameter must not exceed maximum screen width ('%g' > '%g')" %
                             (x, xmax))
        ymax = wx.SystemSettings_GetMetric(wx.SYS_SCREEN_Y)
        if y > ymax:
            raise ValueError("y component of 'size' parameter must not exceed maximum screen heigth ('%g' > '%g')" %
                             (y, ymax))

    # pos
    pos = kwargs.get("pos")
    if pos is not None:
        try:
            pos = tuple(pos)
        except TypeError:
            raise TypeError("parameter 'pos' should be a 2-element sequence of numbers (was: '%s')" % str(pos))
        try:
            x = float(pos[0])
            y = float(pos[1])
        except TypeError:
            raise TypeError("parameter 'pos' should be a 2-element sequence of numbers (was: '%s')" % str(pos))
        if x < 0 or y < 0:
            raise ValueError("parameter 'pos' must contain positive numbers (was: '%s')" % str(pos))
        xmax = wx.SystemSettings_GetMetric(wx.SYS_SCREEN_X)
        if x > xmax:
            raise ValueError("x component of 'pos' parameter must not exceed maximum screen width ('%g' > '%g')" %
                             (x, xmax))
        ymax = wx.SystemSettings_GetMetric(wx.SYS_SCREEN_Y)
        if y > ymax:
            raise ValueError("y component of 'pos' parameter must not exceed maximum screen heigth ('%g' > '%g')" %
                             (y, ymax))

    # check mutual exclusive parameters
    if kwargs.get("xmin") is not None and kwargs.get("xrange") is not None:
        raise ValueError("it is not allowed to specify both 'xrange' and 'xmin' in a single call")
    if kwargs.get("xmax") is not None and kwargs.get("xrange") is not None:
        raise ValueError("it is not allowed to specify both 'xrange' and 'xmax' in a single call")
    if kwargs.get("ymin") is not None and kwargs.get("yrange") is not None:
        raise ValueError("it is not allowed to specify both 'yrange' and 'ymin' in a single call")
    if kwargs.get("ymax") is not None and kwargs.get("yrange") is not None:
        raise ValueError("it is not allowed to specify both 'yrange' and 'ymax' in a single call")
    if kwargs.get("numticks") is not None and kwargs.get("xnumticks") is not None:
        raise ValueError("it is not allowed to specify both 'numticks' and 'xnumticks' in a single call")
    if kwargs.get("numticks") is not None and kwargs.get("ynumticks") is not None:
        raise ValueError("it is not allowed to specify both 'numticks' and 'ynumticks' in a single call")

    # process arguments

    if window is None:
        if size is None:
            size = WindowHandler.GetDefaultSize()
        if pos is None:
            pos = WindowHandler.GetNextPosition(size)
        plot = PlotFrame(size=size, pos=pos)
    else:
        plot = window
        if size is not None:
            plot.SetSize(size)
        if pos is not None:
            plot.Move(pos)

    # prevent intermediate repaints of the plotwindow until we have set all properties
    plot.Freeze()

    try:
        # add data set (if data was given)
        dataSetId = None
        if len(args) > 0:
            dataSetId = plot.AddDataSet(xdata, ydata)
            for attr in dataSetAttributes:
                plot.AddDataSetAttribute(dataSetId, attr, dataSetAttributes[attr])
            if len(dataSetLocation) == 2:
                # TODO: make this work for animated plots
                plot.AddDataSetLocation(dataSetId, dataSetLocation[0], dataSetLocation[1])

        # set generic plot properties
        if windowtitle is not None:
            plot.SetTitle(windowtitle)
        if kwargs.get("title") is not None:
            plot.SetPlotTitle(kwargs.get("title"))
        elif "title" in defaultProperties:
            plot.SetPlotTitle(defaultProperties["title"])
        if kwargs.get("xrange") is not None:
            plot.SetXAxisRange(kwargs.get("xrange"))
        if kwargs.get("yrange") is not None:
            plot.SetYAxisRange(kwargs.get("yrange"))
        if kwargs.get("xmin") is not None:
            if kwargs.get("xmax") is not None:
                plot.SetXAxisRange([kwargs.get("xmin"), kwargs.get("xmax")])
            else:
                plot.SetXAxisRange([kwargs.get("xmin"), plot.GetXAxisRange()[1]])
        if kwargs.get("xmax") is not None:
            plot.SetXAxisRange([plot.GetXAxisRange()[0], kwargs.get("xmax")])
        if kwargs.get("ymin") is not None:
            if kwargs.get("ymax") is not None:
                plot.SetYAxisRange([kwargs.get("ymin"), kwargs.get("ymax")])
            else:
                plot.SetYAxisRange([kwargs.get("ymin"), plot.GetYAxisRange()[1]])
        if kwargs.get("ymax") is not None:
            plot.SetYAxisRange([plot.GetYAxisRange()[0], kwargs.get("ymax")])
        if kwargs.get("xlog") is not None:
            plot.SetXLogAxis(kwargs.get("xlog"))
        elif "xlog" in defaultProperties:
            plot.SetXLogAxis(defaultProperties["xlog"])
        if kwargs.get("ylog") is not None:
            plot.SetYLogAxis(kwargs.get("ylog"))
        elif "ylog" in defaultProperties:
            plot.SetYLogAxis(defaultProperties["ylog"])
        if kwargs.get("xbase") is not None:
            plot.SetXAxisBase(kwargs.get("xbase"))
        elif "xbase" in defaultProperties:
            plot.SetXAxisBase(defaultProperties["xbase"])
        if kwargs.get("ybase") is not None:
            plot.SetYAxisBase(kwargs.get("ybase"))
        elif "ybase" in defaultProperties:
            plot.SetYAxisBase(defaultProperties["ybase"])
        if kwargs.get("xlabel") is not None:
            plot.SetXAxisTitle(kwargs.get("xlabel"))
        elif "xlabel" in defaultProperties:
            plot.SetXAxisTitle(defaultProperties["xlabel"])
        if kwargs.get("ylabel") is not None:
            plot.SetYAxisTitle(kwargs.get("ylabel"))
        elif "ylabel" in defaultProperties:
            plot.SetYAxisTitle(defaultProperties["ylabel"])
        if kwargs.get("numticks") is not None:
            plot.SetXNumAxisLabels(kwargs.get("numticks"))
            plot.SetYNumAxisLabels(kwargs.get("numticks"))
        if kwargs.get("xnumticks") is not None:
            plot.SetXNumAxisLabels(kwargs.get("xnumticks"))
        if kwargs.get("ynumticks") is not None:
            plot.SetYNumAxisLabels(kwargs.get("ynumticks"))
        if kwargs.get("showanimationtoolbar") is not None:
            plot.ShowAnimationToolbar(kwargs.get("showanimationtoolbar"))
        elif "showanimationtoolbar" in defaultProperties:
            plot.ShowAnimationToolbar(defaultProperties["showanimationtoolbar"])
        if kwargs.get("showpropertypanel") is not None:
            plot.ShowPropertyPanel(kwargs.get("showpropertypanel"))
        elif "showpropertypanel" in defaultProperties:
            plot.ShowPropertyPanel(defaultProperties["showpropertypanel"])

        # set data set properties
        if dataSetId is not None:
            if kwargs.get("name") is not None:
                plot.SetDataSetLabel(dataSetId, kwargs.get("name"))
            elif "name" in defaultProperties:
                plot.SetDataSetLabel(dataSetId, defaultProperties["name"])
            if kwargs.get("lines") is not None:
                plot.SetPlotLines(dataSetId, kwargs.get("lines"))
            if kwargs.get("linewidth") is not None:
                plot.SetLineWidth(dataSetId, kwargs.get("linewidth"))
            if kwargs.get("stipplepattern") is not None:
                plot.SetLineStipplePattern(dataSetId, kwargs.get("stipplepattern"))
            if kwargs.get("points") is not None:
                plot.SetPlotPoints(dataSetId, kwargs.get("points"))
            if kwargs.get("pointsize") is not None:
                plot.SetPointSize(dataSetId, kwargs.get("pointsize"))
            if kwargs.get("color") is not None:
                plot.SetPlotColor(dataSetId, kwargs.get("color"))
            if kwargs.get("opacity") is not None:
                plot.SetOpacity(dataSetId, kwargs.get("opacity"))
            else:
                # use our own VISAN specific opacity setting
                plot.SetOpacity(dataSetId, 0.6)
    except Exception:
        if window is None:
            # only destroy the window if we created it ourselves
            plot.Destroy()
        raise
    plot.Thaw()

    return plot


def wplot(*args, **kwargs):
    """ Display a dataset plotted onto an Earth world map.

    The wplot() function accepts dataset parameters similar to
    the plot() function. It can plot basic longitude vs. latitude
    data as well as HARP products containing latitude/longitude
    information. All datasets are plotted onto a 2D or 3D
    Earth world map. For a full reference guide, please consult
    the VISAN documentation at:

        <http://www.stcorp.nl/beat/>

    Basic usage:

    >>> wplot(latitude, longitude)

    will plot the locations using the information from the 'latitude'
    and 'longitude' arrays and project these onto a world map, in a
    single plot frame. The type of projection can be chosen by
    supplying a value for the 'projection' keyword.
    The latitude/longitude arrays may contain either points or
    corner coordinates.

    >>> wplot(latitude, longitude, data)

    will plot the locations using 'data' as color information.

    If 'data' is one-dimensional, then the data will be plotted as
    points or swaths.
    It will be plotted as points if the latitude/longitude arrays
    are one-dimensional, and as swaths if latitude/longitude arrays
    are two-dimensional (in which case the second dimension should
    capture the corners of the swath)

    If 'data' has more than one dimension, then 'data' will be plotted
    as a grid using the latitude and longitude as axis.
    Latitude should match the last dimension of 'data' and longitude
    the second-last dimension.
    If 'data' is three dimensional, then an animation plot is created
    with the first dimension being used as time dimension.

    >>> plot(harpproduct)

    where 'harpproduct' is an object of type harp.Product (see
    also the documentation for the HARP python interface), will
    display a specific worldmap plot associated with the type of
    data contained in 'harpproduct'.

    >>> plot(harpproduct, value='variablename')

    will create a worldmap plot for the specified variable of the
    HARP product.

    The wplot() function also accepts a number of comma-separated
    optional properties of the form 'property=value'. Their order
    is arbitrary, but they must always appear after any data
    arguments to the wplot() function.

    Available wplot() properties are:
    window, windowtitle, size, pos, title, centerlat,
    centerlon, zoom, projection, projectionlat, projectionlon,
    showanimationtoolbar, showpropertypanel, showcolorbar,
    value, colortable, colorrange, colorbartitle, numcolorlabels,
    opacity, linewidth, pointsize, drawpath, drawlocation,
    heightfactor, minheightvalue, maxheightvalue, deltaradius.

    """
    import wx
    from . import windowhandler as WindowHandler
    from visan.plot import WorldPlotFrame

    kPointData = 0
    kSwathData = 1
    kGridData = 2

    # validate all arguments

    defaultProperties = dict()
    dataSetAttributes = dict()
    latitude = None
    longitude = None
    data = None
    value = None
    datatype = kPointData
    plotPoints = False
    plotLines = False
    try:
        value = kwargs["value"]
    except KeyError:
        pass

    if kwargs.get("drawpath") is not None:
        plotLines = bool(kwargs["drawpath"])

    if kwargs.get("drawlocation") is not None:
        plotPoints = bool(kwargs["drawlocation"])

    if len(args) > 0:
        if isinstance(args[0], harp.Product):
            if len(args) != 1:
                raise ValueError("wplot() does not allow additional data arguments when the first argument is a "
                                 "HARP product")
            datatype, data, latitude, longitude, dataSetAttributes, defaultProperties = \
                WorldPlotDataForProduct(args[0], plotPoints or plotLines, value)
        else:
            if value is not None:
                raise ValueError("parameter 'value' (%s) is only allowed when plotting a HARP product" % value)
            if len(args) == 3:
                data = args[2]
                if isinstance(data, harp.Variable):
                    data = data.data
            elif len(args) != 2:
                raise ValueError("wplot() takes either two or three data arguments if the first argument is not a "
                                 "HARP product (%d given)" % len(args))
            latitude = args[0]
            if isinstance(latitude, harp.Variable):
                latitude = latitude.data
            if not isinstance(latitude, numpy.ndarray):
                try:
                    latitude = numpy.asarray(args[0])
                except TypeError:
                    raise TypeError("latitude data argument cannot be converted to numpy array. %s" % str(latitude))
            longitude = args[1]
            if isinstance(longitude, harp.Variable):
                longitude = longitude.data
            if not isinstance(longitude, numpy.ndarray):
                try:
                    longitude = numpy.asarray(args[1])
                except TypeError:
                    raise TypeError("longitude data argument cannot be converted to numpy array. %s" % str(longitude))

            if data is not None:
                try:
                    data = numpy.asarray(data)
                except TypeError:
                    raise TypeError("data argument cannot be converted to numpy array. %s" % str(data))
                if data.ndim > 1:
                    datatype = kGridData

            if datatype == kPointData and latitude.ndim == 2 and longitude.ndim == 2:
                datatype = kSwathData

    elif value is not None:
        raise ValueError("parameter 'value' (%s) is only allowed when plotting a HARP product" % value)

    knownproperties = ["window", "windowtitle", "size", "pos", "title", "centerlat", "centerlon", "zoom", "projection",
                       "projectionlat", "projectionlon", "showanimationtoolbar", "showpropertypanel", "showcolorbar",
                       "value", "colortable", "colorrange", "colorbartitle", "numcolorlabels", "opacity", "linewidth",
                       "pointsize", "drawpath", "drawlocation", "heightfactor", "minheightvalue", "maxheightvalue",
                       "deltaradius"]

    unknowns = [k for k in list(kwargs.keys()) if k not in knownproperties]

    if len(unknowns) == 1:
        raise TypeError("Invalid keyword: %s\n(Supported keywords are: %s)" % (unknowns[0], ', '.join(knownproperties)))
    elif len(unknowns) > 1:
        raise TypeError("Invalid keywords: %s\n(Supported keywords are: %s)" %
                        (', '.join(unknowns), ', '.join(knownproperties)))

    # window
    window = kwargs.get("window")
    if window is not None:
        if not isinstance(window, WorldPlotFrame):
            raise ValueError("parameter 'window' (%s) does not refer to a wplot window" % window)
        if not window:
            raise ValueError("parameter 'window' refers to a window that no longer exists")

    # windowtitle
    windowtitle = kwargs.get("windowtitle")
    if windowtitle is not None:
        try:
            windowtitle = str(windowtitle)
        except TypeError:
            raise ValueError("parameter 'windowtitle' should be a string")

    # size
    size = kwargs.get("size")
    if size is not None:
        try:
            size = tuple(size)
        except TypeError:
            raise TypeError("parameter 'size' should be a 2-element sequence of numbers (was: '%s')" % str(size))
        try:
            x = float(size[0])
            y = float(size[1])
        except TypeError:
            raise TypeError("parameter 'size' should be a 2-element sequence of numbers (was: '%s')" % str(size))
        if x <= 0 or y <= 0:
            raise ValueError("parameter 'size' must contain positive numbers (was: '%s')" % str(size))
        xmax = wx.SystemSettings_GetMetric(wx.SYS_SCREEN_X)
        if x > xmax:
            raise ValueError("x component of 'size' parameter must not exceed maximum screen width ('%g' > '%g')" %
                             (x, xmax))
        ymax = wx.SystemSettings_GetMetric(wx.SYS_SCREEN_Y)
        if y > ymax:
            raise ValueError("y component of 'size' parameter must not exceed maximum screen heigth ('%g' > '%g')" %
                             (y, ymax))

    # pos
    pos = kwargs.get("pos")
    if pos is not None:
        try:
            pos = tuple(pos)
        except TypeError:
            raise TypeError("parameter 'pos' should be a 2-element sequence of numbers (was: '%s')" % str(pos))
        try:
            x = float(pos[0])
            y = float(pos[1])
        except TypeError:
            raise TypeError("parameter 'pos' should be a 2-element sequence of numbers (was: '%s')" % str(pos))
        if x < 0 or y < 0:
            raise ValueError("parameter 'pos' must contain positive numbers (was: '%s')" % str(pos))
        xmax = wx.SystemSettings_GetMetric(wx.SYS_SCREEN_X)
        if x > xmax:
            raise ValueError("x component of 'pos' parameter must not exceed maximum screen width ('%g' > '%g')" %
                             (x, xmax))
        ymax = wx.SystemSettings_GetMetric(wx.SYS_SCREEN_Y)
        if y > ymax:
            raise ValueError("y component of 'pos' parameter must not exceed maximum screen heigth ('%g' > '%g')" %
                             (y, ymax))

    # process arguments

    if window is None:
        if size is None:
            size = WindowHandler.GetDefaultSize()
        if pos is None:
            pos = WindowHandler.GetNextPosition(size)
        plot = WorldPlotFrame(size=size, pos=pos)
    else:
        plot = window
        if size is not None:
            plot.SetSize(size)
        if pos is not None:
            plot.Move(pos)

    # prevent intermediate repaints of the plotwindow until we have set all properties
    plot.Freeze()

    try:
        # add data set (if data was given)
        dataSetId = None
        if len(args) > 0:
            if datatype == kPointData:
                if plotLines:
                    dataSetId = plot.AddLineData(latitude, longitude)
                else:
                    dataSetId = plot.AddPointData(latitude, longitude, data)
            elif datatype == kSwathData:
                dataSetId = plot.AddSwathData(latitude, longitude, data)
            elif datatype == kGridData:
                dataSetId = plot.AddGridData(latitude, longitude, data)
            else:
                raise AssertionError("invalid datatype (%d) for plotdata" % datatype)
            for attr in dataSetAttributes:
                plot.AddDataSetAttribute(dataSetId, attr, dataSetAttributes[attr])

        # set generic plot properties
        if windowtitle is not None:
            plot.SetTitle(windowtitle)
        if kwargs.get("title") is not None:
            plot.SetPlotTitle(kwargs.get("title"))
        elif "title" in defaultProperties:
            plot.SetPlotTitle(defaultProperties["title"])
        if kwargs.get("showanimationtoolbar") is not None:
            plot.ShowAnimationToolbar(kwargs.get("showanimationtoolbar"))
        elif "showanimationtoolbar" in defaultProperties:
            plot.ShowAnimationToolbar(defaultProperties["showanimationtoolbar"])
        if kwargs.get("showpropertypanel") is not None:
            plot.ShowPropertyPanel(kwargs.get("showpropertypanel"))
        elif "showpropertypanel" in defaultProperties:
            plot.ShowPropertyPanel(defaultProperties["showpropertypanel"])
        if kwargs.get("showcolorbar") is not None:
            plot.ShowColorBar(kwargs.get("showcolorbar"))
        elif "showcolorbar" in defaultProperties:
            plot.ShowColorBar(defaultProperties["showcolorbar"])
        if kwargs.get("projection") is not None:
            plot.SetProjection(kwargs.get("projection"))
        if kwargs.get("projectionlat") is not None:
            plot.SetProjectionCenterLatitude(kwargs.get("projectionlat"))
        if kwargs.get("projectionlon") is not None:
            plot.SetProjectionCenterLongitude(kwargs.get("projectionlon"))
        if kwargs.get("centerlat") is not None:
            plot.SetViewCenterLatitude(kwargs.get("centerlat"))
        if kwargs.get("centerlon") is not None:
            plot.SetViewCenterLongitude(kwargs.get("centerlon"))
        if kwargs.get("zoom") is not None:
            plot.SetViewZoom(kwargs.get("zoom"))
        else:
            if window is None:
                # if we are creating the plot, set the initial zoom level (if 1.0 is not appropriate)
                if kwargs.get("projection") is None or kwargs.get("projection").lower() == "3d":
                    plot.SetViewZoom(2.5)
                elif kwargs.get("projection").lower() == "lambert cylindrical" or \
                        kwargs.get("projection").lower() == "plate caree" or \
                        kwargs.get("projection").lower() == "mollweide" or \
                        kwargs.get("projection").lower() == "robinson":
                    plot.SetViewZoom(1.6)

        # set data set properties
        if dataSetId is not None:
            if kwargs.get("name") is not None:
                plot.SetDataSetLabel(dataSetId, kwargs.get("name"))
            elif "name" in defaultProperties:
                plot.SetDataSetLabel(dataSetId, defaultProperties["name"])
            if kwargs.get("colortable") is not None:
                try:
                    plot.GetColorTable(dataSetId).SetColorTableByName(kwargs.get("colortable"))
                except Exception:
                    plot.GetColorTable(dataSetId).Import(kwargs.get("colortable"))
            elif "colortable" in defaultProperties:
                plot.GetColorTable(dataSetId).SetColorTableByName(defaultProperties["colortable"])
            if kwargs.get("colorrange") is not None:
                plot.SetColorRange(dataSetId, kwargs.get("colorrange"))
            elif "colorrange" in defaultProperties:
                plot.SetColorRange(dataSetId, defaultProperties["colorrange"])
            if kwargs.get("colorbartitle") is not None:
                plot.SetColorBarTitle(dataSetId, kwargs.get("colorbartitle"))
            elif "colorbartitle" in defaultProperties:
                plot.SetColorBarTitle(dataSetId, defaultProperties["colorbartitle"])
            if kwargs.get("numcolorlabels") is not None:
                plot.SetNumColorBarLabels(dataSetId, kwargs.get("numcolorlabels"))
            if kwargs.get("opacity") is not None:
                plot.SetOpacity(dataSetId, kwargs.get("opacity"))
            elif "opacity" in defaultProperties:
                plot.SetOpacity(dataSetId, defaultProperties["opacity"])
            if kwargs.get("linewidth") is not None:
                plot.SetLineWidth(dataSetId, kwargs.get("linewidth"))
            if kwargs.get("pointsize") is not None:
                plot.SetPointSize(dataSetId, kwargs.get("pointsize"))
            if kwargs.get("heightfactor") is not None:
                plot.SetHeightFactor(dataSetId, kwargs.get("heightfactor"))
            if kwargs.get("minheightvalue") is not None:
                plot.SetMinHeightValue(dataSetId, kwargs.get("minheightvalue"))
            if kwargs.get("maxheightvalue") is not None:
                plot.SetMinHeightValue(dataSetId, kwargs.get("maxheightvalue"))
            if kwargs.get("deltaradius") is not None:
                try:
                    deltaradius = float(kwargs.get("deltaradius"))
                except TypeError:
                    raise TypeError("deltaradius property should be a float (was: '%s')" %
                                    str(kwargs.get("deltaradius")))
                plot.SetReferenceHeight(dataSetId, 1.0 + deltaradius)
    except Exception:
        if window is None:
            # only destroy the window if we created it ourselves
            plot.Destroy()
        raise
    plot.Thaw()

    # TODO: Is this still applicable?
    # The Yield and Refresh are needed to make sure that colortable changes are shown.
    # Somehow the plot is not rendered using the new colortable after the Thaw.
    # We have to let the current Refresh result in a Render (using wx.Yield())
    # and then ask for a new render using Refresh()
    wx.Yield()
    plot.Refresh()

    return plot


def executescript(filename, globals=None, mainargs=None):
    """ Execute a script.

    This routine runs an external python script.

    >>> executescript(filename)

    runs the script file located at the path indicated by 'filename' and returns
    to the prompt when the script is finished. If the system is unable to locate
    the file indicated by 'filename' an execption will be thrown.

    When you run a script, VISAN will automatically add the location of your
    script to the module searchpath (sys.path). This means that if your script
    uses modules that are located in the same directory as the script file then
    these modules will automatically be found. When the script is finished VISAN
    will change the module searchpath back to its original value.


    If you want the script to have access to variables that you have already
    set or if you want to have access to variables that are going to be set
    by the script, just pass 'globals()' as second parameter:

    >>> executescript(filename, globals())


    If the script needs to be run as a 'main' script (i.e. as if it was run as an
    argument to the python executable) and/or requires command line arguments you
    can use the 'mainargs' keyword. The 'mainargs' keyword should contain a list
    of command line options (which may be an empty list). For instance, to run a
    setup.py script to install an external module you could use:

    >>> executescript('/home/user/package/setup.py', mainargs = ['install'])

    This will have the result the script is called with the '__name__
    variable set to '__main__' and sys.argv will have been set to
    ['/home/user/package/setup.py', 'install'].
    The current working directory for the script will also be set to the
    directory of the script (e.g. '/home/user/package').

    Note that if a 'mainargs' keyword parameter is provided, the 'globals'
    parameter to executescript() (if present) will be ignored.

    """
    if os.path.exists(filename):
        if os.path.isfile(filename):
            print(("Executing VISAN/Python script '%s':\n" % filename))

            oldcwd = os.getcwd()
            scriptdir = os.path.dirname(filename)
            sys.path.insert(0, scriptdir)
            oldargv = sys.argv
            try:
                if mainargs is None:
                    if globals is None:
                        exec(compile(open(filename).read(), filename, 'exec'))
                    else:
                        exec(compile(open(filename).read(), filename, 'exec'), globals)
                else:
                    sys.argv = [filename] + mainargs
                    os.chdir(scriptdir)
                    exec(compile(open(filename).read(), filename, 'exec'), {'__name__': '__main__'})
            finally:
                del sys.path[0]
                sys.argv = oldargv
                os.chdir(oldcwd)
        else:
            raise IOError("Error executing VISAN/Python script, the path '%s' does not point to a file\n" % filename)
    else:
        raise IOError("Error executing VISAN/Python script, the file '%s' does not exist\n" % filename)


def browseproduct(filename):
    """ Open the Product Browser with a specific product.

    This routine opens a new Product Browser window with the give product file.

    >>> browseproduct(filename)

    If the system is unable to locate the file indicated by 'filename' an
    execption will be thrown.

    """
    if os.path.exists(filename):
        if os.path.isfile(filename):
            import wx
            wx.GetApp().BrowseProduct(filename)
        else:
            raise IOError("Error opening product file, the path '%s' does not point to a file\n" % filename)
    else:
        raise IOError("Error opening product file, the file '%s' does not exist\n" % filename)


def version():
    """ Get version number of VISAN.

    >>> v = version()

    returns the version number of the current VISAN release.
    """
    from . import VERSION
    return VERSION
