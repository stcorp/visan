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
from .typedsavefiledialog import TypedSaveFileDialog
from .worldplotdatasetpanel import WorldPlotDataSetPanel, EVT_CURRENTDATASET_CHANGED
from .worldplotpropertypanel import WorldPlotPropertyPanel
from .worldplotwindow import WorldPlotWindow, EVT_WORLDPLOTDATA_CHANGED, EVT_WORLDVIEW_CHANGED, PROJECTIONS

windowCount = 1


class WorldPlotFrame(wx.Frame):

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
            title = "VISAN World Plot"
            if windowCount > 1:
                title += " - %d" % windowCount
            windowCount += 1
        wx.Frame.__init__(self, parent, id, title, pos, size)

        # Set a custom icon if possible
        try:
            self.SetIcon(wx.Icon(parent.iconfile, parent.icontype))
        except Exception:
            pass

        # Set initial state
        self.closingDown = False
        self.filename = ""
        self.dataSetAttributes = []

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
        return "<visan worldplot handle>"

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
        self.viewPropertiesMenuItem.Enable(True)
        self.Bind(wx.EVT_MENU, self.OnViewProps, self.viewPropertiesMenuItem)

        viewmenu.AppendSeparator()

        self.viewColorBarMenuItem = viewmenu.AppendCheckItem(wx.ID_ANY, "&Color Bar",
                                                             "Toggle the display of the Color Bar")
        self.Bind(wx.EVT_MENU, self.OnViewColorBar, self.viewColorBarMenuItem)

        self.viewSliderMenuItem = viewmenu.AppendCheckItem(wx.ID_ANY, "&Animation Toolbar",
                                                           "Toggle the display of the Animation Toolbar")
        self.viewSliderMenuItem.Enable(False)
        self.Bind(wx.EVT_MENU, self.OnViewSlider, self.viewSliderMenuItem)

        menubar.Append(viewmenu, "&View")

        self.SetMenuBar(menubar)

    def CreateControls(self):
        # Create a split panel
        splitterstyle = wx.SP_LIVE_UPDATE
        if wx.Platform == "__WXMAC__":
            splitterstyle |= wx.SP_3DSASH
        self.splitPanel = wx.SplitterWindow(self, -1, style=splitterstyle)

        # Create the plot window
        self.plotWindow = WorldPlotWindow(self.splitPanel, -1)
        self.plotWindow.SetCoastLineFile(os.path.join(str(wx.Config.Get().Read('DirectoryLocation/ApplicationData')),
                                                      "gshhs_l.b"))
        self.plotWindow.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.plotWindow.Bind(EVT_WORLDPLOTDATA_CHANGED, self.OnPlotDataChanged)
        self.plotWindow.Bind(EVT_WORLDVIEW_CHANGED, self.OnWorldViewChanged)

        # Create the animation toolbar
        self.animationToolbar = AnimationToolbar(self, self.plotWindow)
        self.animationToolbar.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.animationToolbar.Bind(EVT_KEYFRAME_CHANGED, self.OnKeyframeChanged)

        # Create the property panel
        # Create a parent wxWindow for the notebook to allow for a background colour for the area behind the tabs
        self.propertyPanel = wx.Window(self.splitPanel, -1)
        # Set the background 'explicitly' to have it stick; TODO: still needed?
        self.propertyPanel.SetBackgroundColour(self.propertyPanel.GetBackgroundColour())
        self.propertyPanel.Bind(wx.EVT_SIZE, self.OnPropertyPanelSize)

        # Create the property notebook
        self.propertyNotebook = wx.Notebook(self.propertyPanel, -1)
        # Don't add size handler for propertyNotebook: re-layout of propertyNotebook doesn't work on Windows

        # Create the content for the property notebook
        self.dataSetPropertyTab = WorldPlotDataSetPanel(self.propertyNotebook, self, self.plotWindow)
        self.dataSetPropertyTab.Bind(wx.EVT_SIZE, self.OnDataSetPropertyTabSize)
        self.dataSetPropertyTab.Bind(EVT_CURRENTDATASET_CHANGED, self.OnCurrentDataSetChanged)
        self.plotPropertyTab = WorldPlotPropertyPanel(self.propertyNotebook, self.plotWindow)
        self.plotPropertyTab.Bind(wx.EVT_SIZE, self.OnPlotPropertyTabSize)

        # Add the content to the notebook
        self.propertyNotebook.AddPage(self.dataSetPropertyTab, "Datasets")
        self.propertyNotebook.AddPage(self.plotPropertyTab, "Plot")

        # Initialize split panel
        self.splitPanel.SetMinimumPaneSize(50)
        self.splitPanel.Initialize(self.plotWindow)
        self.splitPanel.Bind(wx.EVT_SIZE, self.OnSplitPanelSize)

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
        if show:
            self.viewSliderMenuItem.Enable()

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

    def ShowColorBar(self, show=True):
        try:
            show = bool(show)
        except ValueError:
            raise TypeError("Show Color Bar parameter should be a boolean (was: '%s')" % str(show))
        self.viewColorBarMenuItem.Check(show)
        self.plotWindow.ShowColorBar(show)

    def SelectDataSet(self, dataSetId):
        if dataSetId < 0 or dataSetId >= self.plotWindow.GetNumDataSets():
            raise ValueError("Invalid dataSetId")
        self.dataSetPropertyTab.SelectDataSet(dataSetId)
        self.plotWindow.SetDataSetForColorBar(dataSetId)
        self.plotPropertyTab.UpdateControls()

    def GetSelectedDataSet(self):
        return self.plotWindow.GetDataSetForColorBar()

    def AddPointData(self, latitude, longitude, data=None):
        # convert data to numpy array if available
        dataArray = None
        if data is not None:
            if isinstance(data, numpy.ndarray):
                dataArray = data
            else:
                try:
                    dataArray = numpy.asarray(data, dtype=numpy.double)
                except TypeError:
                    raise TypeError("plot data argument cannot be converted to numpy array. %s" % str(data))
            if dataArray.ndim == 0:
                # convert scalar to 1D array with one element
                dataArray.setshape([1])
            if dataArray.ndim > 2:
                raise ValueError("Cannot plot a %d-dimensional numpy array" % dataArray.ndim)

        # convert latitude to numpy latitudeArray
        if isinstance(latitude, numpy.ndarray):
            latitudeArray = latitude
        else:
            try:
                latitudeArray = numpy.asarray(latitude, dtype=numpy.double)
            except TypeError:
                raise TypeError("plot latitude argument cannot be converted to numpy array. %s" % str(latitude))
        if latitudeArray.ndim == 0:
            # convert scalar to 1D array with one element
            latitudeArray = numpy.resize(latitudeArray, [1])
        if latitudeArray.ndim > 2:
            raise ValueError("plot latitude argument cannot be a %d-dimensional numpy array" % latitudeArray.ndim)
        if data is not None and len(data) != len(latitudeArray):
            raise ValueError("plot latitude and data arguments do not have the same size")

        # convert longitude to numpy longitudeArray
        if isinstance(longitude, numpy.ndarray):
            longitudeArray = longitude
        else:
            try:
                longitudeArray = numpy.asarray(longitude, dtype=numpy.double)
            except TypeError:
                raise TypeError("plot longitude argument cannot be converted to numpy array. %s" % str(longitude))
        if longitudeArray.ndim == 0:
            # convert scalar to 1D array with one element
            longitudeArray = numpy.resize(longitudeArray, [1])
        if longitudeArray.ndim > 2:
            raise ValueError("plot longitude argument cannot be a %d-dimensional numpy array" % longitudeArray.ndim)
        if len(latitudeArray) != len(longitudeArray):
            raise ValueError("plot latitude and longitude arguments do not have the same size")

        # create empty attribute entry for this data set
        self.dataSetAttributes.extend([dict()])

        dataSetId = self.plotWindow.AddPointData(latitudeArray, longitudeArray, dataArray)

        self.plotPropertyTab.UpdateControls()

        return dataSetId

    def AddLineData(self, latitude, longitude):
        # convert latitude to numpy latitudeArray
        if isinstance(latitude, numpy.ndarray):
            latitudeArray = latitude
        else:
            try:
                latitudeArray = numpy.asarray(latitude, dtype=numpy.double)
            except TypeError:
                raise TypeError("plot latitude argument cannot be converted to numpy array. %s" % str(latitude))
        if latitudeArray.ndim == 0:
            # convert scalar to 1D array with one element
            latitudeArray = numpy.resize(latitudeArray, [1])
        if latitudeArray.ndim > 2:
            raise ValueError("plot latitude argument cannot be a %d-dimensional numpy array" % latitudeArray.ndim)

        # convert longitude to numpy longitudeArray
        if isinstance(longitude, numpy.ndarray):
            longitudeArray = longitude
        else:
            try:
                longitudeArray = numpy.asarray(longitude, dtype=numpy.double)
            except TypeError:
                raise TypeError("plot longitude argument cannot be converted to numpy array. %s" % str(longitude))
        if longitudeArray.ndim == 0:
            # convert scalar to 1D array with one element
            longitudeArray = numpy.resize(longitudeArray, [1])
        if longitudeArray.ndim > 2:
            raise ValueError("plot longitude argument cannot be a %d-dimensional numpy array" % longitudeArray.ndim)
        if len(latitudeArray) != len(longitudeArray):
            raise ValueError("plot latitude and longitude arguments do not have the same size")

        # create empty attribute entry for this data set
        self.dataSetAttributes.extend([dict()])

        dataSetId = self.plotWindow.AddLineData(latitudeArray, longitudeArray)

        self.plotPropertyTab.UpdateControls()

        return dataSetId

    def AddSwathData(self, cornerLatitude, cornerLongitude, data=None):
        # convert data to numpy array if available
        dataArray = None
        if data is not None:
            if isinstance(data, numpy.ndarray):
                dataArray = data
            else:
                try:
                    dataArray = numpy.asarray(data, dtype=numpy.double)
                except TypeError:
                    raise TypeError("plot data argument cannot be converted to numpy array. %s" % str(data))
            if dataArray.ndim == 0:
                # convert scalar to 1D array with one element
                dataArray.setshape([1])
            if dataArray.ndim > 2:
                raise ValueError("plot data argument cannot be a %d-dimensional numpy array" % dataArray.ndim)

        # convert latitude to numpy latitudeArray
        if isinstance(cornerLatitude, numpy.ndarray):
            latitudeArray = cornerLatitude
        else:
            try:
                latitudeArray = numpy.asarray(cornerLatitude, dtype=numpy.double)
            except TypeError:
                raise TypeError("plot latitude argument cannot be converted to numpy array. %s" % str(cornerLatitude))
        if latitudeArray.ndim == 1:
            # convert single swath to swath array
            latitudeArray = numpy.resize(latitudeArray, [1, len(latitudeArray)])
        if latitudeArray.ndim != 2:
            raise ValueError("plot cornerLatitude argument cannot be a %d-dimensional numpy array" % latitudeArray.ndim)
        if latitudeArray.shape[1] != 2 and latitudeArray.shape[1] != 4:
            raise ValueError("last dimension of plot cornerLatitude argument should be 2 or 4 but not %d" %
                             latitudeArray.shape[1])
        if data is not None and len(data) != len(latitudeArray):
            raise ValueError("plot cornerLatitude and data arguments do not have the same number of elements")

        # convert longitude to numpy longitudeArray
        if isinstance(cornerLongitude, numpy.ndarray):
            longitudeArray = cornerLongitude
        else:
            try:
                longitudeArray = numpy.asarray(cornerLongitude, dtype=numpy.double)
            except TypeError:
                raise TypeError("plot longitude argument cannot be converted to numpy array. %s" % str(cornerLongitude))
        if longitudeArray.ndim == 1:
            # convert single swath to swath array
            longitudeArray = numpy.resize(longitudeArray, [1, len(longitudeArray)])
        if longitudeArray.ndim != 2:
            raise ValueError("plot cornerLongitude argument cannot be a %d-dimensional numpy array" %
                             longitudeArray.ndim)
        if longitudeArray.shape[1] != 2 and longitudeArray.shape[1] != 4:
            raise ValueError("last dimension of plot cornerLongitude argument should be 2 or 4 but not %d" %
                             longitudeArray.shape[1])
        if latitudeArray.shape != longitudeArray.shape:
            raise ValueError("plot cornerLatitude and cornerLongitude arguments do not have the same shape")

        if latitudeArray.shape[1] == 2:
            # convert bounding rect coordinates to bounding polygons
            newLat = numpy.zeros(shape=(latitudeArray.shape[0], 4))
            newLon = numpy.zeros(shape=newLat.shape)
            newLat[:, 0] = latitudeArray[:, 0]
            newLon[:, 0] = longitudeArray[:, 0]
            newLat[:, 1] = latitudeArray[:, 0]
            newLon[:, 1] = longitudeArray[:, 1]
            newLat[:, 2] = latitudeArray[:, 1]
            newLon[:, 2] = longitudeArray[:, 1]
            newLat[:, 3] = latitudeArray[:, 1]
            newLon[:, 3] = longitudeArray[:, 0]
            latitudeArray = newLat
            longitudeArray = newLon

        # create empty attribute entry for this data set
        self.dataSetAttributes.extend([dict()])

        dataSetId = self.plotWindow.AddSwathData(latitudeArray, longitudeArray, dataArray)

        if data is not None:
            self.ShowColorBar()

        self.plotPropertyTab.UpdateControls()

        return dataSetId

    # data should have size: [numGrids, numLatitudes, numLongitudes] or [numLatitudes, numLongitudes]
    def AddGridData(self, latitudeGrid, longitudeGrid, data):
        # convert data to numpy array
        if isinstance(data, numpy.ndarray):
            dataArray = data
        else:
            try:
                dataArray = numpy.asarray(data, dtype=numpy.double)
            except TypeError:
                raise TypeError("plot data argument cannot be converted to numpy array. %s" % str(data))
        if dataArray.ndim == 2:
            # convert single grid to array with one grid element
            dataArray = numpy.resize(dataArray, [1, dataArray.shape[0], dataArray.shape[1]])
        if dataArray.ndim != 3:
            raise ValueError("plot data argument cannot be a %d-dimensional numpy array" % dataArray.ndim)

        # convert latitudeGrid to numpy latitudeArray
        if isinstance(latitudeGrid, numpy.ndarray):
            latitudeArray = latitudeGrid
        else:
            try:
                latitudeArray = numpy.asarray(latitudeGrid, dtype=numpy.double)
            except TypeError:
                raise TypeError("plot latitudeGrid argument cannot be converted to numpy array. %s" % str(latitudeGrid))
        if latitudeArray.ndim != 1:
            if latitudeArray.ndim == 2:
                if latitudeArray.shape[0] != dataArray.shape[0]:
                    raise ValueError("plot latitudeGrid time dimension does not match time dimension of grid data")
                if not numpy.all(latitudeArray[:] == latitudeArray[0]):
                    raise ValueError("plot latitudeGrid should be the same for all grids")
                latitudeArray = latitudeArray[0]
            else:
                raise ValueError("plot latitudeGrid argument should be a one dimensional array")
        if latitudeArray.shape[0] != dataArray.shape[1]:
            raise ValueError("plot latitudeGrid size does not match latitude dimension of grid data")

        # convert longitudeGrid to numpy longitudeArray
        if isinstance(longitudeGrid, numpy.ndarray):
            longitudeArray = longitudeGrid
        else:
            try:
                longitudeArray = numpy.asarray(longitudeGrid, dtype=numpy.double)
            except TypeError:
                raise TypeError("plot longitudeGrid argument cannot be converted to numpy array. %s" %
                                str(longitudeGrid))
        if longitudeArray.ndim != 1:
            if longitudeArray.ndim == 2:
                if longitudeArray.shape[0] != dataArray.shape[0]:
                    raise ValueError("plot longitudeGrid time dimension does not match time dimension of grid data")
                if not numpy.all(longitudeArray[:] == longitudeArray[0]):
                    raise ValueError("plot longitudeGrid should be the same for all grids")
                longitudeArray = longitudeArray[0]
            else:
                raise ValueError("plot longitudeGrid argument should be a one dimensional array")
        if longitudeArray.shape[0] != dataArray.shape[2]:
            raise ValueError("plot longitudeGrid size does not match longitude dimension of grid data")

        # create empty attribute entry for this data set
        self.dataSetAttributes.extend([dict()])

        dataSetId = self.plotWindow.AddGridData(latitudeArray, longitudeArray, dataArray[0])
        if dataArray.shape[0] > 1:
            for i in range(1, dataArray.shape[0]):
                self.plotWindow.AddGridData(latitudeArray, longitudeArray, dataArray[i], dataSetId=dataSetId)
            self.ShowAnimationToolbar()

        self.ShowColorBar()
        self.plotPropertyTab.UpdateControls()

        return dataSetId

    def AddDataSetAttribute(self, dataSetId, name, value):
        if dataSetId < 0 or dataSetId >= self.plotWindow.GetNumDataSets():
            raise ValueError("Invalid dataSetId")
        self.dataSetAttributes[dataSetId][name] = value
        self.dataSetPropertyTab.UpdateAttributes()

    def GetNumDataSets(self):
        return self.plotWindow.GetNumDataSets()

    def GetPlotTitle(self):
        return self.plotWindow.GetPlotTitle()

    def SetPlotTitle(self, title):
        self.plotWindow.SetPlotTitle(str(title))
        self.plotPropertyTab.UpdateControls()

    def GetProjection(self):
        return self.plotWindow.GetProjection()

    def SetProjection(self, projection):
        if projection not in PROJECTIONS:
            raise ValueError("projection '%s' not supported (possible values are %s)" %
                             (projection, str(PROJECTIONS)))
        self.plotWindow.SetProjection(projection)
        self.plotPropertyTab.UpdateControls()

    def GetProjectionCenterLatitude(self):
        return self.plotWindow.GetProjectionCenterLatitude()

    def SetProjectionCenterLatitude(self, centerLatitude):
        try:
            centerLatitude = float(centerLatitude)
        except ValueError:
            raise TypeError("projCenterLatitude property should be a float (was: '%s')" % str(centerLatitude))

        if (centerLatitude < -90) or (centerLatitude > 90):
            raise ValueError("projCenterLatitude property should be between -90 and 90 (was: '%s')" %
                             str(centerLatitude))

        self.plotWindow.SetProjectionCenterLatitude(centerLatitude)
        self.plotPropertyTab.UpdateControls()

    def GetProjectionCenterLongitude(self):
        return self.plotWindow.GetProjectionCenterLongitude()

    def SetProjectionCenterLongitude(self, centerLongitude):
        try:
            centerLongitude = float(centerLongitude)
        except ValueError:
            raise TypeError("projCenterLongitude property should be a float (was: '%s')" % str(centerLongitude))

        # normalize to [-180,180]
        while centerLongitude < -180:
            centerLongitude += 360
        while centerLongitude > 180:
            centerLongitude -= 360

        self.plotWindow.SetProjectionCenterLongitude(centerLongitude)
        self.plotPropertyTab.UpdateControls()

    def GetViewCenterLatitude(self):
        return self.plotWindow.GetViewCenterLatitude()

    def SetViewCenterLatitude(self, centerLatitude):
        try:
            centerLatitude = float(centerLatitude)
        except ValueError:
            raise TypeError("viewCenterLatitude property should be a float (was: '%s')" % str(centerLatitude))

        if (centerLatitude < -90) or (centerLatitude > 90):
            raise ValueError("viewCenterLatitude property should be between -90 and 90 (was: '%s')" %
                             str(centerLatitude))

        centerLongitude = self.plotWindow.GetViewCenterLongitude()
        self.plotWindow.SetViewCenter(centerLatitude, centerLongitude)
        self.plotPropertyTab.UpdateControls()

    def GetViewCenterLongitude(self):
        return self.plotWindow.GetViewCenterLongitude()

    def SetViewCenterLongitude(self, centerLongitude):
        try:
            centerLongitude = float(centerLongitude)
        except ValueError:
            raise TypeError("viewCenterLongitude property should be a float (was: '%s')" % str(centerLongitude))

        # normalize to [-180,180]
        while centerLongitude < -180:
            centerLongitude += 360
        while centerLongitude > 180:
            centerLongitude -= 360

        centerLatitude = self.plotWindow.GetViewCenterLatitude()
        self.plotWindow.SetViewCenter(centerLatitude, centerLongitude)
        self.plotPropertyTab.UpdateControls()

    def SetViewCenter(self, centerLatitude, centerLongitude):
        try:
            centerLatitude = float(centerLatitude)
        except ValueError:
            raise TypeError("viewCenterLatitude property should be a float (was: '%s')" % str(centerLatitude))

        if (centerLatitude < -90) or (centerLatitude > 90):
            raise ValueError("viewCenterLatitude property should be between -90 and 90 (was: '%s')" %
                             str(centerLatitude))

        try:
            centerLongitude = float(centerLongitude)
        except ValueError:
            raise TypeError("viewCenterLongitude property should be a float (was: '%s')" % str(centerLongitude))

        # normalize to [-180,180]
        while centerLongitude < -180:
            centerLongitude += 360
        while centerLongitude > 180:
            centerLongitude -= 360

        self.plotWindow.SetViewCenter(centerLatitude, centerLongitude)
        self.plotPropertyTab.UpdateControls()

    def GetViewZoom(self):
        return self.plotWindow.GetViewZoom()

    def SetViewZoom(self, zoomScale):
        try:
            zoomScale = float(zoomScale)
        except ValueError:
            raise TypeError("zoomScale property should be a float (was: '%s')" % str(zoomScale))

        # clamp to [+1.0,-->)
        if zoomScale < 1.0:
            zoomScale = 1.0

        self.plotWindow.SetViewZoom(zoomScale)
        self.plotPropertyTab.UpdateControls()

    def GetDataSetLabel(self, dataSetId):
        return self.plotWindow.GetDataSetLabel(dataSetId)

    def SetDataSetLabel(self, dataSetId, label):
        if dataSetId < 0 or dataSetId >= self.plotWindow.GetNumDataSets():
            raise ValueError("Invalid dataSetId")
        self.plotWindow.SetDataSetLabel(dataSetId, str(label))
        self.dataSetPropertyTab.UpdateDataSetList()

    def GetOpacity(self, dataSetId):
        if dataSetId < 0 or dataSetId >= self.plotWindow.GetNumDataSets():
            raise ValueError("Invalid dataSetId")
        return self.plotWindow.GetOpacity(dataSetId)

    def SetOpacity(self, dataSetId, opacity):
        if dataSetId < 0 or dataSetId >= self.plotWindow.GetNumDataSets():
            raise ValueError("Invalid dataSetId")
        try:
            opacity = float(opacity)
        except ValueError:
            raise TypeError("opacity property should be a float (was: '%s')" % str(opacity))

        if (opacity < 0) or (opacity > 1):
            raise ValueError("opacity property should be between 0.0 and 1.0 (was: '%s')" % str(opacity))

        self.plotWindow.SetOpacity(dataSetId, opacity)

    def GetLineWidth(self, dataSetId):
        if dataSetId < 0 or dataSetId >= self.plotWindow.GetNumDataSets():
            raise ValueError("Invalid dataSetId")
        return self.plotWindow.GetLineWidth(dataSetId)

    def SetLineWidth(self, dataSetId, linewidth):
        if dataSetId < 0 or dataSetId >= self.plotWindow.GetNumDataSets():
            raise ValueError("Invalid dataSetId")
        try:
            linewidth = float(linewidth)
        except ValueError:
            raise TypeError("linewidth property should be a float (was: '%s')" % str(linewidth))

        if (linewidth < 0):
            raise ValueError("linewidth property should be greater than 0 (was: '%s')" % str(linewidth))

        self.plotWindow.SetLineWidth(dataSetId, linewidth)

    def GetPointSize(self, dataSetId):
        if dataSetId < 0 or dataSetId >= self.plotWindow.GetNumDataSets():
            raise ValueError("Invalid dataSetId")
        return self.plotWindow.GetPointSize(dataSetId)

    def SetPointSize(self, dataSetId, pointsize):
        if dataSetId < 0 or dataSetId >= self.plotWindow.GetNumDataSets():
            raise ValueError("Invalid dataSetId")
        try:
            pointsize = float(pointsize)
        except ValueError:
            raise TypeError("pointsize property should be a float (was: '%s')" % str(pointsize))

        if (pointsize < 0):
            raise ValueError("pointsize property should be equal or greater than 0.0 (was: '%s')" % str(pointsize))

        self.plotWindow.SetPointSize(dataSetId, pointsize)

    def GetReferenceHeight(self, dataSetId):
        if dataSetId < 0 or dataSetId >= self.plotWindow.GetNumDataSets():
            raise ValueError("Invalid dataSetId")
        return self.plotWindow.GetReferenceHeight(dataSetId)

    def SetReferenceHeight(self, dataSetId, referenceHeight):
        if dataSetId < 0 or dataSetId >= self.plotWindow.GetNumDataSets():
            raise ValueError("Invalid dataSetId")
        try:
            referenceHeight = float(referenceHeight)
        except ValueError:
            raise TypeError("referenceHeight property should be a float (was: '%s')" % str(referenceHeight))

        if (referenceHeight <= 0):
            raise ValueError("referenceHeight property should be greater than 0.0 (was: '%s')" % str(referenceHeight))

        self.plotWindow.SetReferenceHeight(dataSetId, referenceHeight)

    def GetHeightFactor(self, dataSetId):
        if dataSetId < 0 or dataSetId >= self.plotWindow.GetNumDataSets():
            raise ValueError("Invalid dataSetId")
        return self.plotWindow.GetHeightFactor(dataSetId)

    def SetHeightFactor(self, dataSetId, heightFactor):
        if dataSetId < 0 or dataSetId >= self.plotWindow.GetNumDataSets():
            raise ValueError("Invalid dataSetId")
        try:
            heightFactor = float(heightFactor)
        except ValueError:
            raise TypeError("heightFactor property should be a float (was: '%s')" % str(heightFactor))

        if (heightFactor < 0):
            raise ValueError("heightFactor property should be equal or greater than 0.0 (was: '%s')" %
                             str(heightFactor))

        self.plotWindow.SetHeightFactor(dataSetId, heightFactor)

    def GetMinHeightValue(self, dataSetId):
        if dataSetId < 0 or dataSetId >= self.plotWindow.GetNumDataSets():
            raise ValueError("Invalid dataSetId")
        return self.plotWindow.GetMinHeightValue(dataSetId)

    def SetMinHeightValue(self, dataSetId, minHeightValue):
        if dataSetId < 0 or dataSetId >= self.plotWindow.GetNumDataSets():
            raise ValueError("Invalid dataSetId")
        try:
            minHeightValue = float(minHeightValue)
        except ValueError:
            raise TypeError("minHeightValue property should be a float (was: '%s')" % str(minHeightValue))

        self.plotWindow.SetMinHeightValue(dataSetId, minHeightValue)

    def GetMaxHeightValue(self, dataSetId):
        if dataSetId < 0 or dataSetId >= self.plotWindow.GetNumDataSets():
            raise ValueError("Invalid dataSetId")
        return self.plotWindow.GetMaxHeightValue(dataSetId)

    def SetMaxHeightValue(self, dataSetId, maxHeightValue):
        if dataSetId < 0 or dataSetId >= self.plotWindow.GetNumDataSets():
            raise ValueError("Invalid dataSetId")
        try:
            maxHeightValue = float(maxHeightValue)
        except ValueError:
            raise TypeError("maxHeightValue property should be a float (was: '%s')" % str(maxHeightValue))

        self.plotWindow.SetMaxHeightValue(dataSetId, maxHeightValue)

    def GetColorRange(self, dataSetId):
        if dataSetId < 0 or dataSetId >= self.plotWindow.GetNumDataSets():
            raise ValueError("Invalid dataSetId")
        return self.plotWindow.GetColorRange(dataSetId)

    def SetColorRange(self, dataSetId, colorrange):
        if dataSetId < 0 or dataSetId >= self.plotWindow.GetNumDataSets():
            raise ValueError("Invalid dataSetId")
        try:
            if len(colorrange) != 2:
                raise TypeError("colorrange property should be a list of two elements")
            range = [float(colorrange[0]), float(colorrange[1])]
        except ValueError:
            raise TypeError("colorrange property should be a float array (was: '%s')" % str(colorrange))

        self.plotWindow.SetColorRange(dataSetId, range[0], range[1])
        self.dataSetPropertyTab.UpdateColorBar()

    def GetColorBarTitle(self, dataSetId):
        return str(self.plotWindow.GetColorBarTitle(dataSetId))

    def SetColorBarTitle(self, dataSetId, title):
        self.plotWindow.SetColorBarTitle(dataSetId, str(title))
        self.dataSetPropertyTab.UpdateColorBar()

    def GetNumColorBarLabels(self, dataSetId):
        return self.plotWindow.GetNumColorBarLabels(dataSetId)

    def SetNumColorBarLabels(self, dataSetId, numLabels):
        try:
            numLabels = int(numLabels)
        except ValueError:
            raise TypeError("numLabels property should be an integer (was: '%s')" % str(numLabels))

        if (numLabels < 2):
            raise ValueError("numLabels property should be equal or greater than 2 (was: '%s')" % str(numLabels))
        self.plotWindow.SetNumColorBarLabels(dataSetId, numLabels)
        self.dataSetPropertyTab.UpdateColorBar()

    def GetColorTable(self, dataSetId):
        if dataSetId < 0 or dataSetId >= self.plotWindow.GetNumDataSets():
            raise ValueError("Invalid dataSetId")
        return self.plotWindow.GetColorTable(dataSetId)

    def GetNumKeyframes(self):
        return self.plotWindow.GetNumKeyframes()

    def GetKeyframe(self):
        return self.plotWindow.GetKeyframe()

    def SetKeyframe(self, keyframe):
        self.animationToolbar.UpdateNumKeyframes()
        self.animationToolbar.SetKeyframe(keyframe)

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
        if (event.GetKeyCode() == 32):  # ' '
            self.animationToolbar.TogglePlayPause()
        elif (event.GetKeyCode() == 114):  # 'r'
            self.plotWindow.Reset()
        event.Skip()

    def OnPlotDataChanged(self, event):
        self.dataSetPropertyTab.UpdateDataSetList()
        self.animationToolbar.UpdateNumKeyframes()
        self.viewSliderMenuItem.Enable(self.plotWindow.GetNumKeyframes() > 1)

    def OnWorldViewChanged(self, event):
        self.plotPropertyTab.UpdateControls()

    def OnKeyframeChanged(self, event):
        # Make sure this wxFrame is not closing down
        if self.closingDown:
            return

        self.plotWindow.SetKeyframe(event.keyframe)
        self.dataSetPropertyTab.UpdateAttributes()

    def OnCurrentDataSetChanged(self, event):
        # Make sure this wxFrame is not closing down
        if self.closingDown:
            return
        self.plotWindow.SetDataSetForColorBar(event.dataSetId)
        self.plotPropertyTab.UpdateControls()

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

    def OnViewColorBar(self, event):
        self.ShowColorBar(event.IsChecked())

    def OnSave(self, event):
        imagetypeinfo = [("TIFF", "tif"), ("Windows Bitmap", "bmp"), ("JPEG", "jpg"), ("PNG", "png"), ("PNM", "pnm")]
        dialog = TypedSaveFileDialog(self, title="Save Image",
                                     initialdir=str(wx.Config.Get().Read('DirectoryLocation/Export')),
                                     typeinfo=imagetypeinfo)
        if dialog.ShowModal() == wx.ID_OK:
            wx.Config.Get().Write('DirectoryLocation/Export', os.path.dirname(dialog.filename))
            self.plotWindow.ExportToImageFile(dialog.filename, dialog.ext)
