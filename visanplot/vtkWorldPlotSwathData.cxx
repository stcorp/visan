//
// Copyright (C) 2002-2022 S[&]T, The Netherlands.
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

#include <assert.h>
#include <string.h>

#include "vtkWorldPlotSwathData.h"

#include "vtkCellArray.h"
#include "vtkCellData.h"
#include "vtkColorTable.h"
#include "vtkDoubleArray.h"
#include "vtkPoints.h"
#include "vtkPolyData.h"
#include "vtkPolyDataCollection.h"

vtkStandardNewMacro(vtkWorldPlotSwathData);

static int isBackscan(const double longitude[4], const double latitude[4])
{
    const double pi = 3.14159265358979;
    double px, py, qx, qy, rx, ry;

    px = longitude[0] * pi / 180.0;
    py = latitude[0] * pi / 180.0;
    qx = longitude[3] * pi / 180.0;
    qy = latitude[3] * pi / 180.0;
    rx = longitude[1] * pi / 180.0;
    ry = latitude[1] * pi / 180.0;

    return (cos(qy) * (cos(ry) * sin(py) * sin(qx - rx) + cos(py) * sin(px - qx) * sin(ry)) -
            cos(py) * cos(ry) * sin(qy) * sin(px - rx) < 0.0);
}


vtkWorldPlotSwathData::vtkWorldPlotSwathData()
{
    this->colorTable->SetColorTableByName("Aerosol");
}

// cornerLatitude[numSwaths,4], cornerLongitude[numSwaths,4], data[numSwaths] (optional)
void vtkWorldPlotSwathData::AddData(vtkDoubleArray *cornerLatitude, vtkDoubleArray *cornerLongitude,
                                    vtkDoubleArray *data)
{
    auto points = vtkSmartPointer<vtkPoints>::New();
    auto swaths = vtkSmartPointer<vtkPolyData>::New();
    auto polys = vtkSmartPointer<vtkCellArray>::New();
    int numSwaths;
    int numValues;
    int i;

    if (cornerLatitude->GetNumberOfComponents() != 4 || cornerLongitude->GetNumberOfComponents() != 4)
    {
        vtkErrorMacro("Number of components should be 4 for corner latitude/longitude arrays");
        return;
    }
    if (cornerLatitude->GetNumberOfTuples() != cornerLongitude->GetNumberOfTuples())
    {
        vtkErrorMacro("Number of tuples should be equal for corner latitudes and longitudes");
        return;
    }
    numValues = data == nullptr ? 0 : data->GetNumberOfTuples();
    if (numValues > 0)
    {
        if (data->GetNumberOfTuples() != cornerLatitude->GetNumberOfTuples())
        {
            vtkErrorMacro("Number of tuples should be equal for data and corner latitudes/longitudes");
            return;
        }
        if (data->GetNumberOfComponents() != 1)
        {
            vtkErrorMacro("Number of components should be 1 for data array");
            return;
        }
    }

    numSwaths = cornerLatitude->GetNumberOfTuples();
    points->SetDataTypeToDouble();
    points->SetNumberOfPoints(4 * numSwaths);
    for (i = 0; i < numSwaths; i++)
    {
        double latitude[4];
        double longitude[4];

        cornerLatitude->GetTuple(i, latitude);
        cornerLongitude->GetTuple(i, longitude);

        points->SetPoint(i * 4 + 0, longitude[0], latitude[0], 0);
        points->SetPoint(i * 4 + 1, longitude[1], latitude[1], 0);
        points->SetPoint(i * 4 + 2, longitude[2], latitude[2], 0);
        points->SetPoint(i * 4 + 3, longitude[3], latitude[3], 0);

        polys->InsertNextCell(4);
        if (isBackscan(longitude, latitude))
        {
            polys->InsertCellPoint(i * 4 + 3);
            polys->InsertCellPoint(i * 4 + 2);
            polys->InsertCellPoint(i * 4 + 1);
            polys->InsertCellPoint(i * 4 + 0);
        }
        else
        {
            polys->InsertCellPoint(i * 4 + 0);
            polys->InsertCellPoint(i * 4 + 1);
            polys->InsertCellPoint(i * 4 + 2);
            polys->InsertCellPoint(i * 4 + 3);
        }
    }
    swaths->SetPoints(points);
    swaths->SetPolys(polys);

    if (numValues > 0)
    {
        auto value = vtkSmartPointer<vtkDoubleArray>::New();
        value->DeepCopy(data);
        swaths->GetCellData()->SetScalars(value);
    }

    this->AddInputData(swaths);

    if (numValues > 0 && this->algorithms->GetNumberOfItems() == 1)
    {
        this->colorTable->SetColorRange(data->GetFiniteRange());
    }
}
