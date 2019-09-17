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

#include "vtkPlotData.h"

#include "vtkAppendPolyData.h"
#include "vtkCell.h"
#include "vtkCellArray.h"
#include "vtkGlyph2D.h"
#include "vtkGlyphSource2D.h"
#include "vtkMath.h"
#include "vtkPoints.h"
#include "vtkPolyData.h"

#define VTK_LEFT -1
#define VTK_MIDDLE 0
#define VTK_RIGHT 1

// Determine whether the value is NaN/+Inf/-Inf
static int isInvalid(const double x, const int log)
{
    if (!vtkMath::IsFinite(x))
    {
        return 1;
    }
    if (log && x <= 0)
    {
        return 1;
    }
    return 0;
}

// Computes the instersection of the line starting in p1 and ending in p2 with the bounding box defined by bounds
// (= [xmin,xmax,ymin,ymax,zmin,zmax])
// If the line intersects with the bounding box the function returns a non-zero
// value and the intersection point is stored in 'intersectionPoint'.
static int ComputeIntersection(double bounds[6], double p1[3], double p2[3], double intersectionPoint[3])
{
    double direction[3];
    double t;
    double maxT[3];
    double candidatePlane[3];
    int quadrant[3];
    int thePlane = 0;
    int inside = 1;
    int i;

    direction[0] = p2[0] - p1[0];
    direction[1] = p2[1] - p1[1];
    direction[2] = p2[2] - p1[2];

    // Find closest planes
    for (i = 0; i < 3; i++)
    {
        if (p1[i] < bounds[2 * i])
        {
            quadrant[i] = VTK_LEFT;
            candidatePlane[i] = bounds[2 * i];
            inside = 0;
        }
        else if (p1[i] > bounds[2 * i + 1])
        {
            quadrant[i] = VTK_RIGHT;
            candidatePlane[i] = bounds[2 * i + 1];
            inside = 0;
        }
        else
        {
            quadrant[i] = VTK_MIDDLE;
        }
    }

    // Check whether origin of ray is inside bbox
    if (inside)
    {
        intersectionPoint[0] = p1[0];
        intersectionPoint[1] = p1[1];
        intersectionPoint[2] = p1[2];
        t = 0;
        return 1;
    }

    // Calculate parametric distances to plane
    for (i = 0; i < 3; i++)
    {
        if (quadrant[i] != VTK_MIDDLE && direction[i] != 0.0)
        {
            maxT[i] = (candidatePlane[i] - p1[i]) / direction[i];
        }
        else
        {
            maxT[i] = -1.0;
        }
    }

    // Find the largest parametric value of intersection
    for (i = 0; i < 3; i++)
    {
        if (maxT[thePlane] < maxT[i])
        {
            thePlane = i;
        }
    }

    // Check for valid intersection along line
    if (maxT[thePlane] > 1.0 || maxT[thePlane] < 0.0)
    {
        return 0;
    }
    else
    {
        t = maxT[thePlane];
    }

    // Intersection point along line is okay.  Check bounding box.
    for (i = 0; i < 3; i++)
    {
        if (thePlane != i)
        {
            intersectionPoint[i] = p1[i] + maxT[thePlane] * direction[i];
            if (intersectionPoint[i] < bounds[2 * i] ||
                intersectionPoint[i] > bounds[2 * i + 1])
            {
                return 0;
            }
        }
        else
        {
            intersectionPoint[i] = candidatePlane[i];
        }
    }

    return 1;
}

vtkPlotData::vtkPlotData()
{
    this->PlotLines = 1;
    this->PlotPoints = 0;

    this->LogX = 0;
    this->LogY = 0;
    this->LogZ = 0;

    this->ClipXRange[0] = 1;
    this->ClipXRange[1] = 0;
    this->ClipYRange[0] = 1;
    this->ClipYRange[1] = 0;
    this->ClipZRange[0] = 1;
    this->ClipZRange[1] = 0;

    this->PlotLabel = nullptr;

    this->ViewportBounds[0] = 1.0;
    this->ViewportBounds[1] = 0.0;
    this->ViewportBounds[2] = 1.0;
    this->ViewportBounds[3] = 0.0;
    this->ViewportBounds[4] = 1.0;
    this->ViewportBounds[5] = 0.0;

    this->PlotPointsData = vtkSmartPointer<vtkPolyData>::New();
    this->PlotLinesData = vtkSmartPointer<vtkPolyData>::New();

    this->GlyphSize = 0.01;

    auto glyphSource = vtkSmartPointer<vtkGlyphSource2D>::New();
    glyphSource->SetGlyphTypeToCircle();
    glyphSource->FilledOff();

    this->PlotGlyph = vtkSmartPointer<vtkGlyph3D>::New();
    this->PlotGlyph->SetSourceConnection(glyphSource->GetOutputPort());
    this->PlotGlyph->SetInputDataObject(this->PlotPointsData);
    this->PlotGlyph->SetScaleModeToDataScalingOff();
    this->PlotGlyph->Update();

    this->PlotAppend = vtkSmartPointer<vtkAppendPolyData>::New();
    this->PlotAppend->AddInputData(this->PlotLinesData);
    this->PlotAppend->AddInputData(this->PlotGlyph->GetOutput());

    this->SetNumberOfInputPorts(0);
}

vtkPlotData::~vtkPlotData()
{
    if (this->PlotLabel)
    {
        delete [] this->PlotLabel;
    }
}

int vtkPlotData::RequestData(vtkInformation *request, vtkInformationVector **inputVector,
                             vtkInformationVector *outputVector)
{
    double dataBounds[6];
    int i;

    vtkDebugMacro(<< "Updating vtkPlotData");

    if (!this->PlotPoints && !this->PlotLines)
    {
        vtkDebugMacro(<< "Nothing to plot");
        this->PlotPointsData->SetPoints(0);
        this->PlotLinesData->SetPoints(0);
        this->PlotLinesData->SetLines(0);
        this->PlotAppend->Update();
        this->GetOutput()->ShallowCopy(this->PlotAppend->GetOutput());
        return 1;
    }

    int viewportMappingNeeded = (this->ViewportBounds[0] <= this->ViewportBounds[1] ||
                                 this->ViewportBounds[2] <= this->ViewportBounds[3] ||
                                 this->ViewportBounds[4] <= this->ViewportBounds[5]);

    this->GetClipXRange(dataBounds);
    this->GetClipYRange(&(dataBounds[2]));
    this->GetClipZRange(&(dataBounds[4]));

    int dataClippingNeeded = (dataBounds[0] <= dataBounds[1] || dataBounds[2] <= dataBounds[3] ||
                              dataBounds[4] <= dataBounds[5]);

    if (viewportMappingNeeded || dataClippingNeeded)
    {
        // Make sure that 'dataBounds' corresponds with the real bounds
        // (for all dimensions that have no user-specified range)
        if (dataBounds[0] > dataBounds[1])
        {
            if (this->LogX)
            {
                this->GetDataXRangeAbove0(dataBounds);
            }
            else
            {
                this->GetDataXRange(dataBounds);
            }
        }
        if (dataBounds[2] > dataBounds[3])
        {
            if (this->LogY)
            {
                this->GetDataYRangeAbove0(&(dataBounds[2]));
            }
            else
            {
                this->GetDataYRange(&(dataBounds[2]));
            }
        }
        if (dataBounds[4] > dataBounds[5])
        {
            if (this->LogZ)
            {
                this->GetDataZRangeAbove0(&(dataBounds[4]));
            }
            else
            {
                this->GetDataZRange(&(dataBounds[4]));
            }
        }
    }

    // Check if boundaries are valid when using logarithmic axis
    if ((this->LogX && dataBounds[0] <= 0.0) || (this->LogY && dataBounds[2] <= 0.0) ||
        (this->LogZ && dataBounds[4] <= 0.0))
    {
        vtkDebugMacro(<< "Trying to plot negative values with logarithmic axis.");
        this->PlotPointsData->SetPoints(0);
        this->PlotLinesData->SetPoints(0);
        this->PlotLinesData->SetLines(0);
        this->PlotAppend->Update();
        this->GetOutput()->ShallowCopy(this->PlotAppend->GetOutput());
        return 1;
    }

    vtkDebugMacro(<< "  Using databounds: (" << dataBounds[0] << ", " << dataBounds[1] << ", " << dataBounds[2] << ", "
                  << dataBounds[3] << ", " << dataBounds[4] << ", " << dataBounds[5] << ")");

    vtkDebugMacro(<< "  Calculating Data Points");
    // The points array will intially contain all data elements.
    auto pts = vtkSmartPointer<vtkPoints>::New();
    pts->SetDataTypeToDouble();
    int numComp = this->GetNumberOfItems();
    for (i = 0; i < numComp; i++)
    {
        double xyz[3];
        xyz[0] = this->GetXValue(i);
        xyz[1] = this->GetYValue(i);
        xyz[2] = this->GetZValue(i);
        pts->InsertNextPoint(xyz);
    }

    this->ComputePlotPoints(pts, dataBounds, viewportMappingNeeded, dataClippingNeeded);
    if (dataClippingNeeded)
    {
        this->ComputePlotLinesWithClipping(pts, dataBounds, viewportMappingNeeded);
    }
    else
    {
        this->ComputePlotLines(pts, dataBounds, viewportMappingNeeded);
    }

    // Update the PlotData, PlotGlyph and PlotAppend polydata
    this->PlotAppend->Update();

    // Update the output
    this->GetOutput()->ShallowCopy(this->PlotAppend->GetOutput());

    return 1;
}

void vtkPlotData::ComputePlotPoints(vtkPoints *pts, double dataBounds[6], int viewportMappingNeeded,
                                    int dataClippingNeeded)
{
    this->PlotPointsData->SetPoints(0);
    if (this->PlotPoints)
    {
        // PlotPointsData contains only those points that are within the X, Y, and Z ranges.
        vtkDebugMacro(<< "  Calculating PlotPoints with DataClipping");
        auto newPts = vtkSmartPointer<vtkPoints>::New();
        newPts->SetDataTypeToDouble();
        int numberOfPoints = 0;
        int logXYZ[3];
        logXYZ[0] = this->LogX;
        logXYZ[1] = this->LogY;
        logXYZ[2] = this->LogZ;
        for (vtkIdType ptId = 0; ptId<pts->GetNumberOfPoints(); ptId++)
        {
            double xyz[3];
            pts->GetPoint(ptId, xyz);
            if (!isInvalid(xyz[0], logXYZ[0]) && !isInvalid(xyz[1], logXYZ[1]) &&
                (!dataClippingNeeded || (xyz[0] >= dataBounds[0] && xyz[0] <= dataBounds[1] &&
                                         xyz[1] >= dataBounds[2] && xyz[1] <= dataBounds[3] &&
                                         xyz[2] >= dataBounds[4] && xyz[2] <= dataBounds[5])))
            {
                if (viewportMappingNeeded)
                {
                    this->DataToViewport3D(xyz, this->ViewportBounds, dataBounds, logXYZ);
                }
                newPts->InsertNextPoint(xyz);
                numberOfPoints++;
            }
        }
        if (numberOfPoints>0)
        {
            this->PlotPointsData->SetPoints(newPts);
        }
        // Set scale of the Glyph with respect to the viewport bounds
        this->PlotGlyph->SetScaleFactor(ComputeGlyphScale());
        this->PlotGlyph->Update();
    }
}

void vtkPlotData::ComputePlotLines(vtkPoints *pts, double dataBounds[6], int viewportMappingNeeded)
{
    this->PlotLinesData->SetLines(0);
    if (this->PlotLines)
    {
        vtkDebugMacro(<< "Calculating PlotLines without DataClipping");
        int numberOfDataPoints = pts->GetNumberOfPoints();
        if (numberOfDataPoints>0)
        {
            int logXYZ[3];
            int numberOfLines = 0;
            int numberOfPoints = 0;  // Number of points within a line segment
            auto newPts = vtkSmartPointer<vtkPoints>::New();
            newPts->SetDataTypeToDouble();
            auto lines = vtkSmartPointer<vtkCellArray>::New();
            logXYZ[0] = this->LogX;
            logXYZ[1] = this->LogY;
            logXYZ[2] = this->LogZ;
            for (vtkIdType ptId = 0; ptId<numberOfDataPoints; ptId++)
            {
                double xyz[3];
                pts->GetPoint(ptId, xyz);
                if (!isInvalid(xyz[0], logXYZ[0]) && !isInvalid(xyz[1], logXYZ[1]))
                {
                    if (viewportMappingNeeded)
                    {
                        this->DataToViewport3D(xyz, this->ViewportBounds, dataBounds, logXYZ);
                    }
                    vtkIdType newPtId = newPts->InsertNextPoint(xyz);
                    if (numberOfPoints == 0)
                    {
                        lines->InsertNextCell(0);
                    }
                    lines->InsertCellPoint(newPtId);
                    numberOfPoints++;
                }
                else if (numberOfPoints > 0)
                {
                    // finish line segment
                    lines->UpdateCellCount(numberOfPoints);
                    numberOfLines++;
                    numberOfPoints = 0;
                }
            }
            // Finish last line segment
            if (numberOfPoints>0)
            {
                lines->UpdateCellCount(numberOfPoints);
                numberOfLines++;
            }
            if (numberOfLines>0)
            {
                this->PlotLinesData->SetPoints(newPts);
                this->PlotLinesData->SetLines(lines);
            }
        }
    }
}

void vtkPlotData::ComputePlotLinesWithClipping(vtkPoints *pts, double dataBounds[6], int viewportMappingNeeded)
{
    this->PlotLinesData->SetLines(0);
    if (this->PlotLines)
    {
        vtkDebugMacro(<< "Calculating PlotLines with DataClipping");
        // The lines array contains the line segments that results form clipping the original line with the X, Y,
        // and Z ranges. Each linesegment is contained within one cell and contains both the points from the dataset
        // and possible new intersection endpoints.
        int numberOfDataPoints = pts->GetNumberOfPoints();
        if (numberOfDataPoints > 0)
        {
            auto newPts = vtkSmartPointer<vtkPoints>::New();
            newPts->SetDataTypeToDouble();
            auto lines = vtkSmartPointer<vtkCellArray>::New();
            int numberOfLines = 0;
            int numberOfPoints = 0; // Number of points within a line segment
            int logXYZ[3];
            double xyz1[3];
            double xyz2[3];
            logXYZ[0] = this->LogX;
            logXYZ[1] = this->LogY;
            logXYZ[2] = this->LogZ;
            pts->GetPoint(0, xyz1);
            // NaN values and negative log values are considered outside the bounds
            int isnan1 = isInvalid(xyz1[0], logXYZ[0]) || isInvalid(xyz1[1], logXYZ[1]);
            int withinBounds1 = (!isnan1 && xyz1[0] >= dataBounds[0] && xyz1[0] <= dataBounds[1] &&
                                 xyz1[1] >= dataBounds[2] && xyz1[1] <= dataBounds[3] &&
                                 xyz1[2] >= dataBounds[4] && xyz1[2] <= dataBounds[5]);
            for (vtkIdType ptId = 0; ptId < numberOfDataPoints - 1; ptId++)
            {
                pts->GetPoint(ptId + 1, xyz2);
                int isnan2 = isInvalid(xyz2[0], logXYZ[0]) || isInvalid(xyz2[1], logXYZ[1]);
                int withinBounds2 = (!isnan2 && xyz2[0] >= dataBounds[0] && xyz2[0] <= dataBounds[1] &&
                                     xyz2[1] >= dataBounds[2] && xyz2[1] <= dataBounds[3] &&
                                     xyz2[2] >= dataBounds[4] && xyz2[2] <= dataBounds[5]);
                if (withinBounds1)
                {
                    double xyz3[3];
                    if (!withinBounds2 && !isnan2)
                    {
                        // calculate intersection
                        ComputeIntersection(dataBounds, xyz2, xyz1, xyz3);
                    }
                    // add xyz1 to points
                    if (viewportMappingNeeded)
                    {
                        this->DataToViewport3D(xyz1, this->ViewportBounds, dataBounds, logXYZ);
                    }
                    vtkIdType newPtId = newPts->InsertNextPoint(xyz1);
                    // add xyz1 to lines
                    if (numberOfPoints == 0)
                    {
                        lines->InsertNextCell(0);
                    }
                    lines->InsertCellPoint(newPtId);
                    numberOfPoints++;
                    // Ending line
                    if (!withinBounds2)
                    {
                        // Leaving the boundaries
                        if (!isnan2)
                        {
                            // add intersection point to points
                            if (viewportMappingNeeded)
                            {
                                this->DataToViewport3D(xyz3, this->ViewportBounds, dataBounds, logXYZ);
                            }
                            newPtId = newPts->InsertNextPoint(xyz3);
                            // add intersection point to lines
                            lines->InsertCellPoint(newPtId);
                            numberOfPoints++;
                        }
                        // finish line segment
                        lines->UpdateCellCount(numberOfPoints);
                        numberOfLines++;
                        numberOfPoints = 0;
                    }
                }
                else if (!isnan1)
                {
                    // Entering the boundaries
                    if (withinBounds2)
                    {
                        double xyz3[3];
                        // calculate intersection
                        ComputeIntersection(dataBounds, xyz1, xyz2, xyz3);
                        // add intersection point to points
                        if (viewportMappingNeeded)
                        {
                            this->DataToViewport3D(xyz3, this->ViewportBounds, dataBounds, logXYZ);
                        }
                        vtkIdType newPtId = newPts->InsertNextPoint(xyz3);
                        // add intersection point to lines starting a new line segment
                        lines->InsertNextCell(0);
                        lines->InsertCellPoint(newPtId);
                        numberOfPoints = 1;
                    }
                    else if (!isnan2)
                    {
                        // Staying outside the boundaries
                        // check if linesegment doesn't intersect with boundaries
                        double xyz3[3];
                        if (ComputeIntersection(dataBounds, xyz1, xyz2, xyz3))
                        {
                            double xyz4[3];
                            // Calculate second intersectionpoint
                            ComputeIntersection(dataBounds, xyz2, xyz1, xyz4);
                            // add first intersection point to points
                            if (viewportMappingNeeded)
                            {
                                this->DataToViewport3D(xyz3, this->ViewportBounds, dataBounds, logXYZ);
                            }
                            vtkIdType newPtId = newPts->InsertNextPoint(xyz3);
                            // add first intersection point to lines
                            lines->InsertNextCell(2);
                            lines->InsertCellPoint(newPtId);
                            // Only add the second intersection point to points if the
                            // first and second intersection point are not the same
                            // (i.e. we don't intersect one of the axes or corner points of
                            // the bounding box)
                            if (viewportMappingNeeded)
                            {
                                this->DataToViewport3D(xyz4, this->ViewportBounds, dataBounds, logXYZ);
                            }
                            if (xyz3[0] != xyz4[0] || xyz3[1] != xyz4[1] || xyz3[2] != xyz4[2])
                            {
                                newPtId = newPts->InsertNextPoint(xyz4);
                            }
                            // add second intersection point to lines
                            lines->InsertCellPoint(newPtId);
                            // go to next line
                            numberOfLines++;
                            numberOfPoints = 0;
                        }
                    }
                }
                xyz1[0] = xyz2[0];
                xyz1[1] = xyz2[1];
                xyz1[2] = xyz2[2];
                withinBounds1 = withinBounds2;
                isnan1 = isnan2;
            }
            if (withinBounds1)
            {
                // Add last point to points
                if (viewportMappingNeeded)
                {
                    this->DataToViewport3D(xyz1, this->ViewportBounds, dataBounds, logXYZ);
                }
                vtkIdType newPtId = newPts->InsertNextPoint(xyz1);
                // Add last point to lines
                if (numberOfPoints == 0)
                {
                    lines->InsertNextCell(0);
                }
                lines->InsertCellPoint(newPtId);
                numberOfPoints++;
            }
            // Finish last line segment
            if (numberOfPoints > 0)
            {
                lines->UpdateCellCount(numberOfPoints);
                numberOfLines++;
            }
            if (numberOfLines > 0)
            {
                this->PlotLinesData->SetPoints(newPts);
                this->PlotLinesData->SetLines(lines);
            }
        }
    }
}

void vtkPlotData::PrintSelf(ostream& os, vtkIndent indent)
{
    os << indent << "Number of Items: " << this->GetNumberOfItems() << endl;
    os << indent << "Log X: " << (this->LogX ? "On" : "Off") << endl;
    os << indent << "Log Y: " << (this->LogY ? "On" : "Off") << endl;
    os << indent << "Log Z: " << (this->LogZ ? "On" : "Off") << endl;
    os << indent << "Viewport Bounds: (" << this->ViewportBounds[0] << ", " <<
        this->ViewportBounds[1] << ", " << this->ViewportBounds[2] << ", " <<
        this->ViewportBounds[3] << ", " << this->ViewportBounds[4] << ", " <<
        this->ViewportBounds[5] << ")" << endl;
    os << indent << "Plot Points: " << (this->PlotPoints ? "On" : "Off") << endl;
    os << indent << "Plot Lines: " << (this->PlotLines ? "On" : "Off") << endl;
    os << indent << "Glyph Size: " << this->GlyphSize << endl;
}

void vtkPlotData::GetValidDataRange(double range[2], int dim, int log)
{
    int numComp = this->GetNumberOfItems();

    range[0] = VTK_DOUBLE_MAX;
    range[1] = log ? 0 : VTK_DOUBLE_MIN;

    for (int i = 0; i < numComp; i++)
    {
        double x;
        switch(dim)
        {
            case 0:
                x = this->GetXValue(i);
                break;
            case 1:
                x = this->GetYValue(i);
                break;
            case 2:
                x = this->GetZValue(i);
                break;
            default:
                x = 0.0;
        }
        if (!isInvalid(x, log))
        {
            if (x < range[0])
            {
                range[0] = x;
            }
            if (x > range[1])
            {
                range[1] = x;
            }
        }
    }

    if (range[0] > range[1])
    {
        range[0] = 1;
        range[1] = 0;
    }

    vtkDebugMacro(<< "GetValidDataRange (dim=" << dim << ", log=" << log << "): range = ("
                  << range[0] << "," << range[1] << ")");
}

void vtkPlotData::GetDataRange(double range[2], int dim)
{
    this->GetValidDataRange(range, dim, 0);
}

void vtkPlotData::GetDataRangeAbove0(double range[2], int dim)
{
    this->GetValidDataRange(range, dim, 1);
}

void vtkPlotData::SetPlotSymbol(vtkPolyData *input)
{
    if (input != this->PlotGlyph->GetSource())
    {
        this->PlotGlyph->SetSourceData(input);
        this->Modified();
    }
}

vtkPolyData *vtkPlotData::GetPlotSymbol()
{
    return this->PlotGlyph->GetSource();
}

double vtkPlotData::ComputeGlyphScale()
{
    this->PlotGlyph->Update();
    vtkPolyData *pd = this->PlotGlyph->GetSource();
    return this->GlyphSize * sqrt((double)(this->ViewportBounds[1] - this->ViewportBounds[0]) *
                                  (this->ViewportBounds[1] - this->ViewportBounds[0]) +
                                  (this->ViewportBounds[3] - this->ViewportBounds[2]) *
                                  (this->ViewportBounds[3] - this->ViewportBounds[2]) +
                                  (this->ViewportBounds[5] - this->ViewportBounds[4]) *
                                  (this->ViewportBounds[5] - this->ViewportBounds[4])) / pd->GetLength();
}


void vtkPlotData::DataToViewport(double &x, double viewportBounds[2], double dataBounds[2], int logX)
{
    if (viewportBounds[0] < viewportBounds[1])
    {
        if (dataBounds[0] == dataBounds[1])
        {
            x = (viewportBounds[0] + viewportBounds[1]) / 2;
        }
        else
        {
            if (logX)
            {
                // Use logarithmic mapping
                if (dataBounds[0] > 0 && dataBounds[1] > 0)
                {
                    x = viewportBounds[0] + (viewportBounds[1] - viewportBounds[0]) *
                        (log(x) - log(dataBounds[0])) / (log(dataBounds[1]) - log(dataBounds[0]));
                }
            }
            else
            {
                // Use linear mapping
                x = viewportBounds[0] + (viewportBounds[1] - viewportBounds[0]) * (x - dataBounds[0]) /
                    (dataBounds[1] - dataBounds[0]);
            }
        }
    }
}

void vtkPlotData::ViewportToData(double &x, double viewportBounds[2], double dataBounds[2], int logX)
{
    if (viewportBounds[0] == viewportBounds[1] || dataBounds[0] == dataBounds[1])
    {
        x = dataBounds[0];
    }
    else if (viewportBounds[0] < viewportBounds[1])
    {
        if (logX)
        {
            // Use logarithmic mapping
            if (dataBounds[0] > 0 && dataBounds[1] > 0)
            {
                x = exp(log(dataBounds[0]) + (log(dataBounds[1]) - log(dataBounds[0])) *
                        (x - viewportBounds[0]) / (viewportBounds[1] - viewportBounds[0]));
            }
        }
        else
        {
            // Use linear mapping
            x = dataBounds[0] + (dataBounds[1] - dataBounds[0]) * (x - viewportBounds[0]) /
                (viewportBounds[1] - viewportBounds[0]);
        }
    }
}
