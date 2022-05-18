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
from .validators import DigitValidator, FloatValidator


class AxisPropertyPanel(wx.Panel):

    def __init__(self, parent, plotWindow, axisId):
        panelstyle = wx.TAB_TRAVERSAL
        if wx.Platform == '__WXGTK__':
            panelstyle |= wx.SUNKEN_BORDER
        wx.Panel.__init__(self, parent, -1, style=panelstyle)

        self.plotWindow = plotWindow
        self.maxTicks = 50
        self.axisId = axisId

        # Create and configure all widgets
        self.CreateControls()
        self.CreateLayout()

    def CreateControls(self):
        (charWidth, charHeight) = DetermineCharSize(self)

        # static boxes should be created before the controls they contain in order to preserve the correct Z-Order
        self.rangeBox = wx.StaticBox(self, -1, "Range")

        self.TitleCtrl = LabeledTextCtrl(self, -1, label="Label:", size=(8 * charWidth, -1), style=wx.TE_PROCESS_ENTER)
        self.TitleCtrl.SetValue(self.plotWindow.GetAxisTitle(self.axisId))
        self.TitleCtrl.SetToolTip(wx.ToolTip("The axis title will be displayed centered on the outside of the axis "
                                             "in the plot panel."))
        self.TitleCtrl.Bind(EVT_VALUE_CHANGED, self.OnTitle)

        self.LogAxisCtrl = wx.CheckBox(self, -1, "Logarithmic Scale")
        self.LogAxisCtrl.SetValue(self.plotWindow.GetLogAxis(self.axisId))
        self.LogAxisCtrl.SetToolTip(wx.ToolTip("Use a logarithmic axis. Disabled if the current range of axis values "
                                               "contains the number 0."))
        self.LogAxisCtrl.Bind(wx.EVT_CHECKBOX, self.OnLog)

        self.NTicksCtrl = LabeledTextCtrl(self, -1, label="Nr of Ticks:", validator=DigitValidator(),
                                          size=(3 * charWidth, -1), style=wx.TE_PROCESS_ENTER)
        self.NTicksCtrl.SetValue(self.plotWindow.GetNumAxisLabels(self.axisId))
        self.NTicksCtrl.SetToolTip(wx.ToolTip("The target number of ticks to display on the axis. "
                                              "The actual number of ticks is calculated; this control's value is "
                                              "what the calculation will try to aim for."))
        self.NTicksCtrl.Bind(EVT_VALUE_CHANGED, self.OnNTicks)

        self.BaseCtrl = LabeledTextCtrl(self, -1, label="Base:", validator=FloatValidator(), formatstring="%-#.3g",
                                        size=(5 * charWidth, -1), style=wx.TE_PROCESS_ENTER)
        self.BaseCtrl.SetValue(self.plotWindow.GetAxisBase(self.axisId))
        self.BaseCtrl.SetToolTip(wx.ToolTip("The base for the linear and logarithmic tick calculation for the axis. "
                                            "This value can be fractional but must be greater than 1."))
        self.BaseCtrl.Bind(EVT_VALUE_CHANGED, self.OnBase)

        self.MinCtrl = LabeledTextCtrl(self, -1, label="Min:", validator=FloatValidator(), formatstring="%-#.3g",
                                       size=(5 * charWidth, -1), style=wx.TE_PROCESS_ENTER)
        self.MinCtrl.SetValue(self.plotWindow.GetAxisRangeMin(self.axisId))
        self.MinCtrl.SetToolTip(wx.ToolTip("The currently displayed minimum range value."))
        self.MinCtrl.Bind(EVT_VALUE_CHANGED, self.OnMin)

        self.MaxCtrl = LabeledTextCtrl(self, -1, label="Max:", validator=FloatValidator(), formatstring="%-#.3g",
                                       size=(5 * charWidth, -1), style=wx.TE_PROCESS_ENTER)
        self.MaxCtrl.SetValue(self.plotWindow.GetAxisRangeMax(self.axisId))
        self.MaxCtrl.SetToolTip(wx.ToolTip("The currently displayed maximum range value."))
        self.MaxCtrl.Bind(EVT_VALUE_CHANGED, self.OnMax)

    def CreateLayout(self):

        sizer0 = wx.BoxSizer(wx.HORIZONTAL)
        sizer0.Add(self.NTicksCtrl, 0, wx.RIGHT, border=10)
        sizer0.Add(self.BaseCtrl, 0)

        rsizer1 = wx.BoxSizer(wx.HORIZONTAL)
        rsizer1.Add((15, 0), 0)
        rsizer1.Add(self.MinCtrl, 0, wx.RIGHT, border=10)
        rsizer1.Add(self.MaxCtrl, 0)

        sizer1 = wx.StaticBoxSizer(self.rangeBox, wx.VERTICAL)
        sizer1.Add((0, 10), 0)
        sizer1.Add(rsizer1, 1, wx.LEFT | wx.RIGHT, border=5)
        sizer1.Add((0, 10), 0)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.TitleCtrl, 0, wx.EXPAND)
        sizer.Add((0, 10), 0)
        sizer.Add(self.LogAxisCtrl, 0)
        sizer.Add((0, 10), 0)
        sizer.Add(sizer0, 0, wx.EXPAND)
        sizer.Add((0, 15), 0)
        sizer.Add(sizer1, 0, wx.EXPAND)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(sizer, 1, wx.EXPAND | wx.ALL, border=10)

        self.SetSizerAndFit(mainSizer)

    def UpdateControls(self):
        # Retrieve and set the values of axis properties
        self.TitleCtrl.SetValue(self.plotWindow.GetAxisTitle(self.axisId))
        self.NTicksCtrl.SetValue(self.plotWindow.GetNumAxisLabels(self.axisId))
        self.LogAxisCtrl.SetValue(self.plotWindow.GetLogAxis(self.axisId))
        self.BaseCtrl.SetValue(self.plotWindow.GetAxisBase(self.axisId))
        self.UpdateRangeFromPlot()

    def UpdateRangeFromPlot(self):
        self.MinCtrl.SetValue(self.plotWindow.GetAxisRangeMin(self.axisId))
        self.MaxCtrl.SetValue(self.plotWindow.GetAxisRangeMax(self.axisId))

    def OnLog(self, event):
        curLog = self.plotWindow.GetLogAxis(self.axisId)
        newLog = self.LogAxisCtrl.IsChecked()

        # Check if the new value is different
        if newLog != curLog:
            self.plotWindow.SetLogAxis(self.axisId, newLog)
            self.UpdateRangeFromPlot()

    def OnBase(self, event):
        curBase = self.plotWindow.GetAxisBase(self.axisId)
        try:
            newBase = float(self.BaseCtrl.GetValue())
        except ValueError:
            wx.Bell()
            self.BaseCtrl.SetValue(curBase)
            return

        # Check if the new value is different
        if newBase != curBase:
            if newBase > 1:
                self.plotWindow.SetAxisBase(self.axisId, newBase)
            else:
                wx.Bell()
                self.BaseCtrl.SetValue(curBase)

    def OnTitle(self, event):
        curTitle = str(self.plotWindow.GetAxisTitle(self.axisId))
        newTitle = self.TitleCtrl.GetValue()

        # Check if the new value is different
        if newTitle != curTitle:
            self.plotWindow.SetAxisTitle(self.axisId, newTitle)

    def OnNTicks(self, event):
        curTicks = self.plotWindow.GetNumAxisLabels(self.axisId)
        try:
            newTicks = int(self.NTicksCtrl.GetValue())
        except ValueError:
            wx.Bell()
            self.NTicksCtrl.SetValue(curTicks)
            return

        # Check if the new value is different
        if newTicks != curTicks:
            if 0 < newTicks <= self.maxTicks:
                self.plotWindow.SetNumAxisLabels(self.axisId, newTicks)
            else:
                wx.Bell()
                if newTicks > self.maxTicks:
                    self.NTicksCtrl.SetValue(self.maxTicks)
                else:
                    self.NTicksCtrl.SetValue(1)

    def OnMin(self, event):
        min = self.plotWindow.GetAxisRangeMin(self.axisId)
        try:
            newMin = float(self.MinCtrl.GetValue())
        except ValueError:
            wx.Bell()
            self.MinCtrl.SetValue(range.min())
            return

        # Check if the new value is different
        if newMin != min:
            self.plotWindow.SetAxisRange(self.axisId, newMin, self.plotWindow.GetAxisRangeMax(self.axisId))

    def OnMax(self, event):
        max = self.plotWindow.GetAxisRangeMax(self.axisId)
        try:
            newMax = float(self.MaxCtrl.GetValue())
        except ValueError:
            wx.Bell()
            self.MaxCtrl.SetValue(max)
            return

        # Check if the new value is different
        if newMax != max:
            self.plotWindow.SetAxisRange(self.axisId, self.plotWindow.GetAxisRangeMin(self.axisId), newMax)
