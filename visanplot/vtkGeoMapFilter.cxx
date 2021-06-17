//
// Copyright (C) 2002-2021 S[&]T, The Netherlands.
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

#include "vtkGeoMapFilter.h"

#include "vtkCellArray.h"
#include "vtkCellData.h"
#include "vtkDoubleArray.h"
#include "vtkFloatArray.h"
#include "vtkMath.h"
#include "vtkObjectFactory.h"
#include "vtkPoints.h"
#include "vtkPolyData.h"
#include "vtkShortArray.h"
#include "vtkUnsignedCharArray.h"

#include "math.h"

#define EPSILON 1e-3

vtkStandardNewMacro(vtkGeoMapFilter);

vtkGeoMapFilter::vtkGeoMapFilter()
{
    this->Values = vtkSmartPointer<vtkDoubleArray>::New();
    this->Heights = vtkSmartPointer<vtkDoubleArray>::New();
    this->Latitudes = vtkSmartPointer<vtkDoubleArray>::New();
    this->Longitudes = vtkSmartPointer<vtkDoubleArray>::New();
    this->Valid = vtkSmartPointer<vtkUnsignedCharArray>::New();
    this->MinMappedValue = 0.0;
    this->MaxMappedValue = 1.0;
    this->Factor = 0.0;
    this->Radius = 1.0;
    this->MapWidth = 0;
    this->MapHeight = 0;
    this->SetNumberOfInputPorts(0);
}

void vtkGeoMapFilter::SetValues(vtkDoubleArray *values)
{
    double *value;
    unsigned char *valid;
    int numPoints;
    int i;

    this->Values = values;

    numPoints = values->GetNumberOfTuples();
    this->Valid->SetNumberOfTuples(numPoints);
    value = this->Values->GetPointer(0);
    valid = this->Valid->GetPointer(0);
    for (i = 0; i < numPoints; i++)
    {
        valid[i] = vtkMath::IsFinite(value[i]);
    }

    this->Modified();
}

vtkDoubleArray *vtkGeoMapFilter::GetValues()
{
    return this->Values.GetPointer();
}

void vtkGeoMapFilter::SetHeights(vtkDoubleArray *heights)
{
    this->Heights = heights;
    this->Modified();
}

vtkDoubleArray *vtkGeoMapFilter::GetHeights()
{
    return this->Heights.GetPointer();
}

void vtkGeoMapFilter::SetLongitudes(vtkDoubleArray *longitudes)
{
    this->Longitudes = longitudes;
    this->Modified();
}

vtkDoubleArray *vtkGeoMapFilter::GetLongitudes()
{
    return this->Longitudes.GetPointer();
}

void vtkGeoMapFilter::SetLatitudes(vtkDoubleArray *latitudes)
{
    this->Latitudes = latitudes;
    this->Modified();
}

vtkDoubleArray *vtkGeoMapFilter::GetLatitudes()
{
    return this->Latitudes.GetPointer();
}

int vtkGeoMapFilter::RequestData(vtkInformation *request, vtkInformationVector **inputVector,
                                 vtkInformationVector *outputVector)
{
    vtkPolyData *output;
    vtkIdType *pointIds;
    vtkIdType ptId;
    double *values = nullptr;
    unsigned char *bits = nullptr;
    double *heights = nullptr;
    double *latitudes = nullptr;
    double *longitudes = nullptr;
    double interpolatedHeight;
    double offsetLatitude;
    double offsetLongitude;

    int numValidPoints;
    int lat;
    int lon;
    int val_id;
    int useHeights;
    int rotation;

    useHeights = (this->Heights != nullptr && this->Factor > 0 && this->MaxMappedValue > this->MinMappedValue);

    if (this->MapHeight <= 1)
    {
        vtkErrorMacro(<< "MapHeight should be > 1");
        return 0;
    }
    if (this->MapWidth <= 1)
    {
        vtkErrorMacro(<< "MapWidth should be > 1");
        return 0;
    }
    if (this->Values->GetNumberOfTuples() != this->MapHeight * this->MapWidth)
    {
        vtkErrorMacro(<< "Input 'Values' contains invalid number of elements");
        return 0;
    }
    if (this->Valid->GetNumberOfTuples() != this->MapHeight * this->MapWidth)
    {
        vtkErrorMacro(<< "Input 'Valid' contains invalid number of elements");
        return 0;
    }
    if (useHeights && this->Heights->GetNumberOfTuples() != this->MapHeight * this->MapWidth)
    {
        vtkErrorMacro(<< "Input 'Heights' contains invalid number of elements");
        return 0;
    }
    if (this->Latitudes->GetNumberOfTuples() != this->MapHeight)
    {
        vtkErrorMacro(<< "Input 'Latitudes' contains invalid number of elements");
        return 0;
    }
    if (this->Longitudes->GetNumberOfTuples() != this->MapWidth)
    {
        vtkErrorMacro(<< "Input 'Longitudes' contains invalid number of elements");
        return 0;
    }
    values = this->Values->GetPointer(0);
    bits = this->Valid->GetPointer(0);
    if (useHeights)
    {
        heights = this->Heights->GetPointer(0);
    }
    latitudes = this->Latitudes->GetPointer(0);
    longitudes = this->Longitudes->GetPointer(0);
    if (values == nullptr || bits == nullptr || (useHeights && heights == nullptr) || latitudes == nullptr ||
        longitudes == nullptr)
    {
        vtkErrorMacro(<< "One or more data array pointers are empty");
        return 0;
    }
    output = (vtkPolyData *)this->GetOutput();
    auto points = vtkSmartPointer<vtkPoints>::New();
    auto polys = vtkSmartPointer<vtkCellArray>::New();
    auto colors = vtkSmartPointer<vtkFloatArray>::New();
    points->SetDataTypeToDouble();
    output->SetPoints(points);
    output->SetPolys(polys);
    output->GetCellData()->SetScalars(colors);

    pointIds = new vtkIdType[(this->MapHeight + 1) * (this->MapWidth + 1)];

    offsetLatitude = (latitudes[1] - latitudes[0]) / 2;
    offsetLongitude = (longitudes[1] - longitudes[0]) / 2;

    // should we create clock-wise or counter-clock-wise polygons
    rotation = (latitudes[0] < latitudes[1]) ^ (longitudes[0] < longitudes[1]);

    // Determine corner points for each grid cell
    for (lat = 0; lat < this->MapHeight + 1; lat++)
    {
        for (lon = 0; lon < this->MapWidth + 1; lon++)
        {
            val_id = lat * this->MapWidth + lon;
            numValidPoints = 0;
            interpolatedHeight = 0;
            if (lat > 0)
            {
                if (lon > 0 && bits[val_id - 1 - this->MapWidth])
                {
                    numValidPoints++;
                    if (useHeights)
                    {
                        interpolatedHeight += heights[val_id - 1 - this->MapWidth];
                    }
                }
                if (lon < this->MapWidth && bits[val_id - this->MapWidth])
                {
                    numValidPoints++;
                    if (useHeights)
                    {
                        interpolatedHeight += heights[val_id - this->MapWidth];
                    }
                }
            }
            if (lat < this->MapHeight)
            {
                if (lon > 0 && bits[val_id - 1])
                {
                    numValidPoints++;
                    if (useHeights)
                    {
                        interpolatedHeight += heights[val_id - 1];
                    }
                }
                if (lon < this->MapWidth && bits[val_id])
                {
                    numValidPoints++;
                    if (useHeights)
                    {
                        interpolatedHeight += heights[val_id];
                    }
                }
            }
            ptId = -1;
            if (numValidPoints > 0)
            {
                double longitude, latitude;
                if (useHeights)
                {
                    interpolatedHeight /= numValidPoints;
                    interpolatedHeight = this->Radius + this->Factor *
                        (vtkMath::Min(vtkMath::Max(interpolatedHeight, this->MinMappedValue),
                                      this->MaxMappedValue) - this->MinMappedValue) /
                        (this->MaxMappedValue - this->MinMappedValue);
                }
                else
                {
                    interpolatedHeight = this->Radius;
                }
                if (lon == this->MapWidth)
                {
                    longitude = longitudes[lon - 1] + offsetLongitude;
                }
                else
                {
                    longitude = longitudes[lon] - offsetLongitude;
                }
                if (lat == this->MapHeight)
                {
                    latitude = latitudes[lat - 1] + offsetLatitude;
                }
                else
                {
                    latitude = latitudes[lat] - offsetLatitude;
                }
                if (latitude < -90)
                {
                    latitude = -90;
                }
                if (latitude > 90)
                {
                    latitude = 90;
                }
                ptId = points->InsertNextPoint(longitude, latitude, interpolatedHeight);
            }
            pointIds[lat * (this->MapWidth + 1) + lon] = ptId;
        }
    }

    // Make sure that values for the poles are the same
    if (fabs(latitudes[0] - offsetLatitude) > 90 - EPSILON)
    {
        double average_height = 0;
        int numPts = 0;
        for (val_id = 0; val_id < this->MapWidth + 1; val_id++)
        {
            if (pointIds[val_id] != -1)
            {
                average_height += points->GetPoint(pointIds[val_id])[2];
                numPts++;
            }
        }
        if (numPts > 0)
        {
            for (val_id = 0; val_id < this->MapWidth + 1; val_id++)
            {
                if (pointIds[val_id] != -1)
                {
                    double *pt = points->GetPoint(pointIds[val_id]);
                    pt[2] = average_height / numPts;
                    points->SetPoint(pointIds[val_id], pt);
                }
            }
        }
    }
    if (fabs(latitudes[this->MapHeight - 1] + offsetLatitude) > 90 - EPSILON)
    {
        double average_height = 0;
        int numPts = 0;
        for (val_id = this->MapHeight * (this->MapWidth + 1); val_id < (this->MapHeight + 1) * (this->MapWidth + 1); val_id++)
        {
            if (pointIds[val_id] != -1)
            {
                average_height += points->GetPoint(pointIds[val_id])[2];
                numPts++;
            }
        }
        if (numPts > 0)
        {
            for (val_id = this->MapHeight * (this->MapWidth + 1); val_id < (this->MapHeight + 1) * (this->MapWidth + 1); val_id++)
            {
                if (pointIds[val_id] != -1)
                {
                    double *pt = points->GetPoint(pointIds[val_id]);
                    pt[2] = average_height / numPts;
                    points->SetPoint(pointIds[val_id], pt);
                }
            }
        }
    }

    // Make sure that values for the longitude wrap-around are the same
    if (fabs(fabs(longitudes[0] - longitudes[this->MapWidth - 1]) + 2 * offsetLongitude - 360) < EPSILON)
    {
        for (val_id = 0; val_id < (this->MapHeight + 1) * (this->MapWidth + 1); val_id += this->MapWidth + 1)
        {
            if (pointIds[val_id] != -1 && pointIds[val_id + this->MapWidth] != -1)
            {
                double *pt1 = points->GetPoint(pointIds[val_id]);
                double *pt2 = points->GetPoint(pointIds[val_id + this->MapWidth]);
                pt1[2] = (pt1[2] + pt2[2]) / 2;
                pt2[2] = pt1[2];
                points->SetPoint(pointIds[val_id], pt1);
                points->SetPoint(pointIds[val_id + this->MapWidth], pt2);
            }
        }
    }

    // Create Polys
    val_id = 0;
    for (lat = 0; lat < this->MapHeight; lat++)
    {
        for (lon = 0; lon < this->MapWidth; lon++)
        {
            int firstPt = lat * (this->MapWidth + 1) + lon;
            numValidPoints = (pointIds[firstPt] != -1) + (pointIds[firstPt + 1] != -1) +
                (pointIds[firstPt + this->MapWidth + 1] != -1) + (pointIds[firstPt + 1 + this->MapWidth + 1] != -1);
            if (numValidPoints >= 3 && bits[val_id])
            {
                vtkIdType polyId = polys->InsertNextCell(numValidPoints);
                colors->InsertTuple1(polyId, values[val_id]);
                if (pointIds[firstPt] != -1)
                {
                    polys->InsertCellPoint(pointIds[firstPt]);
                }
                if (rotation)
                {
                    if (pointIds[firstPt + this->MapWidth + 1] != -1)
                    {
                        polys->InsertCellPoint(pointIds[firstPt + this->MapWidth + 1]);
                    }
                }
                else
                {
                    if (pointIds[firstPt + 1] != -1)
                    {
                        polys->InsertCellPoint(pointIds[firstPt + 1]);
                    }
                }
                if (pointIds[firstPt + 1 + this->MapWidth + 1] != -1)
                {
                    polys->InsertCellPoint(pointIds[firstPt + 1 + this->MapWidth + 1]);
                }
                if (rotation)
                {
                    if (pointIds[firstPt + 1] != -1)
                    {
                        polys->InsertCellPoint(pointIds[firstPt + 1]);
                    }
                }
                else
                {
                    if (pointIds[firstPt + this->MapWidth + 1] != -1)
                    {
                        polys->InsertCellPoint(pointIds[firstPt + this->MapWidth + 1]);
                    }
                }
            }
            val_id++;
        }
    }
    delete [] pointIds;

    return 1;
}

void vtkGeoMapFilter::PrintSelf(ostream& os, vtkIndent indent)
{
    this->Superclass::PrintSelf(os, indent);

    os << indent << "MinMappedValue : " << this->MinMappedValue << endl;
    os << indent << "MaxMappedValue : " << this->MaxMappedValue << endl;
    os << indent << "Factor : " << this->Factor << endl;
    os << indent << "Radius : " << this->Radius << endl;
    os << indent << "MapWidth : " << this->MapWidth << endl;
    os << indent << "MapHeight : " << this->MapHeight << endl;
}
