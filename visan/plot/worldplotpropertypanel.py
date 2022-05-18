# Copyright (C) 2002-2022 S[&]T, The Netherlands.
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

import wx

from .labeledtextctrl import LabeledTextCtrl, EVT_VALUE_CHANGED
from .util import DetermineCharSize
from .validators import FloatValidator
from .worldplotwindow import AZIMUTHAL_PROJECTIONS, CYLINDRICAL_PROJECTIONS, PROJECTIONS


class WorldPlotPropertyPanel(wx.Panel):

    def __init__(self, parent, worldplotWindow):
        panelstyle = wx.TAB_TRAVERSAL
        if wx.Platform == '__WXGTK__':
            panelstyle |= wx.SUNKEN_BORDER
        wx.Panel.__init__(self, parent, -1, style=panelstyle)

        self.plotWindow = worldplotWindow

        # Create and configure all widgets
        self.CreateControls()
        self.CreateLayout()

    def CreateControls(self):
        (charWidth, charHeight) = DetermineCharSize(self)

        self.titleCtrl = LabeledTextCtrl(self, -1, label="Plot Title:", value=self.plotWindow.GetPlotTitle(),
                                         size=(10 * charWidth, -1), style=wx.TE_PROCESS_ENTER)
        self.titleCtrl.SetToolTip(wx.ToolTip("The plot title will be displayed centered at the top of the plot."))
        self.titleCtrl.Bind(EVT_VALUE_CHANGED, self.OnTitle)

        # static boxes should be created before the controls they contain in order to preserve the correct Z-Order
        self.projCenterBox = wx.StaticBox(self, -1, "Center of Projection")
        self.viewCtrlBox = wx.StaticBox(self, -1, "View Center and Zoom")

        self.projectionLabel = wx.StaticText(self, -1, "Projection:", style=wx.ALIGN_RIGHT)

        self.projectionChoice = wx.Choice(self, -1, choices=PROJECTIONS)
        self.projectionChoice.SetToolTip(wx.ToolTip("Projection to use for mapping the world globe to the "
                                                    "2-dimensional plane."))
        self.projectionChoice.Bind(wx.EVT_CHOICE, self.OnProjectionChoice)

        self.projCenterLatitudeCtrl = LabeledTextCtrl(self, -1, label="Lat:", validator=FloatValidator(),
                                                      formatstring="%-#.4g", size=(5 * charWidth, -1),
                                                      style=wx.TE_PROCESS_ENTER)
        self.projCenterLatitudeCtrl.SetToolTip(wx.ToolTip("Latitude of the projection's center point."))
        self.projCenterLatitudeCtrl.Bind(EVT_VALUE_CHANGED, self.OnProjCenterLatitude)

        self.projCenterLongitudeCtrl = LabeledTextCtrl(self, -1, label="Lon:", validator=FloatValidator(),
                                                       formatstring="%-#.4g", size=(5 * charWidth, -1),
                                                       style=wx.TE_PROCESS_ENTER)
        self.projCenterLongitudeCtrl.SetToolTip(wx.ToolTip("Longitude of the projection's center point."))
        self.projCenterLongitudeCtrl.Bind(EVT_VALUE_CHANGED, self.OnProjCenterLongitude)

        self.viewCenterLatitudeCtrl = LabeledTextCtrl(self, -1, label="Lat:", validator=FloatValidator(),
                                                      formatstring="%#.4g", size=(5 * charWidth, -1),
                                                      style=wx.TE_PROCESS_ENTER)
        self.viewCenterLatitudeCtrl.SetToolTip(wx.ToolTip("Latitude of the view center point."))
        self.viewCenterLatitudeCtrl.Bind(EVT_VALUE_CHANGED, self.OnViewCenterLatitude)

        self.viewCenterLongitudeCtrl = LabeledTextCtrl(self, -1, label="Lon:", validator=FloatValidator(),
                                                       formatstring="%#.4g", size=(5 * charWidth, -1),
                                                       style=wx.TE_PROCESS_ENTER)
        self.viewCenterLongitudeCtrl.SetToolTip(wx.ToolTip("Latitude of the view center point."))
        self.viewCenterLongitudeCtrl.Bind(EVT_VALUE_CHANGED, self.OnViewCenterLongitude)

        self.zoomScaleCtrl = LabeledTextCtrl(self, -1, label="Zoom:", validator=FloatValidator(), formatstring="%#.3g",
                                             size=(5 * charWidth, -1), style=wx.TE_PROCESS_ENTER)
        self.zoomScaleCtrl.SetToolTip(wx.ToolTip("View scale around the view center."))
        self.zoomScaleCtrl.Bind(EVT_VALUE_CHANGED, self.OnZoomScale)

        self.UpdateControls()

    def CreateLayout(self):
        spacing = 10
        if wx.Platform == '__WXMAC__':
            spacing = 6

        self.hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.hsizer.Add(self.projectionLabel,  0, wx.ALIGN_CENTER | wx.RIGHT, border=spacing)
        self.hsizer.Add(self.projectionChoice, 0, wx.ALIGN_CENTER)

        self.hsizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.hsizer2.Add((spacing, 0), 0)
        self.hsizer2.Add(self.projCenterLatitudeCtrl, 0, wx.RIGHT, border=spacing)
        self.hsizer2.Add(self.projCenterLongitudeCtrl, 0)

        self.hsizer3 = wx.BoxSizer(wx.HORIZONTAL)
        self.hsizer3.Add((spacing, 0), 0)
        self.hsizer3.Add(self.viewCenterLatitudeCtrl, 0, wx.RIGHT, border=spacing)
        self.hsizer3.Add(self.viewCenterLongitudeCtrl, 0)

        self.hsizer4 = wx.BoxSizer(wx.HORIZONTAL)
        self.hsizer4.Add((spacing, 0), 0)
        self.hsizer4.Add(self.zoomScaleCtrl, 0, wx.RIGHT, border=spacing)

        self.vsizer = wx.StaticBoxSizer(self.projCenterBox, wx.VERTICAL)
        self.vsizer.Add((0, spacing), 0)
        self.vsizer.Add(self.hsizer2, 1, wx.LEFT | wx.RIGHT, border=spacing // 2)
        self.vsizer.Add((0, spacing), 0)

        self.vsizer2 = wx.StaticBoxSizer(self.viewCtrlBox, wx.VERTICAL)
        self.vsizer2.Add(self.hsizer3, 1, wx.LEFT | wx.RIGHT, border=spacing // 2)
        self.vsizer2.Add((0, spacing), 0)
        self.vsizer2.Add(self.hsizer4, 1, wx.LEFT | wx.RIGHT, border=spacing // 2)
        self.vsizer2.Add((0, spacing), 0)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.titleCtrl, 0, wx.EXPAND | wx.ALL, border=10)
        self.sizer.Add((0, spacing), 0)
        self.sizer.Add(self.hsizer, 0, wx.EXPAND)
        self.sizer.Add((0, spacing), 0)
        self.sizer.Add(self.vsizer, 0, wx.EXPAND)
        self.sizer.Add((0, spacing), 0)
        self.sizer.Add(self.vsizer2,  0, wx.EXPAND)

        self.mainsizer = wx.BoxSizer(wx.VERTICAL)
        self.mainsizer.Add(self.sizer, 1, wx.EXPAND | wx.ALL, border=spacing)

        self.SetSizerAndFit(self.mainsizer)

    def UpdateControls(self):
        # Retrieve and set the values of axis properties
        self.titleCtrl.SetValue(self.plotWindow.GetPlotTitle())
        projection = PROJECTIONS.index(self.plotWindow.GetProjection())
        self.projectionChoice.SetSelection(projection)
        self.projCenterLatitude = self.plotWindow.GetProjectionCenterLatitude()
        self.projCenterLatitudeCtrl.SetValue(self.projCenterLatitude)
        self.projCenterLongitude = self.plotWindow.GetProjectionCenterLongitude()
        self.projCenterLongitudeCtrl.SetValue(self.projCenterLongitude)

        self.viewCenterLatitude = self.plotWindow.GetViewCenterLatitude()
        self.viewCenterLatitudeCtrl.SetValue(self.viewCenterLatitude)
        self.viewCenterLongitude = self.plotWindow.GetViewCenterLongitude()
        self.viewCenterLongitudeCtrl.SetValue(self.viewCenterLongitude)
        self.zoomScale = self.plotWindow.GetViewZoom()
        self.zoomScaleCtrl.SetValue(self.zoomScale)

        # Update enabled state of text fields
        self.projCenterLatitudeCtrl.Enable(PROJECTIONS[projection] in AZIMUTHAL_PROJECTIONS)
        self.projCenterLongitudeCtrl.Enable(PROJECTIONS[projection] in CYLINDRICAL_PROJECTIONS or
                                            PROJECTIONS[projection] in AZIMUTHAL_PROJECTIONS)

    def OnTitle(self, event):
        self.plotWindow.SetPlotTitle(event.value)

    def OnProjectionChoice(self, event):
        self.plotWindow.SetProjection(PROJECTIONS[self.projectionChoice.GetSelection()])
        self.UpdateControls()

    def OnProjCenterLatitude(self, event):
        try:
            value = float(self.projCenterLatitudeCtrl.GetValue())
        except ValueError:
            wx.Bell()
            self.projCenterLatitudeCtrl.SetValue(self.projCenterLatitude)
            return
        if value < -90 or value > 90:
            wx.Bell()
            self.projCenterLatitudeCtrl.SetValue(self.projCenterLatitude)
            return
        self.projCenterLatitude = value
        self.plotWindow.SetProjectionCenterLatitude(self.projCenterLatitude)

    def OnProjCenterLongitude(self, event):
        try:
            value = float(self.projCenterLongitudeCtrl.GetValue())
        except ValueError:
            wx.Bell()
            self.projCenterLongitudeCtrl.SetValue(self.projCenterLongitude)
            return
        if value < -180 or value > 180:
            wx.Bell()
            self.projCenterLongitudeCtrl.SetValue(self.projCenterLongitude)
            return
        self.projCenterLongitude = value
        self.plotWindow.SetProjectionCenterLongitude(self.projCenterLongitude)

    def OnZoomScale(self, event):
        try:
            value = float(self.zoomScaleCtrl.GetValue())
        except ValueError:
            wx.Bell()
            self.zoomScaleCtrl.SetValue(self.zoomScale)
            return
        if value < 1.0:
            wx.Bell()
            self.zoomScaleCtrl.SetValue(self.zoomScale)
            return
        self.zoomScale = value
        self.plotWindow.SetViewZoom(self.zoomScale)

    def OnViewCenterLatitude(self, event):
        try:
            value = float(self.viewCenterLatitudeCtrl.GetValue())
        except ValueError:
            wx.Bell()
            self.viewCenterLatitudeCtrl.SetValue(self.viewCenterLatitude)
            return
        if value < -90 or value > 90:
            wx.Bell()
            self.viewCenterLatitudeCtrl.SetValue(self.viewCenterLatitude)
            return

        self.viewCenterLatitude = value
        self.plotWindow.SetViewCenter(self.viewCenterLatitude, self.viewCenterLongitude)

    def OnViewCenterLongitude(self, event):
        try:
            value = float(self.viewCenterLongitudeCtrl.GetValue())
        except ValueError:
            wx.Bell()
            self.viewCenterLongitudeCtrl.SetValue(self.viewCenterLongitude)
            return
        if value < -180 or value > 180:
            wx.Bell()
            self.viewCenterLongitudeCtrl.SetValue(self.viewCenterLongitude)
            return

        self.viewCenterLongitude = value
        self.plotWindow.SetViewCenter(self.viewCenterLatitude, self.viewCenterLongitude)
