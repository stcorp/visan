# Copyright (C) 2002-2019 S[&]T, The Netherlands.
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

import wx
import numpy

from .animationtoolbar import AnimationToolbar, EVT_KEYFRAME_CHANGED
from .plotdatasetpanel import PlotDataSetPanel
from .plotpropertypanel import PlotPropertyPanel
from .plotwindow import PlotWindow, EVT_PLOTDATA_CHANGED, EVT_PLOTAXIS_CHANGED
from .typedsavefiledialog import TypedSaveFileDialog

windowCount = 1


class PlotFrame(wx.Frame):

    def __init__(self, parent=None, id=-1, title=None, pos=wx.DefaultPosition, size=(800, 494)):
        if parent is None:
            # use top level wxWindow
            try:
                parent = wx.GetApp().GetTopWindow()
            except Exception:
                # If there is no top level window, just create parentless plot window
                pass
        if title is None:
            # determine title
            global windowCount
            title = "VISAN 2D Plot"
            if windowCount > 1:
                title += " - %d" % windowCount
            windowCount += 1
        super(PlotFrame, self).__init__(parent, id, title, pos, size)

        # Set icon if possible
        if wx.Config.Get().Read("IconFile"):
            self.SetIcon(wx.Icon(wx.Config.Get().Read("IconFile")))

        # Set initial state
        self.closingDown = False
        self.filename = ""
        self.dataSetAttributes = []
        self.dataSetLocation = []

        # Create and configure all widgets
        self.CreateMenuBar()
        self.CreateControls()
        self.CreateLayout()

        # Other Event Listeneres
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # Give the plotwindow the initial focus (since this might not happen automatically for e.g. Mac OS X)
        self.plotWindow.SetFocus()

        self.Show()
        wx.Yield()

    def __repr__(self):
        return "<visan plot handle>"

    def CreateMenuBar(self):
        menubar = wx.MenuBar()

        filemenu = wx.Menu()

        item = filemenu.Append(wx.ID_SAVE, "&Save Image...\tCtrl-S", "Save the image to an image file")
        self.Bind(wx.EVT_MENU, self.OnSave, item)

        filemenu.AppendSeparator()

        item = filemenu.Append(wx.ID_CLOSE, "&Close\tCtrl-W", "Close this Window")
        self.Bind(wx.EVT_MENU, self.OnClose, item)

        menubar.Append(filemenu, "&File")

        viewmenu = wx.Menu()

        self.viewPropertiesMenuItem = viewmenu.AppendCheckItem(wx.ID_ANY, "&Properties",
                                                               "Toggle the display of the Property Panel")
        self.Bind(wx.EVT_MENU, self.OnViewProps, self.viewPropertiesMenuItem)
        self.viewPropertiesMenuItem.Enable(True)

        self.viewSliderMenuItem = viewmenu.AppendCheckItem(wx.ID_ANY, "&Animation Toolbar",
                                                           "Toggle the display of the Animation Toolbar")
        self.Bind(wx.EVT_MENU, self.OnViewSlider, self.viewSliderMenuItem)
        self.viewSliderMenuItem.Enable(False)

        menubar.Append(viewmenu, "&View")

        self.SetMenuBar(menubar)

    def CreateControls(self):
        # Create a split panel
        splitterstyle = wx.SP_LIVE_UPDATE
        if wx.Platform == "__WXMAC__":
            splitterstyle |= wx.SP_3DSASH
        self.splitPanel = wx.SplitterWindow(self, -1, style=splitterstyle)
        self.splitPanel.Bind(wx.EVT_SIZE, self.OnSplitPanelSize)

        # Create the plot window
        self.plotWindow = PlotWindow(self.splitPanel, -1)
        self.plotWindow.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.plotWindow.Bind(EVT_PLOTDATA_CHANGED, self.OnPlotDataChanged)
        self.plotWindow.Bind(EVT_PLOTAXIS_CHANGED, self.OnPlotAxisChanged)
        self.plotWindow.Enable(1)

        # Create the animation toolbar
        self.animationToolbar = AnimationToolbar(self, self.plotWindow)
        self.animationToolbar.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.animationToolbar.Bind(EVT_KEYFRAME_CHANGED, self.OnKeyframeChanged)

        # Create the property panel
        # Create a parent wxWindow for the notebook to give a proper background colour for the area behind the tabs
        self.propertyPanel = wx.Window(self.splitPanel, -1)
        # Set the background 'explicitly' to have it stick
        self.propertyPanel.SetBackgroundColour(self.propertyPanel.GetBackgroundColour())
        self.propertyPanel.Bind(wx.EVT_SIZE, self.OnPropertyPanelSize)

        # Create the property notebook
        self.propertyNotebook = wx.Notebook(self.propertyPanel, -1)
        # Don't add size handler for propertyNotebook: re-layout of propertyNotebook doesn't work on Windows

        # Create the content for the property notebook
        self.dataSetPropertyTab = PlotDataSetPanel(self.propertyNotebook, self)
        self.dataSetPropertyTab.Bind(wx.EVT_SIZE, self.OnDataSetPropertyTabSize)
        self.plotPropertyTab = PlotPropertyPanel(self.propertyNotebook, self.plotWindow)
        self.plotPropertyTab.Bind(wx.EVT_SIZE, self.OnPlotPropertyTabSize)

        # Add the content to the notebook
        self.propertyNotebook.AddPage(self.dataSetPropertyTab, "Datasets")
        self.propertyNotebook.AddPage(self.plotPropertyTab, "Plot")

        # Initialize split panel
        self.splitPanel.SetMinimumPaneSize(50)
        self.splitPanel.Initialize(self.plotWindow)

    def CreateLayout(self):
        self.propertyPanelSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.propertyPanelSizer.Add(self.propertyNotebook, 1, wx.EXPAND)
        self.propertyPanel.SetSizerAndFit(self.propertyPanelSizer)

        self.splitPanelSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.splitPanelSizer.Add(self.plotWindow, 1, wx.EXPAND)
        self.splitPanelSizer.Add((self.splitPanel.GetSashSize(), -1), 0, wx.EXPAND)
        self.splitPanelSizer.Add(self.propertyPanel, 0, wx.EXPAND)
        self.splitPanelSizer.Show(1, False)
        self.splitPanelSizer.Show(2, False)
        self.splitPanel.SetSizer(self.splitPanelSizer)

        self.plotWindow.SetMinSize((80, 50))

        self.verticalSizer = wx.BoxSizer(wx.VERTICAL)
        self.verticalSizer.Add(self.splitPanel, 1, wx.EXPAND)
        self.verticalSizer.Add(self.animationToolbar, 0, wx.EXPAND)

        # Hide the animation toolbar by default (so it must be shown explicitly)
        self.verticalSizer.Hide(self.animationToolbar)

        # Hide the property panel by default (so it must be shown explicitly)
        self.propertyPanel.Hide()

        self.SetSizer(self.verticalSizer)
        self.Layout()
        self.UpdateMinSize()

    def UpdateMinSize(self):
        self.SetMinSize(self.GetBestSize())
        currentsize = self.GetSize()
        minsize = self.GetMinSize()
        if currentsize.x < minsize.x or currentsize.y < minsize.y:
            if currentsize.x < minsize.x:
                currentsize.x = minsize.x
            if currentsize.y < minsize.y:
                currentsize.y = minsize.y
            self.SetSize(currentsize)

    def AdjustSplitPanelSashPosition(self):
        # Update sash position in splitter window
        # Try to keep the size of the property pane the same
        sashPosition = -(self.propertyPanel.GetSize()[0] + self.splitPanel.GetSashSize())
        self.splitPanel.SetSashPosition(sashPosition)

    def ShowAnimationToolbar(self, show=True):
        try:
            show = bool(show)
        except ValueError:
            raise TypeError("Show Animation Toolbar parameter should be a boolean (was: '%s')" % str(show))
        self.viewSliderMenuItem.Check(show)

        self.verticalSizer.Show(self.animationToolbar, show)
        self.Layout()

        self.UpdateMinSize()
        self.Refresh()

    def ShowPropertyPanel(self, show=True):
        try:
            show = bool(show)
        except ValueError:
            raise TypeError("Show Property Panel parameter should be a boolean (was: '%s')" % str(show))
        self.viewPropertiesMenuItem.Check(show)

        if show:
            self.splitPanel.SplitVertically(self.plotWindow, self.propertyPanel)
            self.splitPanelSizer.Show(1, True)
            self.splitPanelSizer.Show(2, True)
            self.propertyPanel.Show()
            self.propertyPanel.Fit()
            self.AdjustSplitPanelSashPosition()
        else:
            self.splitPanel.Unsplit(self.propertyPanel)
            self.splitPanelSizer.Show(1, False)
            self.splitPanelSizer.Show(2, False)
        self.splitPanel.Layout()

        self.UpdateMinSize()
        self.Refresh()

    def AddDataSet(self, xdata, ydata):
        xarray = None
        yarray = None
        keyframeSize = None
        keyframeXOffset = None
        keyframeYOffset = None

        # convert ydata to numpy yarray
        if isinstance(ydata, numpy.ndarray):
            yarray = ydata
        else:
            try:
                yarray = numpy.asarray(ydata, dtype=numpy.double)
            except TypeError:
                raise TypeError("plot ydata argument cannot be converted to numpy array. %s" % str(ydata))
        if yarray.ndim == 0:
            # convert scalar to 1D array with one element
            yarray.setshape([1])
        if yarray.ndim > 2:
            raise ValueError("Cannot plot a %d-dimensional numpy array" % yarray.ndim)

        # convert xdata to numpy xarray (if it is available)
        if xdata is not None:
            if isinstance(xdata, numpy.ndarray):
                xarray = xdata
            else:
                try:
                    xarray = numpy.asarray(xdata, dtype=numpy.double)
                except TypeError:
                    raise TypeError("plot xdata argument cannot be converted to numpy array. %s" % str(xdata))
            if xarray.ndim == 0:
                # convert scalar to 1D array with one element
                xarray.setshape([1])
            if xarray.ndim > 2:
                raise ValueError("Cannot plot a %d-dimensional numpy array" % xarray.ndim)

        if yarray.ndim == 2:
            if xarray is not None:
                if xarray.ndim == 2:
                    if xarray.shape[0] != yarray.shape[0] or xarray.shape[1] != yarray.shape[1]:
                        raise ValueError("plot xdata and ydata arguments do not have the same size")
                else:
                    if xarray.shape[0] != yarray.shape[1]:
                        raise ValueError("plot xdata (first dimension) and ydata (second dimension) arguments "
                                         "do not have the same size")
            else:
                xarray = numpy.arange(yarray.shape[1])
        else:
            if xarray is not None and xarray.ndim == 2:
                if xarray.shape[1] != yarray.shape[0]:
                    raise ValueError("plot xdata (second dimension) and ydata (first dimension) arguments "
                                     "do not have the same size")
            elif xarray is None:
                xarray = numpy.arange(yarray.shape[0])

        # create empty attribute/location entry for this data set
        self.dataSetAttributes.extend([dict()])
        self.dataSetLocation.extend([dict()])

        if xarray.ndim == 2 or yarray.ndim == 2:
            self.ShowAnimationToolbar(True)
            if xarray.ndim == 2:
                numDataSets = xarray.shape[0]
            else:
                numDataSets = yarray.shape[0]
            dataSetId = None
            for i in range(numDataSets):
                xdata = xarray[i,:] if xarray.ndim == 2 else xarray
                ydata = yarray[i,:] if yarray.ndim == 2 else yarray
                dataSetId = self.plotWindow.AddDataSet(xdata, ydata, dataSetId=dataSetId)
            self.plotWindow.SetAxisRange(0, *self.plotWindow.GetDataXRange())
            self.plotWindow.SetAxisRange(1, *self.plotWindow.GetDataYRange())
        else:
            dataSetId = self.plotWindow.AddDataSet(xarray, yarray)

        return dataSetId

    def AddDataSetAttribute(self, dataSetId, name, value):
        if dataSetId < 0 or dataSetId >= self.plotWindow.GetNumDataSets():
            raise ValueError("Invalid dataSetId")
        self.dataSetAttributes[dataSetId][name] = value
        self.dataSetPropertyTab.UpdateAttributes()

    def AddDataSetLocation(self, dataSetId, latitude, longitude):
        if dataSetId < 0 or dataSetId >= self.plotWindow.GetNumDataSets():
            raise ValueError("Invalid dataSetId")
        if len(self.dataSetLocation[dataSetId]) != 0:
            raise ValueError("dataset already has a location set")
        self.dataSetLocation[dataSetId]['latitude'] = latitude
        self.dataSetLocation[dataSetId]['longitude'] = longitude
        self.dataSetPropertyTab.UpdateLocation()

    def GetNumDataSets(self):
        return self.plotWindow.GetNumDataSets()

    def GetPlotTitle(self):
        return self.plotWindow.GetPlotTitle()

    def SetPlotTitle(self, title):
        try:
            title = str(title)
        except TypeError:
            raise TypeError("parameter 'title' should be a string")
        self.plotWindow.SetPlotTitle(title)
        self.plotPropertyTab.UpdateControls()

    def GetXAxisRange(self):
        return [self.plotWindow.GetAxisRangeMin(0), self.plotWindow.GetAxisRangeMax(0)]

    def SetXAxisRange(self, range):
        try:
            range = tuple(range)
        except TypeError:
            raise TypeError("X Axis range should be a 2-element sequence of numbers (was: '%s')" % str(range))
        try:
            xmin = float(range[0])
            xmax = float(range[1])
        except ValueError:
            raise TypeError("X Axis range should be a 2-element sequence of numbers (was: '%s')" % str(range))
        if xmin > xmax:
            raise ValueError("X Axis range must not denote an empty interval (was: '%s')" % str(range))
        self.plotWindow.SetAxisRange(0, range[0], range[1])
        self.plotPropertyTab.UpdateControls()

    def GetYAxisRange(self):
        return [self.plotWindow.GetAxisRangeMin(1), self.plotWindow.GetAxisRangeMax(1)]

    def SetYAxisRange(self, range):
        try:
            range = tuple(range)
        except TypeError:
            raise TypeError("Y Axis range should be a 2-element sequence of numbers (was: '%s')" % str(range))
        try:
            ymin = float(range[0])
            ymax = float(range[1])
        except ValueError:
            raise TypeError("Y Axis range should be a 2-element sequence of numbers (was: '%s')" % str(range))
        if ymin > ymax:
            raise ValueError("Y Axis range must not denote an empty interval (was: '%s')" % str(range))
        self.plotWindow.SetAxisRange(1, range[0], range[1])
        self.plotPropertyTab.UpdateControls()

    def GetXLogAxis(self):
        return self.plotWindow.GetLogAxis(0)

    def SetXLogAxis(self, log):
        try:
            log = bool(log)
        except ValueError:
            raise TypeError("X Log Axis parameter should be a boolean (was: '%s')" % str(log))
        self.plotWindow.SetLogAxis(0, log)
        self.plotPropertyTab.UpdateControls()

    def GetYLogAxis(self):
        return self.plotWindow.GetLogAxis(1)

    def SetYLogAxis(self, log):
        try:
            log = bool(log)
        except ValueError:
            raise TypeError("Y Log Axis parameter should be a boolean (was: '%s')" % str(log))
        self.plotWindow.SetLogAxis(1, log)
        self.plotPropertyTab.UpdateControls()

    def GetXAxisBase(self):
        return self.plotWindow.GetAxisBase(0)

    def SetXAxisBase(self, base):
        try:
            base = float(base)
        except ValueError:
            raise TypeError("X Axis base should be a float (was: '%s')" % str(base))
        if base < 1:
            raise ValueError("X Axis base should be equal or greater than 1.0 (was: '%s')" % str(base))
        self.plotWindow.SetAxisBase(0, base)
        self.plotPropertyTab.UpdateControls()

    def GetYAxisBase(self):
        return self.plotWindow.GetAxisBase(1)

    def SetYAxisBase(self, base):
        try:
            base = float(base)
        except ValueError:
            raise TypeError("Y Axis base should be a float (was: '%s')" % str(base))
        if base < 1:
            raise ValueError("Y Axis base should be equal or greater than 1.0 (was: '%s')" % str(base))
        self.plotWindow.SetAxisBase(1, base)
        self.plotPropertyTab.UpdateControls()

    def GetXAxisTitle(self):
        return str(self.plotWindow.GetAxisTitle(0))

    def SetXAxisTitle(self, title):
        try:
            title = str(title)
        except TypeError:
            raise ValueError("X Axis title should be a string")
        self.plotWindow.SetAxisTitle(0, title)
        self.plotPropertyTab.UpdateControls()

    def GetYAxisTitle(self):
        return str(self.plotWindow.GetAxisTitle(1))

    def SetYAxisTitle(self, title):
        try:
            title = str(title)
        except TypeError:
            raise ValueError("Y Axis title should be a string")
        self.plotWindow.SetAxisTitle(1, title)
        self.plotPropertyTab.UpdateControls()

    def GetXNumAxisLabels(self):
        return self.plotWindow.GetNumAxisLabels(0)

    def SetXNumAxisLabels(self, numticks):
        try:
            numticks = int(numticks)
        except ValueError:
            raise TypeError("X Axis number of labels should be an integer (was: '%s')" % str(numticks))
        if numticks < 2:
            raise ValueError("X Axis number of labels should be equal or greater than 2 (was: '%s')" % str(numticks))
        self.plotWindow.SetNumAxisLabels(0, numticks)
        self.plotPropertyTab.UpdateControls()

    def GetYNumAxisLabels(self):
        return self.plotWindow.GetNumAxisLabels(1)

    def SetYNumAxisLabels(self, numticks):
        try:
            numticks = int(numticks)
        except ValueError:
            raise TypeError("Y Axis number of labels should be an integer (was: '%s')" % str(numticks))
        if numticks < 2:
            raise ValueError("Y Axis number of labels should be equal or greater than 2 (was: '%s')" % str(numticks))
        self.plotWindow.SetNumAxisLabels(1, numticks)
        self.plotPropertyTab.UpdateControls()

    def GetDataSetLabel(self, dataSetId):
        return str(self.plotWindow.GetDataSetLabel(dataSetId))

    def SetDataSetLabel(self, dataSetId, label):
        try:
            label = str(label)
        except TypeError:
            raise ValueError("DataSet Plot Label should be a string")
        self.plotWindow.SetDataSetLabel(dataSetId, label)
        self.dataSetPropertyTab.UpdateDataSetList()

    def GetPlotLines(self, dataSetId):
        return self.plotWindow.GetPlotLines(dataSetId)

    def SetPlotLines(self, dataSetId, plotLines):
        try:
            plotLines = bool(plotLines)
        except ValueError:
            raise TypeError("PlotLines parameter should be a boolean (was: '%s')" % str(plotLines))
        self.plotWindow.SetPlotLines(dataSetId, plotLines)

    def GetLineWidth(self, dataSetId):
        return self.plotWindow.GetLineWidth(dataSetId)

    def SetLineWidth(self, dataSetId, lineWidth):
        try:
            lineWidth = float(lineWidth)
        except ValueError:
            raise TypeError("Line Width should be a float (was: '%s')" % str(lineWidth))
        if lineWidth < 0:
            raise ValueError("Line Width should be equal or greater than 0.0 (was: '%s')" % str(lineWidth))
        self.plotWindow.SetLineWidth(dataSetId, lineWidth)

    def GetLineStipplePattern(self, dataSetId):
        return self.plotWindow.GetLineStipplePattern(dataSetId)

    def SetLineStipplePattern(self, dataSetId, lineStipplePattern):
        try:
            lineStipplePattern = int(lineStipplePattern)
        except ValueError:
            raise TypeError("Line Stipple Pattern should be an (hex) integer (was: '%s')" % str(lineStipplePattern))
        if lineStipplePattern <= 0 or lineStipplePattern > 65535:
            raise ValueError("Line Stipple Pattern should be greater than 0 and less than 65536 (was: '%s')" %
                             str(lineStipplePattern))
        self.plotWindow.SetLineStipplePattern(dataSetId, lineStipplePattern)

    def GetPlotPoints(self, dataSetId):
        return self.plotWindow.GetPlotPoints(dataSetId)

    def SetPlotPoints(self, dataSetId, plotPoints):
        try:
            plotPoints = bool(plotPoints)
        except ValueError:
            raise TypeError("PlotPoints parameter should be a boolean (was: '%s')" % str(plotPoints))
        self.plotWindow.SetPlotPoints(dataSetId, plotPoints)

    def GetPointSize(self, dataSetId):
        return self.plotWindow.GetPointSize(dataSetId)

    def SetPointSize(self, dataSetId, pointSize):
        try:
            pointSize = float(pointSize)
        except ValueError:
            raise TypeError("Point Size should be a float (was: '%s')" % str(pointSize))
        if pointSize < 0:
            raise ValueError("Point Size should be equal or greater than 0.0 (was: '%s')" % str(pointSize))
        self.plotWindow.SetPointSize(dataSetId, pointSize)

    def GetPlotColor(self, dataSetId):
        return self.plotWindow.GetPlotColor(dataSetId)

    def SetPlotColor(self, dataSetId, color):
        try:
            color = tuple(color)
        except TypeError:
            raise TypeError("Plot Color should be a 3-element sequence of numbers (was: '%s')" % str(color))
        try:
            r = float(color[0])
            g = float(color[1])
            b = float(color[2])
        except ValueError:
            raise TypeError("Plot Color should be a 3-element sequence of numbers (was: '%s')" % str(color))
        if r < 0 or g < 0 or b < 0 or r > 1 or g > 1 or b > 1:
            raise ValueError("Plot Color must contain numbers between 0.0 and 1.0 (was: '%s')" % str(color))
        self.plotWindow.SetPlotColor(dataSetId, color)

    def GetOpacity(self, dataSetId):
        return self.plotWindow.GetOpacity(dataSetId)

    def SetOpacity(self, dataSetId, opacity):
        try:
            opacity = float(opacity)
        except ValueError:
            raise TypeError("Opacity should be a float (was: '%s')" % str(opacity))
        if opacity < 0 or opacity > 1:
            raise ValueError("Opacity should be between 0.0 and 1.0 (was: '%s')" % str(opacity))
        self.plotWindow.SetOpacity(dataSetId, opacity)

    def GetNumKeyframes(self):
        return self.plotWindow.GetNumKeyframes()

    def GetKeyframe(self):
        return self.plotWindow.GetKeyframe()

    def SetKeyframe(self, keyframe):
        self.animationToolbar.UpdateNumKeyframes()
        self.animationToolbar.SetKeyframe(keyframe)

    def ExportToImageFile(self, filename, imageType):
        self.plotWindow.ExportToImageFile(filename, imageType)

    def OnClose(self, event):
        # Make sure this wxFrame is not closing down
        if self.closingDown:
            return

        # Fix for EVT_KILL_FOCUS crashes
        win = wx.Window.FindFocus()
        if win is not None:
            win.Disconnect(-1, -1, wx.wxEVT_KILL_FOCUS)

        self.closingDown = True
        self.animationToolbar.Destroy()
        self.Destroy()

    def OnKeyDown(self, event):
        # Check if space was pressed
        if (event.GetKeyCode() == 32):
            self.animationToolbar.TogglePlayPause()
        event.Skip()

    def OnPlotAxisChanged(self, event):
        self.plotPropertyTab.UpdateAxes()

    def OnPlotDataChanged(self, event):
        self.dataSetPropertyTab.UpdateDataSetList()
        self.animationToolbar.UpdateNumKeyframes()
        self.viewSliderMenuItem.Enable(self.plotWindow.GetNumKeyframes() > 1)

    def OnKeyframeChanged(self, event):
        # Make sure this wxFrame is not closing down
        if self.closingDown:
            return

        self.plotWindow.SetKeyframe(event.keyframe)
        self.dataSetPropertyTab.UpdateAttributes()
        self.dataSetPropertyTab.UpdateLocation()

    def OnSplitPanelSize(self, event):
        if self.splitPanel.IsSplit():
            self.AdjustSplitPanelSashPosition()
        event.Skip()

    def OnPropertyPanelSize(self, event):
        self.propertyPanel.Layout()
        event.Skip()

    def OnDataSetPropertyTabSize(self, event):
        self.dataSetPropertyTab.Layout()
        event.Skip()

    def OnPlotPropertyTabSize(self, event):
        self.plotPropertyTab.Layout()
        event.Skip()

    def OnViewSlider(self, event):
        self.ShowAnimationToolbar(event.IsChecked())

    def OnViewProps(self, event):
        self.ShowPropertyPanel(event.IsChecked())

    def OnSave(self, event):
        imagetypeinfo = [("TIFF", "tif"), ("Windows Bitmap", "bmp"), ("JPEG", "jpg"), ("PNG", "png"), ("PNM", "pnm")]
        dialog = TypedSaveFileDialog(self, title="Save Image",
                                     initialdir=str(wx.Config.Get().Read('DirectoryLocation/Export')),
                                     typeinfo=imagetypeinfo)
        if dialog.ShowModal() == wx.ID_OK:
            wx.Config.Get().Write('DirectoryLocation/Export', os.path.dirname(dialog.filename))
            self.ExportToImageFile(dialog.filename, dialog.ext)
