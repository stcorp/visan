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

from .colorbarpanel import ColorBarPanel
from .colortablepanel import ColorTablePanel
from .datasetattributespanel import DataSetAttributesPanel
from .util import DetermineCharSize

CurrentDataSetChangedEvent, EVT_CURRENTDATASET_CHANGED = wx.lib.newevent.NewEvent()


class WorldPlotDataSetPanel(wx.Panel):

    def __init__(self, parent, plotFrame, plotWindow):
        panelstyle = wx.TAB_TRAVERSAL
        if wx.Platform == '__WXGTK__':
            panelstyle |= wx.SUNKEN_BORDER
        wx.Panel.__init__(self, parent, -1, style=panelstyle)

        # Set initial state
        self.plotFrame = plotFrame
        self.plotWindow = plotWindow

        # Create and configure all widgets
        self.CreateControls()
        self.CreateLayout()

        self.UpdateDataSetList()

    def CreateControls(self):
        (charWidth, charHeight) = DetermineCharSize(self)

        self.dataSetChoice = wx.Choice(self, -1, size=(10 * charWidth, -1))
        self.dataSetChoice.Bind(wx.EVT_CHOICE, self.OnDataSetSelectionChanged)

        self.dataSetPropertiesNotebook = wx.Notebook(self, -1)
        self.dataSetAttributesPanel = DataSetAttributesPanel(self.dataSetPropertiesNotebook)
        self.dataSetPropertiesNotebook.AddPage(self.dataSetAttributesPanel, "Attributes")
        self.colorTablePanel = ColorTablePanel(self.dataSetPropertiesNotebook, self.plotWindow)
        self.dataSetPropertiesNotebook.AddPage(self.colorTablePanel, "Color Table")
        self.colorBarPanel = ColorBarPanel(self.dataSetPropertiesNotebook, self.plotWindow)
        self.dataSetPropertiesNotebook.AddPage(self.colorBarPanel, "Color Bar")

    def CreateLayout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.dataSetChoice, 0, wx.EXPAND | wx.ALL, border=0)
        sizer.Add(self.dataSetPropertiesNotebook, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=2)
        self.SetSizer(sizer)

    def SelectDataSet(self, dataSetId):
        if dataSetId >= 0 and dataSetId < self.dataSetChoice.GetCount():
            self.dataSetChoice.Select(dataSetId)
            self.UpdateAttributes()
            self.UpdateColorTable()
            self.UpdateColorBar()

    def UpdateDataSetList(self):
        oldDataSetId = self.dataSetChoice.GetSelection()
        self.dataSetChoice.Clear()
        for i in range(self.plotFrame.GetNumDataSets()):
            name = self.plotFrame.GetDataSetLabel(i)
            if not name:
                name = 'dataset #%d' % (i+1)
            self.dataSetChoice.Insert(name, self.dataSetChoice.GetCount())
        if self.dataSetChoice.GetCount() > 0:
            newDataSetId = oldDataSetId
            if newDataSetId < 0 or newDataSetId >= self.dataSetChoice.GetCount():
                newDataSetId = 0
            self.dataSetChoice.Select(newDataSetId)
            if newDataSetId != oldDataSetId:
                self.UpdateAttributes()
                self.UpdateColorTable()
                self.UpdateColorBar()
        else:
            self.colorTablePanel.SetColorTable(None)

    def UpdateColorTable(self):
        dataSetId = self.dataSetChoice.GetSelection()
        self.colorTablePanel.SetColorTable(self.plotFrame.GetColorTable(dataSetId))

    def UpdateColorBar(self):
        dataSetId = self.dataSetChoice.GetSelection()
        self.colorBarPanel.UpdateControls(dataSetId)

    def UpdateAttributes(self):
        dataSetId = self.dataSetChoice.GetSelection()
        if dataSetId >= 0:
            attributes = self.plotFrame.dataSetAttributes[dataSetId]
            keyframe = self.plotFrame.GetKeyframe()
            self.dataSetAttributesPanel.UpdateAttributes(attributes, keyframe)
            self.Update()

    def OnDataSetSelectionChanged(self, event):
        self.UpdateAttributes()
        self.UpdateColorTable()
        self.UpdateColorBar()
        dataSetId = self.dataSetChoice.GetSelection()
        if dataSetId >= 0:
            wx.PostEvent(self, CurrentDataSetChangedEvent(dataSetId=dataSetId))
