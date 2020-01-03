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
import wx.lib.newevent

from .datasetattributespanel import DataSetAttributesPanel
from .geolocationpanel import GeolocationPanel
from .util import DetermineCharSize

CurrentDataSetChangedEvent, EVT_CURRENTDATASET_CHANGED = wx.lib.newevent.NewEvent()


class PlotDataSetPanel(wx.Panel):

    def __init__(self, parent, plotFrame):
        panelstyle = wx.TAB_TRAVERSAL
        if wx.Platform == '__WXGTK__':
            panelstyle |= wx.SUNKEN_BORDER
        wx.Panel.__init__(self, parent, -1, style=panelstyle)

        # Set initial state
        self.plotFrame = plotFrame

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
        self.dataSetLocationPanel = GeolocationPanel(self.dataSetPropertiesNotebook)
        self.dataSetPropertiesNotebook.AddPage(self.dataSetLocationPanel, "Location")

    def CreateLayout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.dataSetChoice, 0, wx.EXPAND | wx.ALL, border=10)
        sizer.Add(self.dataSetPropertiesNotebook, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=2)
        self.SetSizer(sizer)

    def UpdateDataSetList(self):
        oldDataSetId = self.dataSetChoice.GetSelection()
        self.dataSetChoice.Clear()
        for i in range(self.plotFrame.GetNumDataSets()):
            name = str(self.plotFrame.GetDataSetLabel(i))
            if not name:
                name = 'dataset #%d' % (i + 1)
            self.dataSetChoice.Insert(name, self.dataSetChoice.GetCount())
        if self.dataSetChoice.GetCount() > 0:
            newDataSetId = oldDataSetId
            if newDataSetId < 0 or newDataSetId >= self.dataSetChoice.GetCount():
                newDataSetId = 0
            self.dataSetChoice.Select(newDataSetId)
            if newDataSetId != oldDataSetId:
                self.UpdateAttributes()
                self.UpdateLocation()

    def UpdateAttributes(self):
        dataSetId = self.dataSetChoice.GetSelection()
        if dataSetId >= 0:
            attributes = self.plotFrame.dataSetAttributes[dataSetId]
            keyframe = self.plotFrame.GetKeyframe()
            self.dataSetAttributesPanel.UpdateAttributes(attributes, keyframe)
            self.Update()

    def UpdateLocation(self):
        dataSetId = self.dataSetChoice.GetSelection()
        if dataSetId >= 0 and not self.plotFrame.closingDown:
            location = self.plotFrame.dataSetLocation[dataSetId]
            keyframe = self.plotFrame.GetKeyframe()
            self.dataSetLocationPanel.UpdateLocation(dataSetId, location, keyframe)
            self.Update()

    def OnDataSetSelectionChanged(self, event):
        self.UpdateAttributes()
        self.UpdateLocation()
        dataSetId = self.dataSetChoice.GetSelection()
        if dataSetId >= 0:
            wx.PostEvent(self, CurrentDataSetChangedEvent(dataSetId=dataSetId))
