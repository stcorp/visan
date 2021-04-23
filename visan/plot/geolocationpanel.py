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

import os

import numpy
import wx

from .worldplotwindow import WorldPlotWindow


class GeolocationPanel(wx.Panel):

    def __init__(self, parent):
        panelstyle = wx.TAB_TRAVERSAL
        if wx.Platform == '__WXGTK__':
            panelstyle |= wx.SUNKEN_BORDER
        wx.Panel.__init__(self, parent, -1, style=panelstyle)

        # Create and configure all widgets
        self.CreateControls()
        self.CreateLayout()
        self.datasetsShown = []

    def CreateControls(self):
        # Create the plot window
        self.plotWindow = WorldPlotWindow(self, -1)
        datadir = str(wx.Config.Get().Read('DirectoryLocation/ApplicationData'))
        self.plotWindow.SetCoastLineFile(os.path.join(datadir, "gshhs_l.b"))
        self.plotWindow.SetPoliticalBorderFile(os.path.join(datadir, "wdb_borders_l.b"))

    def CreateLayout(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.plotWindow, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def UpdateLocation(self, datasetId, location, keyframe):
        if len(location) == 0:
            self.plotWindow.SetViewCenter(0, 0)
            return
        latitude = location['latitude']
        longitude = location['longitude']
        if not isinstance(latitude, numpy.ndarray):
            try:
                latitude = numpy.asarray(latitude, dtype=numpy.double)
            except TypeError:
                raise TypeError("location latitude cannot be converted to numpy array")
        if not isinstance(longitude, numpy.ndarray):
            try:
                longitude = numpy.asarray(longitude, dtype=numpy.double)
            except TypeError:
                raise TypeError("location longitude cannot be converted to numpy array")
        if datasetId not in self.datasetsShown:
            if latitude.ndim == 2 and longitude.ndim == 2:
                self.plotWindow.AddSwathData(latitude, longitude, None)
            else:
                self.plotWindow.AddPointData(latitude.flat, longitude.flat, None)
            self.datasetsShown.append(datasetId)
        if latitude.ndim > 0 and longitude.ndim > 0:
            latitude = latitude[keyframe]
            longitude = longitude[keyframe]
        latitude = latitude.flat[0]
        longitude = longitude.flat[0]
        self.plotWindow.SetViewCenter(latitude, longitude)
        self.plotWindow.Refresh()
