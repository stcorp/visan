//
// Copyright (C) 2002-2019 S[&]T, The Netherlands.
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//
// 1. Redistributions of source code must retain the above copyright notice,
//    this list of conditions and the following disclaimer.
//
// 2. Redistributions in binary form must reproduce the above copyright
//    notice, this list of conditions and the following disclaimer in the
//    documentation and/or other materials provided with the distribution.
//
// 3. Neither the name of the copyright holder nor the names of its
//    contributors may be used to endorse or promote products derived from
//    this software without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
// AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
// IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
// ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
// LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
// CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
// SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
// INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
// CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
// ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
// POSSIBILITY OF SUCH DAMAGE.
//

#ifndef __vtkPlotActor_h
#define __vtkPlotActor_h

#include "vtkActor2D.h"
#include "vtkLegendBoxActor.h"
#include "vtkPolyData.h"
#include "vtkTextProperty.h"

#include "vtkSmartPointer.h"

class vtkActor2DCollection;
class vtkAppendPolyData;
class vtkNewAxisActor2D;
class vtkDataObjectCollection;
class vtkGlyph2D;
class vtkGlyphSource2D;
class vtkIntArray;
class vtkPlanes;
class vtkPlotDataCollection;
class vtkPlotData;
class vtkPolyDataMapper2D;
class vtkTextMapper;

class VTK_EXPORT vtkPlotActor : public vtkActor2D
{
    public:
        vtkTypeMacro(vtkPlotActor,vtkActor2D);
        void PrintSelf(ostream& os, vtkIndent indent) override;

        static vtkPlotActor *New();

        void AddData(vtkPlotData *plotData, vtkProperty2D *property);
        void RemoveData(vtkPlotData *plotData);

        // Retrieve the plotData that is used as data for a certain plotActor.
        // If the actor is not a plotActor or if the plotData could not be found
        // nulptr will be returned.
        vtkPlotData *GetPlotDataFromActor(vtkActor2D *plotActor);

        // Get the bounds of the plot area (without axis) in viewport coordinates.
        vtkGetVector4Macro(InnerPlotBounds, double);

        vtkSetStringMacro(Title);
        vtkGetStringMacro(Title);
        vtkSetStringMacro(XTitle);
        vtkGetStringMacro(XTitle);
        vtkSetStringMacro(YTitle);
        vtkGetStringMacro(YTitle);

        // Set the plot range (range of independent and dependent variables).
        // Data outside of the range will be clipped.
        // If the plot range of either the x or y variables is set to (v1,v2), where v1 > v2,
        // then the range will be computed automatically (automatic computation is the default behavior).
        virtual void SetXRange(double xmin, double xmax);
        virtual void SetXRange(double range[2])
        {
            this->SetXRange(range[0], range[1]);
        }
        vtkGetVectorMacro(XRange, double, 2);
        virtual void SetYRange(double ymin, double ymax);
        virtual void SetYRange(double range[2])
        {
            this->SetYRange(range[0], range[1]);
        }
        vtkGetVectorMacro(YRange, double, 2);
        void SetPlotRange(double xmin, double ymin, double xmax, double ymax)
        {
            this->SetXRange(xmin, xmax); this->SetYRange(ymin, ymax);
        }

        // Get the data range (x or y values) for the union of all data sets in this plot.
        vtkGetVectorMacro(DataXRange, double, 2);
        vtkGetVectorMacro(DataYRange, double, 2);

        void SetLogX(int logX);
        vtkGetMacro(LogX, int);
        vtkBooleanMacro(LogX, int);

        void SetLogY(int logY);
        vtkGetMacro(LogY, int);
        vtkBooleanMacro(LogY, int);

        // Set the base (> 1.0) for the linear and logarithmic tick calculation for the x-axis.
        vtkSetMacro(BaseX, double);
        vtkGetMacro(BaseX, double);

        // Set the base (> 1.0) for the linear and logarithmic tick calculation for the y-axis.
        vtkSetMacro(BaseY, double);
        vtkGetMacro(BaseY, double);

        // Set the minimal value (> 0) used when using logarithmic axis.
        // All datavalues below this value will be ignored.
        // The default value for MinLogValue is 1 / VTK_DOUBLE_MAX
        void SetMinLogValue(double value);
        vtkGetMacro(MinLogValue, double);

        // Set/Get the number of annotation labels to show along the x and y axes.
        // This values is a suggestion: the number of labels may vary depending on the particulars of the data.
        // The convenience method SetNumberOfLabels() sets the number of x and y labels to the same value.
        vtkSetClampMacro(NumberOfXLabels, int, 0, 50);
        vtkGetMacro(NumberOfXLabels, int);
        vtkSetClampMacro(NumberOfYLabels, int, 0, 50);
        vtkGetMacro(NumberOfYLabels, int);

        vtkSetStringMacro(LabelXFormat);
        vtkGetStringMacro(LabelXFormat);

        vtkSetStringMacro(LabelYFormat);
        vtkGetStringMacro(LabelYFormat);

        virtual void SetTitleTextProperty(vtkTextProperty *p);
        vtkTextProperty *GetTitleTextProperty()
        {
            return TitleTextProperty.GetPointer();
        }

        // Set/Get the title text property of all axes. Note that each axis can
        // be controlled individually through the GetX/YAxisActor2D() methods.
        virtual void SetAxisTitleTextProperty(vtkTextProperty *p);
        vtkTextProperty *GetAxisTitleTextProperty()
        {
            return AxisTitleTextProperty.GetPointer();
        }

        // Set/Get the labels text property of all axes. Note that each axis can
        // be controlled individually through the GetX/YAxisActor2D() methods.
        virtual void SetAxisLabelTextProperty(vtkTextProperty *p);
        vtkTextProperty *GetAxisLabelTextProperty()
        {
            return AxisLabelTextProperty.GetPointer();
        }

        // Auto adjust and zoom the current range such that it becomes a 'nice'
        // range and encapsulates the current range
        void ZoomToOuterXRange();
        void ZoomToOuterYRange();

        // Auto adjust and zoom the current range such that it becomes a 'nice'
        // range and is encapsulated by the current range
        void ZoomToInnerXRange();
        void ZoomToInnerYRange();

        // This zooms in at the data value x (or y) adjusting the current x (or y) range of the plot.
        // The zoomFactor is applied in such a way that a value of 2 would reduce the plot range by half.
        void ZoomInAtXValue(double x, double zoomFactor);
        void ZoomInAtYValue(double y, double zoomFactor);

        // This pans (i.e. shifts) the x (or y) range of the plot.
        // A positive value for the panFactor will shift the plot range to the negative side of the axis.
        // The panFactor is a fractional factor; the amount shifted equals the
        // panFactor times the length of the plot range.
        void PanXRange(double panFactor);
        void PanYRange(double panFactor);

        // Retrieve a handle to the legend box. This is usefull if you would like
        // to change the default behavior of the legend box.
        vtkLegendBoxActor *GetLegendBoxActor()
        {
            return LegendActor.GetPointer();
        }

        vtkSetMacro(Legend, int);
        vtkGetMacro(Legend, int);
        vtkBooleanMacro(Legend, int);

        // Set/Get the symbol that will be used if PlotPoints is off but
        // PlotLines is on for a PlotData input object
        vtkSetObjectMacro(DefaultLegendSymbol, vtkPolyData);
        vtkPolyData *GetDefaultLegendSymbol()
        {
            return DefaultLegendSymbol.GetPointer();
        }

        // Is the specified viewport position within the inner plot area?
        int IsInPlot(double x, double y);

        // Is the specified viewport position within the X axis bounds?
        int IsXAxis(double x, double y);

        // Is the specified viewport position within the Y axis bounds?
        int IsYAxis(double x, double y);

        // Find the closest PlotData near the viewport position (x,y).
        // A pointer to the PlotData will be returned when a PlotData object is
        // found, otherwise 0 will be returned.
        vtkPlotData *FindPlotData(double x, double y);

        // Take into account the modified time of internal helper classes.
        vtkMTimeType GetMTime() override;

        // Draw the x-y plot.
        int RenderOpaqueGeometry(vtkViewport*) override;
        int RenderOverlay(vtkViewport*) override;
        virtual int RenderTranslucentPolygonalGeometry(vtkViewport *) override {return 0;}
        virtual int HasTranslucentPolygonalGeometry() override;
        void ReleaseGraphicsResources(vtkWindow *) override;

        // Force recalculation of data ranges
        void CalculateDataRanges();

    protected:
        vtkPlotActor();
        ~vtkPlotActor() override;

        vtkTimeStamp BuildTime;

        // The data drawn within the axes. Each curve is one polydata. color is controlled by scalar data.
        // The curves are appended together, possibly glyphed with point symbols.
        vtkSmartPointer<vtkPlotDataCollection> PlotData;
        vtkSmartPointer<vtkActor2DCollection> PlotActors;

        // Inner bounds in absolute viewport coordinates
        double InnerPlotBounds[4];
        // Outer bounds in absolute viewport coordinates
        double OuterPlotBounds[4];
        // Viewport size in abosulte coordinates
        int CachedViewportSize[2];

        char *Title;
        vtkSmartPointer<vtkTextMapper> TitleMapper;
        vtkSmartPointer<vtkActor2D> TitleActor;
        vtkSmartPointer<vtkTextProperty> TitleTextProperty;

        char *XTitle;
        char *YTitle;
        double XRange[2];
        double YRange[2];
        double DataXRange[2];
        double DataYRange[2];
        double DataXRangeAbove0[2];
        double DataYRangeAbove0[2];
        int LogX;
        int LogY;
        // the base for the linear and logarithmic tick calculation
        double BaseX;
        double BaseY;
        double MinLogValue;
        // user defined number of labels/ticks
        int NumberOfXLabels;
        int NumberOfYLabels;
        // actual number of labels/ticks
        int ComputedNumberOfXLabels;
        int ComputedNumberOfYLabels;
        char *LabelXFormat;
        char *LabelYFormat;

        vtkSmartPointer<vtkNewAxisActor2D> XAxis;
        vtkSmartPointer<vtkNewAxisActor2D> YAxis;

        vtkSmartPointer<vtkTextProperty> AxisTitleTextProperty;
        vtkSmartPointer<vtkTextProperty> AxisLabelTextProperty;

        // Legends and plot symbols. The legend also keeps track of the symbols and such.
        int Legend;
        // The PositionCoordinate of the legend is set to normalized viewport and
        // uses the PositionCoordinate of the vtkPlotActor as reference.
        // The PositionCoordinate2 of the legend is set to normalized viewport and
        // has the PositionCoordinate of the legend as reference coordinate.
        vtkSmartPointer<vtkLegendBoxActor> LegendActor;
        // This is the symbol that will be used if PlotPoints is off but PlotLines is on for a PlotData input object
        vtkSmartPointer<vtkPolyData> DefaultLegendSymbol;

        void PlaceAxes(vtkViewport *viewport);

    private:
        vtkPlotActor(const vtkPlotActor&) = delete;
        void operator=(const vtkPlotActor&) = delete;
};
#endif
