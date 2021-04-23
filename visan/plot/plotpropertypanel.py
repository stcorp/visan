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

import wx

from .axispropertypanel import AxisPropertyPanel
from .labeledtextctrl import LabeledTextCtrl, EVT_VALUE_CHANGED
from .plotwindow import X_AXIS, Y_AXIS
from .util import DetermineCharSize


class PlotPropertyPanel(wx.Panel):

    def __init__(self, parent, plotWindow):
        windowstyle = wx.TAB_TRAVERSAL
        if wx.Platform == '__WXGTK__':
            windowstyle |= wx.SUNKEN_BORDER
        wx.Panel.__init__(self, parent, -1, style=windowstyle)

        # Set initial state
        self.plotFrame = parent
        self.plotWindow = plotWindow

        # Create and configure all widgets
        self.CreateControls()
        self.CreateLayout()

    def CreateControls(self):
        (charWidth, charHeight) = DetermineCharSize(self)

        self.titleCtrl = LabeledTextCtrl(self, -1, label="Plot Title:", value=self.plotWindow.GetPlotTitle(),
                                         size=(10 * charWidth, -1), style=wx.TE_PROCESS_ENTER)
        self.titleCtrl.SetToolTip(wx.ToolTip("The plot title will be displayed centered at the top of the plot."))
        self.titleCtrl.Bind(EVT_VALUE_CHANGED, self.OnTitle)

        self.axisNotebook = wx.Notebook(self, -1)

        self.xAxisPanel = AxisPropertyPanel(self.axisNotebook, self.plotWindow, X_AXIS)
        self.axisNotebook.AddPage(self.xAxisPanel, "X-Axis")

        self.yAxisPanel = AxisPropertyPanel(self.axisNotebook, self.plotWindow, Y_AXIS)
        self.axisNotebook.AddPage(self.yAxisPanel, "Y-Axis")

    def CreateLayout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.titleCtrl, 0, wx.EXPAND | wx.ALL, border=10)
        sizer.Add(self.axisNotebook, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=2)

        self.SetSizerAndFit(sizer)

    def UpdateControls(self):
        self.titleCtrl.SetValue(self.plotWindow.GetPlotTitle())
        self.xAxisPanel.UpdateControls()
        self.yAxisPanel.UpdateControls()

    def UpdateAxes(self):
        self.xAxisPanel.UpdateRangeFromPlot()
        self.yAxisPanel.UpdateRangeFromPlot()

    def OnTitle(self, event):
        self.plotWindow.SetPlotTitle(event.value)
