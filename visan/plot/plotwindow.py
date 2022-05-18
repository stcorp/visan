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

import numpy
import vtk
from vtk.util.numpy_support import numpy_to_vtk
from .wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
import wx

from .visanplot import vtkInteractorStylePlot, vtkPlotActor, vtkXYPlotData

PlotDataChangedEvent, EVT_PLOTDATA_CHANGED = wx.lib.newevent.NewEvent()
PlotAxisChangedEvent, EVT_PLOTAXIS_CHANGED = wx.lib.newevent.NewEvent()

X_AXIS = 0
Y_AXIS = 1

COLORMAP = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [1.0, 0.0, 1.0],
            [0.0, 1.0, 1.0], [0.7, 0.7, 0.0], [0.0, 0.7, 0.7], [0.7, 0.0, 0.7],
            [0.5, 0.0, 0.0], [0.0, 0.5, 0.0], [0.0, 0.0, 0.5]]


class PlotWindow(wxVTKRenderWindowInteractor):

    def __init__(self, *args, **kwargs):
        super(PlotWindow, self).__init__(*args, **kwargs)
        # TODO: Still needed?
        # self.UseCaptureMouseOn()
        self.keyframe = 0
        self.numKeyframes = 1

        self.dataSets = []
        self.dataSetProperties = []

        self.actor = vtkPlotActor()
        self.actor.GetProperty().SetColor(0.0, 0.0, 0.0)

        def onPlotAxisChanged(caller, event, calldata=None):
            wx.PostEvent(self, PlotAxisChangedEvent())
        self.actor.AddObserver("XRangeChanged", onPlotAxisChanged)
        self.actor.AddObserver("YRangeChanged", onPlotAxisChanged)

        renderer = vtk.vtkRenderer()
        renderer.SetBackground(1.0, 1.0, 1.0)
        renderer.AddActor2D(self.actor)

        self.GetRenderWindow().AddRenderer(renderer)
        self.GetRenderWindow().SetPointSmoothing(True)
        self.GetRenderWindow().SetLineSmoothing(True)

        istyle = vtkInteractorStylePlot()
        self.SetInteractorStyle(istyle)

    def SetPlotTitle(self, title):
        self.actor.SetTitle(title)
        self.Refresh()

    def GetPlotTitle(self):
        return self.actor.GetTitle()

    def AddDataSet(self, xdata, ydata, dataSetId=None):
        xdata = numpy_to_vtk(numpy.asarray(xdata, dtype=numpy.double))
        ydata = numpy_to_vtk(numpy.asarray(ydata, dtype=numpy.double))
        if dataSetId is None:
            plotData = vtkXYPlotData()
            plotData.AddData(xdata, ydata)
            plotProperty = vtk.vtkProperty2D()
            plotProperty.SetColor(COLORMAP[len(self.dataSets) % 11]);
            self.actor.AddData(plotData, plotProperty)
            self.dataSets.append(plotData)
            self.dataSetProperties.append(plotProperty)
            dataSetId = len(self.dataSets) - 1
        else:
            self.dataSets[dataSetId].AddData(xdata, ydata)
            if self.dataSets[dataSetId].GetNumberOfKeyframes() > self.numKeyframes:
                self.numKeyframes = self.dataSets[dataSetId].GetNumberOfKeyframes()
            self.actor.CalculateDataRanges()
        self.Refresh()

        wx.PostEvent(self, PlotDataChangedEvent())

        return dataSetId

    def UpdateDataSet(self, dataSetId, xdata, ydata):
        xdata = numpy_to_vtk(numpy.asarray(xdata, dtype=numpy.double))
        ydata = numpy_to_vtk(numpy.asarray(ydata, dtype=numpy.double))
        self.dataSets[dataSetId].SetData(xdata, ydata)
        # recalculate number of keyframes
        self.numKeyframes = max(dataSet.GetNumberOfKeyframes() for dataSet in self.dataSets)
        self.actor.CalculateDataRanges()
        self.Refresh()

        wx.PostEvent(self, PlotDataChangedEvent())

        return dataSetId

    def GetDataXRange(self):
        return self.actor.GetDataXRange()

    def GetDataYRange(self):
        return self.actor.GetDataYRange()

    def GetNumDataSets(self):
        return len(self.dataSets)

    def GetNumKeyframes(self):
        return self.numKeyframes

    def GetNumKeyframesForDataSet(self, dataSetId):
        return self.dataSets[dataSetId].GetNumberOfKeyframes()

    def SetKeyframe(self, keyframe):
        if keyframe >= self.numKeyframes:
            keyframe = sef.numKeyframes - 1
        if keyframe < 0:
            keyframe = 0
        self.keyframe = keyframe
        for dataSet in self.dataSets:
            dataSet.SetKeyframe(keyframe)
        self.Refresh()

    def GetKeyframe(self):
        return self.keyframe

    def SetAxisRange(self, axisId, minValue, maxValue):
        if axisId == X_AXIS:
            self.actor.SetXRange(minValue, maxValue)
        if axisId == Y_AXIS:
            self.actor.SetYRange(minValue, maxValue)
        self.Refresh()

    def GetAxisRangeMin(self, axisId):
        if axisId == X_AXIS:
            return self.actor.GetXRange()[0]
        if axisId == Y_AXIS:
            return self.actor.GetYRange()[0]

    def GetAxisRangeMax(self, axisId):
        if axisId == X_AXIS:
            return self.actor.GetXRange()[1]
        if axisId == Y_AXIS:
            return self.actor.GetYRange()[1]

    def SetLogAxis(self, axisId, log):
        if axisId == X_AXIS:
            self.actor.SetLogX(log)
        if axisId == Y_AXIS:
            self.actor.SetLogY(log)
        self.Refresh()

    def GetLogAxis(self, axisId):
        if axisId == X_AXIS:
            return self.actor.GetLogX() != 0
        if axisId == Y_AXIS:
            return self.actor.GetLogY() != 0

    def SetAxisBase(self, axisId, base):
        if axisId == X_AXIS:
            self.actor.SetBaseX(base)
        if axisIdd == Y_AXIS:
            self.actor.SetBaseY(base)
        self.Refresh()

    def GetAxisBase(self, axisId):
        if axisId == X_AXIS:
            return self.actor.GetBaseX()
        if axisId == Y_AXIS:
            return self.actor.GetBaseY()

    def SetNumAxisLabels(self, axisId, numLabels):
        if axisId == X_AXIS:
            self.actor.SetNumberOfXLabels(numLabels)
        if axisId == Y_AXIS:
            self.actor.SetNumberOfYLabels(numLabels)
        self.Refresh()

    def GetNumAxisLabels(self, axisId):
        if axisId == X_AXIS:
            return self.actor.GetNumberOfXLabels()
        if axisId == Y_AXIS:
            return self.actor.GetNumberOfYLabels()

    def SetAxisTitle(self, axisId, title):
        if axisId == X_AXIS:
            self.actor.SetXTitle(title)
        if axisId == Y_AXIS:
            self.actor.SetYTitle(title)
        self.Refresh()

    def GetAxisTitle(self, axisId):
        if axisId == X_AXIS:
            return self.actor.GetXTitle()
        if axisId == Y_AXIS:
            return self.actor.GetYTitle()
        return ""

    def SetAxisLabelFormat(self, axisId, format):
        if axisId == X_AXIS:
            self.actor.SetLabelXFormat(format)
        if axisId == Y_AXIS:
            self.actor.SetLabelYFormat(format)
        self.Refresh()

    def GetAxisLabelFormat(self, axisId):
        if axisId == X_AXIS:
            return self.actor.GetLabelXFormat()
        if axisId == Y_AXIS:
            return self.actor.GetLabelYFormat()

    def SetDataSetLabel(self, dataSetId, label):
        self.dataSets[dataSetId].SetPlotLabel(label)
        self.Refresh()

    def GetDataSetLabel(self, dataSetId):
        return self.dataSets[dataSetId].GetPlotLabel()

    def SetPlotLines(self, dataSetId, plotLines):
        self.dataSets[dataSetId].SetPlotLines(plotLines)
        self.Refresh()

    def GetPlotLines(self, dataSetId):
        return self.dataSets[dataSetId].GetPlotLines()

    def SetLineWidth(self, dataSetId, lineWidth):
        self.dataSetProperties[dataSetId].SetLineWidth(lineWidth)
        self.Refresh()

    def GetLineWidth(self, dataSetId):
        return self.dataSetProperties[dataSetId].GetLineWidth()

    def SetLineStipplePattern(self, dataSetId, stipplePattern):
        self.dataSetProperties[dataSetId].SetLineStipplePattern(stipplePattern)
        self.Refresh()

    def GetLineStipplePattern(self, dataSetId):
        return self.dataSetProperties[dataSetId].GetLineStipplePattern()

    def SetPlotPoints(self, dataSetId, plotPoints):
        self.dataSets[dataSetId].SetPlotPoints(plotPoints)
        self.Refresh()

    def GetPlotPoints(self, dataSetId):
        return self.dataSets[dataSetId].GetPlotPoints()

    def SetPointSize(self, dataSetId, pointSize):
        self.dataSets[dataSetId].SetGlyphSize(pointSize / 100.0)

    def GetPointSize(self, dataSetId):
        return self.dataSets[dataSetId].GetGlyphSize() * 100.0

    def SetPlotColor(self, dataSetId, rgb):
        self.dataSetProperties[dataSetId].SetColor(rgb[0], rgb[1], rgb[2])
        self.Refresh()

    def GetPlotColor(self, dataSetId):
        return self.dataSetProperties[dataSetId].GetColor()

    def SetOpacity(self, dataSetId, opacity):
        self.dataSetProperties[dataSetId].SetOpacity(opacity)
        self.Refresh()

    def GetOpacity(self, dataSetId):
        return self.dataSetProperties[dataSetId].GetOpacity()

    def ExportToImageFile(self, filename, format):
        if format == "tif":
            writer = vtk.vtkTIFFWriter()
        elif format == "bmp":
            writer = vtk.vtkBMPWriter()
        elif format == "jpg":
            writer = vtk.vtkJPEGWriter()
        elif format == "png":
            writer = vtk.vtkPNGWriter()
        elif format == "pnm":
            writer = vtk.vtkPNMWriter()
        else:
            raise Exception("Unsupported export format")

        imageFilter = vtk.vtkWindowToImageFilter()
        imageFilter.SetInput(self.GetRenderWindow())
        writer.SetInputConnection(imageFilter.GetOutputPort())
        writer.SetFileName(filename)
        self.GetRenderWindow().Render()
        writer.Write()
