# Copyright (C) 2002-2020 S[&]T, The Netherlands.
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


class ColorBarPanel(wx.Panel):

    def __init__(self, parent, plotWindow):
        panelstyle = wx.TAB_TRAVERSAL
        if wx.Platform == '__WXGTK__':
            panelstyle |= wx.SUNKEN_BORDER
        wx.Panel.__init__(self, parent, -1, style=panelstyle)

        # Set initial state
        self.plotWindow = plotWindow

        # Create and configure all widgets
        self.CreateControls()
        self.CreateLayout()

    def CreateControls(self):
        (charWidth, charHeight) = DetermineCharSize(self)

        self.titleCtrl = LabeledTextCtrl(self, -1, label="Color Bar Title:", value="",
                                         size=(10 * charWidth, -1), style=wx.TE_PROCESS_ENTER)
        self.titleCtrl.SetToolTip(wx.ToolTip("This title will be shown just above the color bar and should "
                                             "contain information on the physical unit."))
        self.titleCtrl.Bind(EVT_VALUE_CHANGED, self.OnTitle)

        self.numLabelsCtrl = LabeledTextCtrl(self, -1, label="Number of labels:", validator=DigitValidator(),
                                             size=(3 * charWidth, -1), style=wx.TE_PROCESS_ENTER)
        self.numLabelsCtrl.SetToolTip(wx.ToolTip("Number of labels shown on the plot's color bar."))
        self.numLabelsCtrl.Bind(EVT_VALUE_CHANGED, self.OnNumLabels)

        # static boxes should be created before the controls they contain in order to preserve the correct Z-Order
        self.rangeBox = wx.StaticBox(self, -1, "Range")

        self.rangeMinCtrl = LabeledTextCtrl(self, -1, label="Min:", value="0", validator=FloatValidator(),
                                            formatstring="%g", size=(5 * charWidth, -1),
                                            style=wx.TE_PROCESS_ENTER)
        self.rangeMinCtrl.SetToolTip(wx.ToolTip("Minimium value to use for the color range."))
        self.rangeMinCtrl.Bind(EVT_VALUE_CHANGED, self.OnRange)

        self.rangeMaxCtrl = LabeledTextCtrl(self, -1, label="Max:", value="1", formatstring="%g",
                                            validator=FloatValidator(), size=(5 * charWidth, -1),
                                            style=wx.TE_PROCESS_ENTER)
        self.rangeMaxCtrl.SetToolTip(wx.ToolTip("Maximum value to use for the color range."))
        self.rangeMaxCtrl.Bind(EVT_VALUE_CHANGED, self.OnRange)

        self.UpdateControls()

    def CreateLayout(self):
        spacing = 10
        if wx.Platform == '__WXMAC__':
            spacing = 6

        self.hsizer3 = wx.BoxSizer(wx.HORIZONTAL)
        self.hsizer3.Add((spacing, 0), 0)
        self.hsizer3.Add(self.rangeMinCtrl, 0, wx.RIGHT, border=spacing)
        self.hsizer3.Add(self.rangeMaxCtrl, 0)

        self.vsizer2 = wx.StaticBoxSizer(self.rangeBox, wx.VERTICAL)
        self.vsizer2.Add((0, spacing), 0)
        self.vsizer2.Add(self.hsizer3, 1, wx.LEFT | wx.RIGHT, border=spacing / 2)
        self.vsizer2.Add((0, spacing), 0)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.titleCtrl, 0, wx.EXPAND | wx.ALL, border=spacing / 2)
        self.sizer.Add((0, spacing), 0)
        self.sizer.Add(self.numLabelsCtrl, 0, wx.LEFT | wx.RIGHT, border=spacing / 2)
        self.sizer.Add((0, spacing), 0)
        self.sizer.Add(self.vsizer2, 0, wx.EXPAND)

        self.mainsizer = wx.BoxSizer(wx.VERTICAL)
        self.mainsizer.Add(self.sizer, 1, wx.EXPAND | wx.ALL, border=spacing)

        self.SetSizerAndFit(self.mainsizer)

    def UpdateControls(self, dataSetId=None):
        if dataSetId is None:
            dataSetId = self.plotWindow.GetDataSetForColorBar()
        if dataSetId >= 0:
            self.titleCtrl.SetValue(self.plotWindow.GetColorBarTitle(dataSetId))
            self.colorRange = self.plotWindow.GetColorRange(dataSetId)
            self.numLabels = self.plotWindow.GetNumColorBarLabels(dataSetId)
        else:
            self.titleCtrl.SetValue("")
            self.colorRange = [0, 1]
            self.numLabels = 2
        self.numLabelsCtrl.SetValue(self.numLabels)
        self.rangeMinCtrl.SetValue(self.colorRange[0])
        self.rangeMaxCtrl.SetValue(self.colorRange[1])

        # Update enabled state of text fields
        self.titleCtrl.Enable(dataSetId >= 0)
        self.numLabelsCtrl.Enable(dataSetId >= 0)
        self.rangeMinCtrl.Enable(dataSetId >= 0)
        self.rangeMaxCtrl.Enable(dataSetId >= 0)

    def OnTitle(self, event):
        dataSetId = self.plotWindow.GetDataSetForColorBar()
        if dataSetId >= 0:
            curTitle = str(self.plotWindow.GetColorBarTitle(dataSetId))
            newTitle = str(self.titleCtrl.GetValue())
            # Check if the new value is different
            if newTitle != curTitle:
                self.plotWindow.SetColorBarTitle(dataSetId, str(self.titleCtrl.GetValue()))

    def OnNumLabels(self, event):
        try:
            value = int(self.numLabelsCtrl.GetValue())
        except ValueError:
            wx.Bell()
            self.numLabelsCtrl.SetValue(self.numLabels)
            return
        if value < 0:
            wx.Bell()
            self.numLabelsCtrl.SetValue(self.numLabels)
            return
        self.numLabels = value
        dataSetId = self.plotWindow.GetDataSetForColorBar()
        if dataSetId >= 0:
            self.plotWindow.SetNumColorBarLabels(dataSetId, self.numLabels)

    def OnRange(self, event):
        try:
            value = [float(self.rangeMinCtrl.GetValue()), float(self.rangeMaxCtrl.GetValue())]
        except ValueError:
            wx.Bell()
            self.rangeMinCtrl.SetValue(self.colorRange[0])
            self.rangeMaxCtrl.SetValue(self.colorRange[1])
            return
        if value[0] > value[1]:
            wx.Bell()
            self.rangeMinCtrl.SetValue(self.colorRange[0])
            self.rangeMaxCtrl.SetValue(self.colorRange[1])
            return
        self.colorRange = value
        dataSetId = self.plotWindow.GetDataSetForColorBar()
        if dataSetId >= 0:
            self.plotWindow.SetColorRange(dataSetId, self.colorRange[0], self.colorRange[1])
