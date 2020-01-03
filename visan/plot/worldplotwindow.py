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
import vtk
from vtk.util.numpy_support import numpy_to_vtk
from vtkmodules.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
import wx

from .visanplotPython import vtkGeoGridSource, vtkGeoMapFilter, vtkInteractorStyleWorldPlot2D, \
    vtkInteractorStyleWorldPlot3D, vtkProjFilter, vtkCoastLineData, vtkColorTable, vtkGeoGridData, \
    vtkWorldPlotGridData, vtkWorldPlotLineData, vtkWorldPlotPointData, vtkWorldPlotSwathData

WorldPlotDataChangedEvent, EVT_WORLDPLOTDATA_CHANGED = wx.lib.newevent.NewEvent()
WorldViewChangedEvent, EVT_WORLDVIEW_CHANGED = wx.lib.newevent.NewEvent()

PROJECTION_LAMBERT_CYLINDRICAL = "Lambert Cylindrical"
PROJECTION_PLATE_CAREE = "Plate Caree"
PROJECTION_MOLLWEIDE = "Mollweide"
PROJECTION_ROBINSON = "Robinson"
PROJECTION_LAMBERT_AZIMUTHAL = "Lambert Azimuthal"
PROJECTION_AZIMUTHAL_EQUIDISTANT = "Azimuthal Equidistant"
PROJECTION_3D = "3D"

PROJECTIONS = [PROJECTION_LAMBERT_CYLINDRICAL, PROJECTION_PLATE_CAREE, PROJECTION_MOLLWEIDE, PROJECTION_ROBINSON,
               PROJECTION_LAMBERT_AZIMUTHAL, PROJECTION_AZIMUTHAL_EQUIDISTANT, PROJECTION_3D]
CYLINDRICAL_PROJECTIONS = [PROJECTION_LAMBERT_CYLINDRICAL, PROJECTION_PLATE_CAREE, PROJECTION_MOLLWEIDE,
                           PROJECTION_ROBINSON]
AZIMUTHAL_PROJECTIONS = [PROJECTION_LAMBERT_AZIMUTHAL, PROJECTION_AZIMUTHAL_EQUIDISTANT]

PROJECTION_IDS = {
    PROJECTION_LAMBERT_CYLINDRICAL: 1,
    PROJECTION_PLATE_CAREE: 2,
    PROJECTION_MOLLWEIDE: 3,
    PROJECTION_ROBINSON: 4,
    PROJECTION_LAMBERT_AZIMUTHAL: 5,
    PROJECTION_AZIMUTHAL_EQUIDISTANT: 6,
    PROJECTION_3D: 7,
}

class WorldPlotWindow(wxVTKRenderWindowInteractor):

    def __init__(self, *args, **kwargs):
        super(WorldPlotWindow, self).__init__(*args, **kwargs)

        self.keyframe = 0
        self.numKeyframes = 1
        self.dataSets = []
        self.projCenterLongitude = 0.0
        self.projCenterLatitude = 0.0

        self.colorBarHeight = 60
        self.dataSetForColorBar = -1

        self.renderer2D = vtk.vtkRenderer()
        self.renderer2D.SetBackground(1, 1, 1)

        self.renderer3D = vtk.vtkRenderer()
        self.renderer3D.SetBackground(0, 0, 0)

        self.style2D = vtkInteractorStyleWorldPlot2D()
        self.style3D = vtkInteractorStyleWorldPlot3D()

        # Globe (only applicable for 3D)
        sphere = vtk.vtkSphereSource()
        sphere.SetRadius(1)
        sphere.SetPhiResolution(30)
        sphere.SetThetaResolution(60)

        mapper3D = vtk.vtkPolyDataMapper()
        actor3D = vtk.vtkActor()

        mapper3D.SetInputConnection(sphere.GetOutputPort())
        actor3D.SetMapper(mapper3D)
        self.renderer3D.AddActor(actor3D)

        def onWorldViewChanged(caller, event, calldata=None):
            wx.PostEvent(self, WorldViewChangedEvent())
        self.style2D.AddObserver("WorldViewChanged", onWorldViewChanged)
        self.style3D.AddObserver("WorldViewChanged", onWorldViewChanged)

        # Grid lines
        self.geoGridData = vtkGeoGridData()
        self.renderer2D.AddActor2D(self.geoGridData.GetActor2D())
        self.renderer3D.AddActor(self.geoGridData.GetActor3D())
        self.style2D.GetTransformCollection().AddItem(self.geoGridData.GetTransform())

        # Coastlines
        self.coastLineData = vtkCoastLineData()
        self.coastLineData.SetMaxLevel(1)
        self.renderer2D.AddActor2D(self.coastLineData.GetActor2D())
        self.renderer3D.AddActor(self.coastLineData.GetActor3D())
        self.style2D.GetTransformCollection().AddItem(self.coastLineData.GetTransform())

        # Plot Title
        self.titleMapper2D = vtk.vtkTextMapper()
        self.titleMapper2D.GetTextProperty().SetFontFamilyToArial()
        self.titleMapper2D.GetTextProperty().SetFontSize(14)
        self.titleMapper2D.GetTextProperty().SetColor(0, 0, 0)
        self.titleMapper2D.GetTextProperty().SetShadow(1)
        self.titleMapper2D.GetTextProperty().SetBold(1)
        self.titleMapper2D.GetTextProperty().SetItalic(1)
        self.titleMapper2D.GetTextProperty().SetJustificationToCentered()
        self.titleActor2D = vtk.vtkActor2D()
        self.titleActor2D.SetMapper(self.titleMapper2D)
        self.titleActor2D.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        self.titleActor2D.SetPosition(0.5, 0.95)
        self.renderer2D.AddActor2D(self.titleActor2D)

        self.titleMapper3D = vtk.vtkTextMapper()
        self.titleMapper3D.GetTextProperty().SetFontFamilyToArial()
        self.titleMapper3D.GetTextProperty().SetFontSize(14)
        self.titleMapper3D.GetTextProperty().SetColor(1, 1, 1)
        self.titleMapper3D.GetTextProperty().SetShadow(1)
        self.titleMapper3D.GetTextProperty().SetBold(1)
        self.titleMapper3D.GetTextProperty().SetItalic(1)
        self.titleMapper3D.GetTextProperty().SetJustificationToCentered()
        titleActor = vtk.vtkActor2D()
        titleActor.SetMapper(self.titleMapper3D)
        titleActor.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        titleActor.SetPosition(0.5, 0.95)
        self.renderer3D.AddActor2D(titleActor)

        # Color Bar
        self.colorBarRenderer = vtk.vtkRenderer()
        self.colorBarActor = vtk.vtkScalarBarActor()
        defaultLut = vtk.vtkLookupTable()
        defaultLut.SetNumberOfTableValues(1)
        defaultLut.SetTableValue(0, 0, 0, 0, 0)
        self.colorBarActor.SetLookupTable(defaultLut)
        self.colorBarActor.SetOrientationToHorizontal()
        self.colorBarActor.SetPosition(0.1, 0.1)
        self.colorBarActor.SetPosition2(0.8, 0.9)
        self.colorBarActor.SetNumberOfLabels(5)
        self.colorBarActor.GetLabelTextProperty().SetColor(1, 1, 1)
        self.colorBarActor.GetLabelTextProperty().ShadowOff()
        self.colorBarActor.GetLabelTextProperty().SetFontFamilyToArial()
        self.colorBarActor.GetLabelTextProperty().ItalicOff()
        self.colorBarActor.GetLabelTextProperty().BoldOff()
        self.colorBarActor.GetLabelTextProperty().SetJustificationToCentered()
        self.colorBarActor.GetTitleTextProperty().SetColor(1, 1, 1)
        self.colorBarActor.GetTitleTextProperty().ShadowOff()
        self.colorBarActor.GetTitleTextProperty().SetFontFamilyToArial()
        self.colorBarActor.GetTitleTextProperty().ItalicOff()
        self.colorBarActor.GetTitleTextProperty().BoldOff()
        self.colorBarActor.SetLabelFormat("%g")
        self.colorBarRenderer.AddActor2D(self.colorBarActor)
        self.colorBarRenderer.InteractiveOff()

        # Make sure the renderer starts with the default zoom/pan position from style3D.
        # We need to do this step before the renderer is attached to the renderwindow otherwise the
        # renderwindow will start to draw itself which breaks the wxVTK binding.
        self.style3D.SetCurrentRenderer(self.renderer3D)
        self.style3D.SetDefaultZoom(2.5)
        self.style3D.SetDefaultView()

        # start with 3D projection
        self.projection = PROJECTION_3D
        self.GetRenderWindow().AddRenderer(self.colorBarRenderer)
        self.GetRenderWindow().AddRenderer(self.renderer2D)
        self.GetRenderWindow().AddRenderer(self.renderer3D)
        self.renderer2D.DrawOff()
        self.SetInteractorStyle(self.style3D)

        # By default the colorbar is hidden
        self.showColorBar = False
        self.UpdateColorBarSize()

    def SetPlotTitle(self, title):
        self.titleMapper2D.SetInput(title)
        self.titleMapper3D.SetInput(title)
        self.Refresh()

    def GetPlotTitle(self):
        return self.titleMapper2D.GetInput()

    def AddWorldPlotData(self, data):
        self.dataSets.append(data)
        self.renderer2D.RemoveActor2D(self.titleActor2D)
        self.renderer2D.AddActor2D(data.GetActor2D())
        self.renderer2D.AddActor2D(self.titleActor2D)
        self.renderer3D.AddActor(data.GetActor3D())
        self.style2D.GetTransformCollection().AddItem(data.GetTransform())
        if len(self.dataSets) == 1:
            self.SetDataSetForColorBar(0)

        def onColorTableChanged(caller, event, calldata=None):
            self.Refresh()
        data.GetColorTable().AddObserver("ColorTableChanged", onColorTableChanged)

        self.SetProjection(self.projection)
        self.SetProjectionCenterLatitude(self.GetProjectionCenterLatitude())
        self.SetProjectionCenterLongitude(self.GetProjectionCenterLongitude())
        if self.projection != PROJECTION_3D:
            self.UpdateStyle2D()

        if data.GetNumberOfKeyframes() > self.numKeyframes:
            self.numKeyframes = data.GetNumberOfKeyframes()
        self.Refresh()

        wx.PostEvent(self, WorldPlotDataChangedEvent())

        return len(self.dataSets) - 1

    def AddPointData(self, latitude, longitude, data=None, dataSetId=None):
        if dataSetId is None:
            pointData = vtkWorldPlotPointData()
        else:
            pointData = self.dataSets[dataSetId]
            if pointData.__class__.__name__ != "vtkWorldPlotPointData":
                raise Exception("pointData can only be added to existing pointData")
        latitude = numpy_to_vtk(numpy.asarray(latitude, dtype=numpy.double))
        longitude = numpy_to_vtk(numpy.asarray(longitude, dtype=numpy.double))
        if data is not None:
            data = numpy_to_vtk(numpy.asarray(data, dtype=numpy.double))
        pointData.AddData(latitude, longitude, data)
        if dataSetId is None:
            return self.AddWorldPlotData(pointData)
        else:
            if pointData.GetNumberOfKeyframes() > self.numKeyframes:
                self.numKeyframes = pointData.GetNumberOfKeyframes()
            self.Refresh()
            wx.PostEvent(self, WorldPlotDataChangedEvent())
        return dataSetId

    def AddLineData(self, latitude, longitude, dataSetId=None):
        if dataSetId is None:
            lineData = vtkWorldPlotLineData()
        else:
            lineData = self.dataSets[dataSetId]
            if lineData.__class__.__name__ != "vtkWorldPlotLineData":
                raise Exception("lineData can only be added to existing lineData")
        latitude = numpy_to_vtk(numpy.asarray(latitude, dtype=numpy.double))
        longitude = numpy_to_vtk(numpy.asarray(longitude, dtype=numpy.double))
        lineData.AddData(latitude, longitude)
        if dataSetId is None:
            return self.AddWorldPlotData(lineData)
        else:
            if lineData.GetNumberOfKeyframes() > self.numKeyframes:
                self.numKeyframes = lineData.GetNumberOfKeyframes()
            self.Refresh()
            wx.PostEvent(self, WorldPlotDataChangedEvent())
        return dataSetId

    def AddSwathData(self, cornerLatitude, cornerLongitude, data=None, dataSetId=None):
        if dataSetId is None:
            swathData = vtkWorldPlotSwathData()
        else:
            swathData = self.dataSets[dataSetId]
            if swathData.__class__.__name__ != "vtkWorldPlotSwathData":
                raise Exception("swathData can only be added to existing swathData")
        cornerLatitude = numpy_to_vtk(numpy.asarray(cornerLatitude, dtype=numpy.double))
        cornerLongitude = numpy_to_vtk(numpy.asarray(cornerLongitude, dtype=numpy.double))
        if data is not None:
            data = numpy_to_vtk(numpy.asarray(data, dtype=numpy.double))
        swathData.AddData(cornerLatitude, cornerLongitude, data)
        if dataSetId is None:
            return self.AddWorldPlotData(swathData)
        else:
            if swathData.GetNumberOfKeyframes() > self.numKeyframes:
                self.numKeyframes = swathData.GetNumberOfKeyframes()
            self.Refresh()
            wx.PostEvent(self, WorldPlotDataChangedEvent())
        return dataSetId

    def AddGridData(self, latitude, longitude, data, dataSetId=None):
        if dataSetId is None:
            gridData = vtkWorldPlotGridData()
        else:
            gridData = self.dataSets[dataSetId]
            if gridData.__class__.__name__ != "vtkWorldPlotGridData":
                raise Exception("gridData can only be added to existing gridData")
        latitude = numpy_to_vtk(numpy.asarray(latitude, dtype=numpy.double))
        longitude = numpy_to_vtk(numpy.asarray(longitude, dtype=numpy.double))
        data = numpy_to_vtk(numpy.ravel(numpy.asarray(data, dtype=numpy.double)))
        gridData.AddData(latitude, longitude, data)
        if dataSetId is None:
            return self.AddWorldPlotData(gridData)
        else:
            if gridData.GetNumberOfKeyframes() > self.numKeyframes:
                self.numKeyframes = gridData.GetNumberOfKeyframes()
            self.Refresh()
            wx.PostEvent(self, WorldPlotDataChangedEvent())
        return dataSetId

    def GetNumKeyframesForDataSet(self, dataSetId):
        return self.dataSets[dataSetId].GetNumberOfKeyframes()

    def GetNumDataSets(self):
        return len(self.dataSets)

    def GetNumKeyframes(self):
        return self.numKeyframes

    def SetKeyframe(self, newKeyframe):
        if newKeyframe < 0:
            newKeyframe = 0
        if newKeyframe >= self.numKeyframes:
            newKeyframe = self.numKeyframes - 1
        if newKeyframe != self.keyframe:
            self.keyframe = newKeyframe
            for dataSet in self.dataSets:
                dataSet.SetKeyframe(self.keyframe)
        self.Refresh()

    def GetKeyframe(self):
        return self.keyframe

    def SetProjection(self, projection):
        if projection != self.projection:
            # prevent multiple renderings of the VTK window
            self.Freeze()

            if self.projection == PROJECTION_3D:
                # switch from 3D to 2D
                viewLat = self.style3D.GetViewCenterLatitude()
                viewLon = self.style3D.GetViewCenterLongitude()
                zoom = self.style3D.GetViewZoom()
                self.renderer3D.DrawOff()
                self.renderer2D.DrawOn()
                self.SetInteractorStyle(self.style2D)
                self.colorBarRenderer.SetBackground(1, 1, 1)
                self.colorBarActor.GetLabelTextProperty().SetColor(0, 0, 0)
                self.colorBarActor.GetTitleTextProperty().SetColor(0, 0, 0)
            elif projection == PROJECTION_3D:
                # switch from 2D to 3D
                x = self.style2D.GetViewMidPointX()
                y = self.style2D.GetViewMidPointY()
                viewLat, viewLon = vtkProjFilter.NormalizedDeprojection2D(PROJECTION_IDS[self.projection],
                                                                          self.projCenterLatitude,
                                                                          self.projCenterLongitude, x, y)
                zoom = self.style2D.GetViewZoom()
                self.renderer2D.DrawOff()
                self.renderer3D.DrawOn()
                self.SetInteractorStyle(self.style3D)
                self.colorBarRenderer.SetBackground(0, 0, 0)
                self.colorBarActor.GetLabelTextProperty().SetColor(1, 1, 1)
                self.colorBarActor.GetTitleTextProperty().SetColor(1, 1, 1)
            else:
                # 2D to 2D
                x = self.style2D.GetViewMidPointX()
                y = self.style2D.GetViewMidPointY()
                viewLat, viewLon = vtkProjFilter.NormalizedDeprojection2D(PROJECTION_IDS[self.projection],
                                                                          self.projCenterLatitude,
                                                                          self.projCenterLongitude, x, y)
                zoom = self.style2D.GetViewZoom()

            self.geoGridData.SetProjection(PROJECTION_IDS[projection])
            self.coastLineData.SetProjection(PROJECTION_IDS[projection])
            for dataSet in self.dataSets:
                dataSet.SetProjection(PROJECTION_IDS[projection])

            self.projection = projection

            # set the view parameters
            if self.projection == PROJECTION_3D:
                self.style3D.SetViewParameters(viewLat, viewLon, 0.0, zoom)
            else:
                x, y = vtkProjFilter.NormalizedProjection2D(PROJECTION_IDS[self.projection], self.projCenterLatitude,
                                                            self.projCenterLongitude, viewLat, viewLon)

                self.UpdateStyle2D()

                self.style2D.SetViewMidPoint(x, y)
                self.style2D.SetViewZoom(zoom)
                if self.projection in CYLINDRICAL_PROJECTIONS:
                    self.style2D.SetDefaultZoom(1.6)
                else:
                    self.style2D.SetDefaultZoom(1.0)

            # allow rendering of the VTK window again
            self.Thaw()
            self.Refresh()

    def GetProjection(self):
        return self.projection

    def SetCoastLineFile(self, filename):
        self.coastLineData.SetFileName(filename)
        self.Refresh()

    def GetCoastLineFile(self):
        return self.coastLineData.GetFileName()

    def GetColorTable(self, dataSetId):
        return self.dataSets[dataSetId].GetColorTable()

    def ShowColorBar(self, show):
        if show != self.showColorBar:
            self.showColorBar = show
            self.UpdateColorBarSize()
            if self.projection != PROJECTION_3D:
                self.UpdateStyle2D()
            self.Refresh()

    def SetDataSetForColorBar(self, dataSetId):
        if dataSetId != self.dataSetForColorBar:
            self.dataSetForColorBar = dataSetId
            self.colorBarActor.SetLookupTable(self.dataSets[dataSetId].GetColorTable().GetVTKLookupTable())
            self.colorBarActor.SetTitle(self.dataSets[dataSetId].GetColorBarTitle())
            self.colorBarActor.SetNumberOfLabels(self.dataSets[dataSetId].GetNumColorBarLabels())
            self.UpdateColorBarSize()
            self.Refresh()

    def GetDataSetForColorBar(self):
        return self.dataSetForColorBar

    def SetProjectionCenterLatitude(self, projCenterLatitude):
        # This is NOT relevant for 3D
        if projCenterLatitude != self.projCenterLatitude:
            viewCenterLatitude = self.GetViewCenterLatitude()
            viewCenterLongitude = self.GetViewCenterLongitude()
            self.projCenterLatitude = projCenterLatitude
            self.geoGridData.SetProjectionCenterLatitude(projCenterLatitude)
            self.coastLineData.SetProjectionCenterLatitude(projCenterLatitude)
            for dataSet in self.dataSets:
                dataSet.SetProjectionCenterLatitude(projCenterLatitude)
            self.SetViewCenter(viewCenterLatitude, viewCenterLongitude)
            self.Refresh()

    def GetProjectionCenterLatitude(self):
        return self.projCenterLatitude

    def SetProjectionCenterLongitude(self, projCenterLongitude):
        # This is NOT relevant for 3D
        if projCenterLongitude != self.projCenterLongitude:
            viewCenterLatitude = self.GetViewCenterLatitude()
            viewCenterLongitude = self.GetViewCenterLongitude()
            self.projCenterLongitude = projCenterLongitude
            self.geoGridData.SetProjectionCenterLongitude(projCenterLongitude)
            self.coastLineData.SetProjectionCenterLongitude(projCenterLongitude)
            for dataSet in self.dataSets:
                dataSet.SetProjectionCenterLongitude(projCenterLongitude)
            self.SetViewCenter(viewCenterLatitude, viewCenterLongitude)
            self.Refresh()

    def GetProjectionCenterLongitude(self):
        return self.projCenterLongitude

    def SetViewCenter(self, viewCenterLatitude, viewCenterLongitude):
        # Pass through to the appropriate interactor style
        if self.projection == PROJECTION_3D:
            self.style3D.SetLatitude(viewCenterLatitude)
            self.style3D.SetLongitude(viewCenterLongitude)
        else:
            # modify the mid-point by mapping the view coordinates
            x, y = vtkProjFilter.NormalizedProjection2D(PROJECTION_IDS[self.projection], self.projCenterLatitude,
                                                        self.projCenterLongitude, viewCenterLatitude,
                                                        viewCenterLongitude)
            self.style2D.SetViewMidPoint(x, y)
            self.Refresh()

    def SetViewZoom(self, zoomScale):
        if self.projection == PROJECTION_3D:
            self.style3D.SetZoom(zoomScale)
        else:
            self.style2D.SetViewZoom(zoomScale)

    def GetViewCenterLatitude(self):
        if self.projection == PROJECTION_3D:
            return self.style3D.GetViewCenterLatitude()
        else:
            x = self.style2D.GetViewMidPointX()
            y = self.style2D.GetViewMidPointY()
            return vtkProjFilter.NormalizedDeprojection2D(PROJECTION_IDS[self.projection], self.projCenterLatitude,
                                                          self.projCenterLongitude, x, y)[0]

    def GetViewCenterLongitude(self):
        if self.projection == PROJECTION_3D:
            return self.style3D.GetViewCenterLongitude()
        else:
            x = self.style2D.GetViewMidPointX()
            y = self.style2D.GetViewMidPointY()
            return vtkProjFilter.NormalizedDeprojection2D(PROJECTION_IDS[self.projection], self.projCenterLatitude,
                                                          self.projCenterLongitude, x, y)[1]

    def GetViewZoom(self):
        if self.projection == PROJECTION_3D:
            return self.style3D.GetViewZoom()
        else:
            return self.style2D.GetViewZoom()

    def SetColorRange(self, dataSetId, minValue, maxValue):
        self.dataSets[dataSetId].GetColorTable().SetColorRange(minValue, maxValue)
        self.Refresh()

    def GetColorRange(self, dataSetId):
        return self.dataSets[dataSetId].GetColorTable().GetColorRange()

    def SetColorBarTitle(self, dataSetId, title):
        self.dataSets[dataSetId].SetColorBarTitle(title)
        if dataSetId == self.dataSetForColorBar:
            self.colorBarActor.SetLookupTable(self.dataSets[dataSetId].GetColorTable().GetVTKLookupTable())
            self.colorBarActor.SetTitle(title)
            self.UpdateColorBarSize()
        self.Refresh()

    def GetColorBarTitle(self, dataSetId):
        return self.dataSets[dataSetId].GetColorBarTitle()

    def SetDataSetLabel(self, dataSetId, label):
        self.dataSets[dataSetId].SetPlotLabel(label)
        self.Refresh()

    def GetDataSetLabel(self, dataSetId):
        return self.dataSets[dataSetId].GetPlotLabel()

    def SetNumColorBarLabels(self, dataSetId, numLabels):
        self.dataSets[dataSetId].SetNumColorBarLabels(numLabels)
        if dataSetId == self.dataSetForColorBar:
            self.colorBarActor.SetNumberOfLabels(numLabels)
        self.Refresh()

    def GetNumColorBarLabels(self, dataSetId):
        return self.dataSets[dataSetId].GetNumColorBarLabels()

    def SetOpacity(self, dataSetId, opacity):
        self.dataSets[dataSetId].SetOpacity(opacity)
        self.Refresh()

    def GetOpacity(self, dataSetId):
        return self.dataSets[dataSetId].GetOpacity()

    def SetLineWidth(self, dataSetId, width):
        self.dataSets[dataSetId].SetLineWidth(width)
        self.Refresh()

    def GetLineWidth(self, dataSetId):
        return self.dataSets[dataSetId].GetLineWidth()

    def SetPointSize(self, dataSetId, size):
        self.dataSets[dataSetId].SetPointSize(size)
        self.Refresh()

    def GetPointSize(self, dataSetId):
        return self.dataSets[dataSetId].GetPointSize()

    def SetReferenceHeight(self, dataSetId, referenceHeight):
        self.dataSets[dataSetId].SetReferenceHeight(referenceHeight)
        self.Refresh()

    def GetReferenceHeight(self, dataSetId):
        return self.dataSets[dataSetId].GetReferenceHeight()

    def SetHeightFactor(self, dataSetId, heightFactor):
        self.dataSets[dataSetId].SetHeightFactor(heightFactor)
        self.Refresh()

    def GetHeightFactor(self, dataSetId):
        return self.dataSets[dataSetId].GetHeightFactor()

    def SetMinHeightValue(self, dataSetId, minValue):
        self.dataSets[dataSetId].SetMinHeightValue(minValue)
        self.Refresh()

    def GetMinHeightValue(self, dataSetId):
        return self.dataSets[dataSetId].GetMinHeightValue()

    def SetMaxHeightValue(self, dataSetId, maxValue):
        self.dataSets[dataSetId].SetMaxHeightValue(maxValue)
        self.Refresh()

    def GetMaxHeightValue(self, dataSetId):
        return self.dataSets[dataSetId].GetMaxHeightValue()

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

    def OnSize(self, event):
        self.UpdateColorBarSize()
        if self.projection != PROJECTION_3D:
            self.UpdateStyle2D()
        event.Skip()

    def UpdateStyle2D(self):
        # Update 2D interactor style with new window size
        w, h = self.GetSize()
        if self.showColorBar:
            h -= self.colorBarHeight
        ratio = self.geoGridData.GetXYRatio()
        self.style2D.SetViewportSizeAndDataXYRatio(w, h, ratio)

    def UpdateColorBarSize(self):
        if self.showColorBar:
            width, height = self.GetSize()
            if height < 1:
                height = 1
            if not self.colorBarActor.GetTitle():
                relativeHeight = float(self.colorBarHeight) * 3.0 / (height * 4.0)
                self.colorBarActor.SetBarRatio(0.65)
            else:
                relativeHeight = float(self.colorBarHeight) / height
                self.colorBarActor.SetBarRatio(0.5)
        else:
            relativeHeight = 0.0
        self.colorBarRenderer.SetViewport(0, 0, 1, relativeHeight)
        self.renderer2D.SetViewport(0, relativeHeight, 1, 1)
        self.renderer3D.SetViewport(0, relativeHeight, 1, 1)
