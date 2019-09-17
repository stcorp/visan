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

#ifndef __vtkPlotData_h
#define __vtkPlotData_h

#include "vtkPolyDataAlgorithm.h"

#include "vtkSmartPointer.h"

class vtkAppendPolyData;
class vtkGlyph3D;
class vtkPoints;

// Undefine any macro called GetYValue (Windows seems to have such a macro)
#ifdef GetYValue
#undef GetYValue
#endif

class vtkPlotData : public vtkPolyDataAlgorithm
{
    public:
        vtkTypeMacro(vtkPlotData, vtkPolyDataAlgorithm);
        virtual void PrintSelf(ostream& os, vtkIndent indent) override;

        virtual double GetXValue(int i) = 0;
        virtual double GetYValue(int i) = 0;
        virtual double GetZValue(int i) = 0;
        virtual int GetNumberOfItems() = 0;

        // Set/Get whether a logarithmic axis is used.
        // When logarithmic axis is turned on and bounds[0]!=bounds[1] then a value will be scaled logarithmic
        // between the data boundaries as follows:
        // x_new = bounds[0] + log(x-bounds[0]+1) * (bounds[1] - bounds[0]) / log(bounds[1]-bounds[0]+1)
        // If bounds[0]==bounds[1], no conversion will be done
        // The logarithmic axis option should only be modified by the vtkPlotActor
        vtkSetMacro(LogX, int);
        vtkGetMacro(LogX, int);
        vtkSetMacro(LogY, int);
        vtkGetMacro(LogY, int);
        vtkSetMacro(LogZ, int);
        vtkGetMacro(LogZ, int);

        // Set the label of the data. This label is used within legends
        vtkSetStringMacro(PlotLabel);
        vtkGetStringMacro(PlotLabel);

        // Set the glyph symbol that is used when plotting points
        // Use output from e.g. vtkGlyphSource2D as input
        void SetPlotSymbol(vtkPolyData *input);
        vtkPolyData *GetPlotSymbol();

        // Set/Get the relative size of the glyph.
        vtkSetMacro(GlyphSize, double);
        vtkGetMacro(GlyphSize, double);

        // Set/Get whether to plot the lines
        vtkSetMacro(PlotLines, int);
        vtkGetMacro(PlotLines, int);
        vtkBooleanMacro(PlotLines, int);

        // Set/Get whether to plot the points (= glyphs)
        vtkSetMacro(PlotPoints, int);
        vtkGetMacro(PlotPoints, int);
        vtkBooleanMacro(PlotPoints, int);

        // This will compute the actual range of the underlying data.
        // If there are no elements the range will be [1,0]
        // If in a derived class a specific dimension is not used the range for that dimension
        // should be set to [0,0] and the GetValue method should return 0.0.
        virtual void GetDataRange(double range[2], int dim);
        void GetDataXRange(double range[2])
        {
            this->GetDataRange(range, 0);
        }
        void GetDataYRange(double range[2])
        {
            this->GetDataRange(range, 1);
        }
        void GetDataZRange(double range[2])
        {
            this->GetDataRange(range, 2);
        }

        // This will compute the range of the underlying data for values > 0.
        // This range will be used for plots with a logarithmic axis.
        // If there are no elements with a value > 0 the range will be [1,0]
        // If in a derived class a specific dimension is not used the range for that dimension
        // should be set to [1,0] (i.e. there are no elements with a value > 0).
        virtual void GetDataRangeAbove0(double range[2], int dim);
        void GetDataXRangeAbove0(double range[2])
        {
            this->GetDataRangeAbove0(range, 0);
        }
        void GetDataYRangeAbove0(double range[2])
        {
            this->GetDataRangeAbove0(range, 1);
        }
        void GetDataZRangeAbove0(double range[2])
        {
            this->GetDataRangeAbove0(range, 2);
        }

        // Set these ranges to clip the data in the X, Y and/or Z dimension.
        // If for a dimension range[0]>range[1] then the range is ignored and
        // no clipping is performed in that dimension.
        // For a 2D plot the z dimension is ignored.
        // The clipping ranges should only be modified by the vtkPlotActor
        vtkSetVector2Macro(ClipXRange, double);
        vtkGetVector2Macro(ClipXRange, double);
        vtkSetVector2Macro(ClipYRange, double);
        vtkGetVector2Macro(ClipYRange, double);
        vtkSetVector2Macro(ClipZRange, double);
        vtkGetVector2Macro(ClipZRange, double);

        // Set/Get the geometry bounding box in viewport coordinats in the form (xmin, xmax, ymin, ymax, zmin, zmax).
        // The datavalues will be linearly mapped from (range[0], range[1]) to (min, max) for each dimension.
        // If for a dimension min>max then for that dimension the data values
        // are used as viewport coordinates and no mapping is performed.
        // For a 2D plot the z dimension is ignored.
        vtkSetVector6Macro(ViewportBounds, double);
        vtkGetVector6Macro(ViewportBounds, double);

        // Calculate the viewport coordinate in one dimension for a datapoint.
        // viewportBounds is one dimension of the area in which the plotdata is drawn
        // (the area between te axes) in viewport coordinates.
        // dataBounds[0] is the data value at viewportBounds[0] and dataBounds[1] the data value at viewportBounds[1].
        // If viewportBounds[0]>viewportBounds[1] the coordinate is left unchanged.
        // If dataBounds[0]==dataBounds[1] the center of the viewportBounds is returned.
        // If logX is true and dataBounds[0]<=0 or dataBounds[1]<=0 then the coordinate is left unchanged.
        static void DataToViewport(double &x, double viewportBounds[2], double dataBounds[2], int logX);

        static void DataToViewport2D(double xy[2], double viewportBounds[4], double dataBounds[4], int logXY[2])
        {
            DataToViewport(xy[0], viewportBounds, dataBounds, logXY[0]);
            DataToViewport(xy[1], &(viewportBounds[2]), &(dataBounds[2]), logXY[1]);
        }

        static void DataToViewport3D(double xyz[3], double viewportBounds[6], double dataBounds[6], int logXYZ[3])
        {
            DataToViewport(xyz[0], viewportBounds, dataBounds, logXYZ[0]);
            DataToViewport(xyz[1], &(viewportBounds[2]), &(dataBounds[2]), logXYZ[1]);
            DataToViewport(xyz[2], &(viewportBounds[4]), &(dataBounds[4]), logXYZ[2]);
        }

        // Calculate one dimension of viewport coordinate to datapoint mapping.
        // ViewportBounds is one dimension of the area in which the plotdata is drawn
        // (the area between te axes) in viewport coordinates.
        // dataBounds[0] is the data value at viewportBounds[0] and dataBounds[1] the data value at viewportBounds[1].
        // If viewportBounds[0]>viewportBounds[1] the datapoint is left unchanged.
        // If viewportBounds[0]==viewportBounds[1] or dataBounds[0]==dataBounds[1]
        // then x will be set to the value of dataBounds[0].
        // If logX is true and dataBounds[0]<=0 or dataBounds[1]<=0 then the datapoint is left unchanged.
        static void ViewportToData(double &x, double viewportBounds[2], double dataBounds[2], int logX);

        static void ViewportToData2D(double xy[2], double viewportBounds[4], double dataBounds[4], int logXY[2])
        {
            ViewportToData(xy[0], viewportBounds, dataBounds, logXY[0]);
            ViewportToData(xy[1], &(viewportBounds[2]), &(dataBounds[2]), logXY[1]);
        }

        static void ViewportToData3D(double xyz[3], double viewportBounds[6], double dataBounds[6], int logXYZ[3])
        {
            ViewportToData(xyz[0], viewportBounds, dataBounds, logXYZ[0]);
            ViewportToData(xyz[1], &(viewportBounds[2]), &(dataBounds[2]), logXYZ[1]);
            ViewportToData(xyz[2], &(viewportBounds[4]), &(dataBounds[4]), logXYZ[2]);
        }

    protected:
        vtkPlotData();
        ~vtkPlotData() override;

        int RequestData(vtkInformation *request, vtkInformationVector **inputVector,
                        vtkInformationVector *outputVector) override;

        void ComputePlotPoints(vtkPoints *pts, double dataBounds[6], int viewportMappingNeeded, int dataClippingNeeded);
        void ComputePlotLines(vtkPoints *pts, double dataBounds[6], int viewportMappingNeeded);
        void ComputePlotLinesWithClipping(vtkPoints *pts, double dataBounds[6], int viewportMappingNeeded);
        double ComputeGlyphScale();

        void GetValidDataRange(double range[2], int dim, int log);

    protected:
        int PlotLines;
        int PlotPoints;

        int LogX;
        int LogY;
        int LogZ;

        double ClipXRange[2];
        double ClipYRange[2];
        double ClipZRange[2];

        double ViewportBounds[6];

        // The data drawn within the axes. A curve is one polydata.
        // color is controlled by scalar data. The curves are appended
        // together, possibly glyphed with point symbols.
        char *PlotLabel;
        double GlyphSize;
        vtkSmartPointer<vtkGlyph3D> PlotGlyph;
        vtkSmartPointer<vtkPolyData> PlotPointsData;
        vtkSmartPointer<vtkPolyData> PlotLinesData;
        vtkSmartPointer<vtkAppendPolyData> PlotAppend;

    private:
        vtkPlotData(const vtkPlotData&) = delete;
        void operator=(const vtkPlotData&) = delete;
};
#endif
