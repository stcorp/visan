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

import numpy
import wx
import wx.lib.newevent

from .util import DetermineCharSize

ValueChangedEvent, EVT_VALUE_CHANGED = wx.lib.newevent.NewCommandEvent()


class ColorBar(wx.Panel):

    def __init__(self, parent, showTicks=False):
        wx.Panel.__init__(self, parent, -1)

        self.colorTable = None
        self.showTicks = showTicks
        self.selectedTick = -1
        self.observertag = -1

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)

        self.UpdateBitmap()

    def SetColorTable(self, colorTable):
        def onColorTableChanged(caller, event, calldata=None):
            self.UpdateBitmap()
        if self.colorTable is not None:
            self.colorTable.RemoveObserver(self.observertag)
        self.colorTable = colorTable
        if self.colorTable is not None:
            self.observertag = self.colorTable.AddObserver("ColorTableChanged", onColorTableChanged)
        self.UpdateBitmap()

    def SelectTick(self, tickId):
        if tickId != self.selectedTick:
            self.selectedTick = tickId
            if self.showTicks:
                self.UpdateBitmap()

    def ShowTicks(self, show=True):
        if self.showTicks != show:
            self.showTicks = show
            self.UpdateBitmap()

    def UpdateBitmap(self):
        width, height = self.GetSize()
        width = max(width, 1)
        height = max(height, 1)

        arr = numpy.empty(shape=(height, width, 4), dtype='u1')
        if arr.size == 0:
            return
        arr[:] = 0

        if self.colorTable is not None:
            for x in range(width):
                index = (x * self.colorTable.GetNumTableColors()) / width
                r, g, b, a = self.colorTable.GetTableColor(index)
                arr[:, x, 0] = r * 255
                arr[:, x, 1] = g * 255
                arr[:, x, 2] = b * 255
                arr[:, x, 3] = a * 255

            tickHeight = 10
            if self.showTicks and height > tickHeight:
                arr[height - tickHeight:height, :, :] = 0
                for index in range(self.colorTable.GetNumGradientEdges()):
                    tickPos = int(self.colorTable.GetGradientEdgeValue(index)[0] * (width - 1))
                    arr[height - tickHeight + 2:height, tickPos, 3] = 255
                    if index == self.selectedTick:
                        if tickPos > 0:
                            arr[height - 1, tickPos - 4:tickPos, 3] = 255
                            arr[height - 2, tickPos - 3:tickPos, 3] = 255
                            arr[height - 3, tickPos - 2:tickPos, 3] = 255
                            arr[height - 4, tickPos - 1, 3] = 255
                        if tickPos < width - 1:
                            arr[height - 1, tickPos + 1:tickPos + 5, 3] = 255
                            arr[height - 2, tickPos + 1:tickPos + 4, 3] = 255
                            arr[height - 3, tickPos + 1:tickPos + 3, 3] = 255
                            arr[height - 4, tickPos + 1, 3] = 255

        self.bitmap = wx.Bitmap.FromBufferRGBA(width, height, arr)
        self.Refresh()

    def OnSize(self, evt):
        self.UpdateBitmap()

    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bitmap, 0, 0, True)


class ColorBox(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)

        self.color = [0.0, 0.0, 0.0, 1.0]
        self.UpdateBitmap()

    def SetColor(self, color):
        self.color = color
        self.UpdateBitmap()

    def UpdateBitmap(self):
        width, height = self.GetSize()
        width = max(width, 1)
        height = max(height, 1)

        arr = numpy.empty(shape=(height, width, 4), dtype='u1')
        arr[:, :, 0] = self.color[0] * 255
        arr[:, :, 1] = self.color[1] * 255
        arr[:, :, 2] = self.color[2] * 255
        arr[:, :, 3] = self.color[3] * 255
        self.bitmap = wx.Bitmap.FromBufferRGBA(width, height, arr)
        self.Refresh()

    def OnSize(self, evt):
        self.UpdateBitmap()

    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bitmap, 0, 0, True)


class ValueSlider(wx.Panel):

    def __init__(self, parent, title, minValue=0, maxValue=255):
        wx.Panel.__init__(self, parent, -1)

        self.parent = parent
        self.hasfocus = False
        self.title = title
        self.minValue = int(minValue)
        self.maxValue = int(maxValue)

        # Create and configure all widgets
        self.CreateControls()
        self.CreateLayout()

    def CreateControls(self):
        (charWidth, charHeight) = DetermineCharSize(self)

        self.label = wx.StaticText(self, -1, "%s:" % self.title)

        self.slider = wx.Slider(self, -1, value=0, minValue=self.minValue, maxValue=self.maxValue, size=(120, -1))
        self.slider.Bind(wx.EVT_SLIDER, self.OnSlider)

        self.text = wx.TextCtrl(self, -1, "0", style=wx.TE_PROCESS_ENTER | wx.TE_RIGHT, size=(4 * charWidth, -1))
        self.text.Bind(wx.EVT_TEXT_ENTER, self.OnText)
        self.text.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
        self.text.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)

    def CreateLayout(self):
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.label, 0, wx.ALIGN_CENTRE | wx.RIGHT, border=3)
        self.sizer.Add(self.slider, 1, wx.ALIGN_CENTRE | wx.RIGHT, border=5)
        self.sizer.Add(self.text, 0, wx.ALIGN_CENTRE)
        self.SetSizer(self.sizer)

    def GetValue(self):
        assert str(self.slider.GetValue()) == self.text.GetValue()
        return self.slider.GetValue()

    def SetValue(self, value):
        self.slider.SetValue(int(value))
        self.text.SetValue(str(int(value)))

    def SetRange(self, minValue, maxValue):
        if minValue != self.minValue or maxValue != self.maxValue:
            self.minValue = minValue
            self.maxValue = maxValue
            self.slider.SetRange(self.minValue, self.maxValue)
            self.text.SetValue(str(self.slider.GetValue()))

    def OnSlider(self, event):
        self.text.SetValue(str(self.slider.GetValue()))
        wx.PostEvent(self, ValueChangedEvent(self.GetId()))
        if wx.Platform == '__WXMAC__':
            wx.Yield()

    def OnText(self, event):
        self.slider.SetValue(max(min(int(self.text.GetValue()), self.maxValue), self.minValue))
        wx.PostEvent(self, ValueChangedEvent(self.GetId()))
        if wx.Platform == '__WXMAC__':
            wx.Yield()

    def OnSetFocus(self, event):
        self.hasfocus = True
        self.text.SetSelection(-1, -1)
        event.Skip()

    def OnKillFocus(self, event):
        self.slider.SetValue(max(min(int(self.text.GetValue()), self.maxValue), self.minValue))
        if self.hasfocus:
            self.text.SetSelection(0, 0)
            self.hasfocus = False
        wx.PostEvent(self, ValueChangedEvent(self.GetId()))
        if wx.Platform == '__WXMAC__':
            wx.Yield()
        event.Skip()


class ColorTablePanel(wx.Panel):

    def __init__(self, parent, plotWindow):
        panelstyle = wx.TAB_TRAVERSAL
        if wx.Platform == '__WXGTK__':
            panelstyle |= wx.SUNKEN_BORDER
        wx.Panel.__init__(self, parent, -1, style=panelstyle)

        # Set initial state
        self.liveUpdate = True
        self.colorTable = None
        self.plotWindow = plotWindow
        self.xSliderScale = 1000
        self.currentIndex = 0
        self.observertag = -1

        # Create and configure all widgets
        self.CreateControls()
        self.CreateLayout()

        self.UpdateAll()

    def CreateControls(self):
        (charWidth, charHeight) = DetermineCharSize(self)

        self.namedColorTableChoice = wx.Choice(self, -1, size=(10 * charWidth, -1),
                                               choices=["", "Default", "BlackToWhite", "WhiteToBlack", "GreenToRed",
                                                        "RedToGreen", "Cloud", "Rainbow", "Ozone", "Blackbody",
                                                        "Aerosol"])
        self.namedColorTableChoice.Bind(wx.EVT_CHOICE, self.OnNamedColorTabelChoice)

        self.colorBar = ColorBar(self, showTicks=True)
        self.colorBar.SetSize((100, 40))
        self.colorBar.SelectTick(0)

        self.pointLabel = wx.StaticText(self, -1, "Gradient Edge Point:")

        self.pointChoice = wx.Choice(self, -1, name="Gradient Edge Point:", size=(3 * charWidth, -1))
        self.pointChoice.Bind(wx.EVT_CHOICE, self.OnEdgePointChanged)

        self.xSlider = ValueSlider(self, 'X', 0, self.xSliderScale)
        self.xSlider.Bind(EVT_VALUE_CHANGED, self.OnValueChanged)

        self.rSlider = ValueSlider(self, 'R')
        self.rSlider.Bind(EVT_VALUE_CHANGED, self.OnValueChanged)

        self.gSlider = ValueSlider(self, 'G')
        self.gSlider.Bind(EVT_VALUE_CHANGED, self.OnValueChanged)

        self.bSlider = ValueSlider(self, 'B')
        self.bSlider.Bind(EVT_VALUE_CHANGED, self.OnValueChanged)

        self.aSlider = ValueSlider(self, 'A')
        self.aSlider.Bind(EVT_VALUE_CHANGED, self.OnValueChanged)
        self.aSlider.SetValue(255)

        self.colorBox = ColorBox(self)
        self.colorBox.SetSize((50, 50))
        self.colorBox.SetColor(self.GetColor())

        self.insertButton = wx.Button(self, -1, "Add Point")
        self.Bind(wx.EVT_BUTTON, self.OnInsert)

        self.removeButton = wx.Button(self, -1, "Remove Point")
        self.removeButton.Bind(wx.EVT_BUTTON, self.OnRemove)

        self.liveUpdateCtrl = wx.CheckBox(self, -1, "Live update")
        self.liveUpdateCtrl.SetToolTip(wx.ToolTip("If disabled, you will only see color table changes in the plot "
                                                  "area once you interact with the plot area (e.g. click in it with "
                                                  "the mouse). Since updating the plot area can be time consuming, "
                                                  "disabling this option allows you to quickly edit a color table"))
        self.liveUpdateCtrl.Bind(wx.EVT_CHECKBOX, self.OnLiveUpdate)
        self.liveUpdateCtrl.SetValue(True)

    def CreateLayout(self):
        butsizer = wx.BoxSizer(wx.HORIZONTAL)
        butsizer.Add(self.insertButton, 0, wx.ALIGN_LEFT | wx.ALL, border=5)
        butsizer.Add(self.removeButton, 0, wx.ALIGN_RIGHT | wx.ALL, border=5)

        colorslidersizer = wx.BoxSizer(wx.VERTICAL)
        colorslidersizer.Add(self.xSlider, 1, wx.EXPAND | wx.BOTTOM, border=10)
        colorslidersizer.Add(self.rSlider, 1, wx.EXPAND | wx.BOTTOM, border=5)
        colorslidersizer.Add(self.gSlider, 1, wx.EXPAND | wx.BOTTOM, border=5)
        colorslidersizer.Add(self.bSlider, 1, wx.EXPAND | wx.BOTTOM, border=10)
        colorslidersizer.Add(self.aSlider, 1, wx.EXPAND)

        colorsizer = wx.BoxSizer(wx.HORIZONTAL)
        colorsizer.Add(colorslidersizer, 1, wx.EXPAND | wx.ALIGN_LEFT)
        colorsizer.Add((10, 0), 0)
        colorsizer.Add(self.colorBox, 0, wx.ALIGN_LEFT)

        pointchoicesizer = wx.BoxSizer(wx.HORIZONTAL)
        pointchoicesizer.Add(self.pointLabel, 0, wx.ALIGN_LEFT)
        pointchoicesizer.Add(self.pointChoice, 1, wx.EXPAND | wx.ALIGN_LEFT | wx.LEFT, border=10)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.namedColorTableChoice, 0, wx.EXPAND | wx.ALL, border=5)
        sizer.Add(self.colorBar, 0, wx.EXPAND | wx.ALL, border=5)
        sizer.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND | wx.TOP | wx.BOTTOM, border=5)
        sizer.Add(pointchoicesizer, 0, wx.EXPAND | wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT, border=5)
        sizer.Add(butsizer, 0, wx.ALIGN_RIGHT)
        sizer.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND | wx.TOP | wx.BOTTOM, border=5)
        sizer.Add(colorsizer, 0, wx.EXPAND | wx.ALIGN_RIGHT | wx.ALL, border=5)
        sizer.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND | wx.TOP | wx.BOTTOM, border=5)
        sizer.Add(self.liveUpdateCtrl, 0, wx.ALIGN_RIGHT | wx.TOP | wx.RIGHT, border=5)

        self.SetSizer(sizer)

    def SetColorTable(self, colorTable):
        def onColorTableChanged(caller, event, calldata=None):
            self.UpdateAll()
            if self.liveUpdate:
                self.plotWindow.Refresh()
        if self.colorTable is not None:
            self.colorTable.RemoveObserver(self.observertag)
        self.colorTable = colorTable
        if self.colorTable is not None:
            self.observertag = self.colorTable.AddObserver("ColorTableChanged", onColorTableChanged)
        self.UpdateAll()

    def GetColor(self):
        r = float(self.rSlider.GetValue()) / 255.
        g = float(self.gSlider.GetValue()) / 255.
        b = float(self.bSlider.GetValue()) / 255.
        a = float(self.aSlider.GetValue()) / 255.
        return (r, g, b, a)

    def SetColor(self, color):
        self.rSlider.SetValue(int(color[0] * 255))
        self.gSlider.SetValue(int(color[1] * 255))
        self.bSlider.SetValue(int(color[2] * 255))
        self.aSlider.SetValue(int(color[3] * 255))
        self.colorBox.SetColor(color)

    def GetEdgePosition(self):
        return float(self.xSlider.GetValue()) / self.xSliderScale

    def SetEdgePosition(self, x):
        self.xSlider.SetValue(x * self.xSliderScale)

    def OnNamedColorTabelChoice(self, event):
        name = self.namedColorTableChoice.GetStringSelection()
        if name != "":
            self.colorTable.SetColorTableByName(name)

    def OnValueChanged(self, event):
        r, g, b, a = self.GetColor()
        x = self.GetEdgePosition()
        self.colorTable.SetGradientEdgeValue(self.currentIndex, x, r, g, b, a)

    def OnEdgePointChanged(self, event):
        self.currentIndex = self.pointChoice.GetSelection()
        self.colorBar.SelectTick(self.currentIndex)
        self.UpdateEdgePoint()

    def OnInsert(self, event):
        r, g, b, a = self.GetColor()
        x = self.GetEdgePosition()
        if self.currentIndex == 0:
            x = (x + self.colorTable.GetGradientEdgeValue(self.currentIndex + 1)[0]) / 2.0
        else:
            x = (x + self.colorTable.GetGradientEdgeValue(self.currentIndex - 1)[0]) / 2.0
        newIndex = self.colorTable.InsertGradientEdgeValue(x, r, g, b, a)
        # A refresh will automatically happen via the OnColorTableChanged event handler
        if newIndex != self.currentIndex:
            self.currentIndex = newIndex
            self.colorBar.SelectTick(self.currentIndex)
            self.UpdateEdgePoint()

    def OnRemove(self, event):
        self.colorTable.RemoveGradientEdgeValue(self.currentIndex)
        # A refresh will automatically happen via the OnColorTableChanged event handler

    def OnLiveUpdate(self, event):
        self.liveUpdate = self.liveUpdateCtrl.IsChecked()
        if self.liveUpdate:
            self.plotWindow.Refresh()

    def UpdateEdgePoint(self):
        x, r, g, b, a = self.colorTable.GetGradientEdgeValue(self.currentIndex)
        sliderMin = 0
        if self.currentIndex > 0:
            sliderMin = self.colorTable.GetGradientEdgeValue(self.currentIndex - 1)[0] + 1.0 / self.xSliderScale
        sliderMax = 1
        if self.currentIndex < self.colorTable.GetNumGradientEdges() - 1:
            sliderMax = self.colorTable.GetGradientEdgeValue(self.currentIndex + 1)[0] - 1.0 / self.xSliderScale
        self.xSlider.SetRange(sliderMin * self.xSliderScale, sliderMax * self.xSliderScale)
        self.SetColor((r, g, b, a))
        self.SetEdgePosition(x)

        modifiableEdge = self.currentIndex > 0 and self.currentIndex < self.colorTable.GetNumGradientEdges() - 1
        self.xSlider.Enable(modifiableEdge)
        self.removeButton.Enable(modifiableEdge)

    def UpdateAll(self):
        if self.colorTable is not None:
            name = str(self.colorTable.GetColorTableName())
            if name is None:
                self.namedColorTableChoice.SetSelection(0)
            else:
                self.namedColorTableChoice.SetStringSelection(name)
            numEdges = self.colorTable.GetNumGradientEdges()
            if self.currentIndex >= numEdges:
                self.currentIndex = numEdges - 1
            self.pointChoice.SetItems([str(i) for i in range(numEdges)])
            self.pointChoice.Select(self.currentIndex)
            self.colorBar.SelectTick(self.currentIndex)
            self.UpdateEdgePoint()
        else:
            self.namedColorTableChoice.SetSelection(0)
            self.namedColorTableChoice.Disable()
            self.colorBar.SelectTick(-1)
        self.namedColorTableChoice.Enable(self.colorTable is not None)
        self.pointChoice.Enable(self.colorTable is not None)
        self.insertButton.Enable(self.colorTable is not None)
        self.removeButton.Enable(self.colorTable is not None)
        self.xSlider.Enable(self.colorTable is not None)
        self.rSlider.Enable(self.colorTable is not None)
        self.gSlider.Enable(self.colorTable is not None)
        self.bSlider.Enable(self.colorTable is not None)
        self.aSlider.Enable(self.colorTable is not None)
